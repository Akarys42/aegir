import logging
import re
from pathlib import Path
from typing import Any

import yaml

_log = logging.getLogger(__name__)
_CONFIG: dict = {}
_CONFIG_DEFAULT: dict = {}
_SUFFIX_NODES = {
    "category": ("guild", "categories"),
    "channel": ("guild", "text_channels"),
    "emoji": ("style", "emojis"),
    "role": ("guild", "roles"),
    "voice": ("guild", "voice_channels"),
    "webhook": ("guild", "webhooks"),
}


def read_config(path: str = "config.yml") -> None:
    """
    Read the YAML config file at `path` and store the contents internally.

    Raise FileNotFoundError if the file does not exist.
    """
    global _CONFIG
    path = Path(path)

    if path.is_file():
        with path.open(encoding="utf-8") as f:
            _CONFIG = yaml.safe_load(f)

    raise FileNotFoundError(f"No config found at path {path!r}")


class _ConfigMetaBase(type):

    def __getattribute__(cls, name):
        if name.startswith("_"):
            # Normal behaviour for private attributes.
            return super().__getattribute__(name)

        try:
            value = cls.__get_node__(name)
            if hasattr(value, "__get__"):
                return value.__get__(None, cls)
            else:
                return value
        except KeyError:
            return super().__getattribute__(name)


class ConfigMeta(_ConfigMetaBase):

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue

            split_name = name.rsplit("_", 1)
            if len(split_name) > 1 and (node_path := _SUFFIX_NODES.get(split_name[1])):
                node = _get_node(_CONFIG_DEFAULT, *node_path, setdefault=True)
                node[split_name[0]] = value
            else:
                _CONFIG_DEFAULT.setdefault(cls.__module__, {})[name] = value

        return cls

    def __get_node__(cls, name):
        # Split to get the suffix, which may determine where to find the config value.
        split_name = name.rsplit("_", 1)

        if len(split_name) > 1 and (node_path := _SUFFIX_NODES.get(split_name[1])):
            return _get_node(_CONFIG, *node_path, split_name[0])
        else:
            # All other attributes are considered to be specific to the module.
            return _get_node(_CONFIG, cls.__module__, name)


class GlobalConfigMeta(_ConfigMetaBase):

    # By nickl- from https://stackoverflow.com/a/12867228/
    # Only guaranteed to work with ASCII names.
    _CAMEL_TO_SNAKE_RE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

    def __new__(mcs, name, bases, namespace, **kwargs):
        namespace["__parents__"] = kwargs.pop("parents", ())
        namespace["__node_name__"] = mcs._CAMEL_TO_SNAKE_RE.sub(r"_\1", name).lower()
        cls = super().__new__(mcs, name, bases, namespace)

        for name, value in vars(cls).items():
            if name.startswith("_"):
                continue

            node = _get_node(_CONFIG_DEFAULT, *cls.__parents__, cls.__node_name__, setdefault=True)
            node[name] = value

        return cls

    def __get_node__(cls, name):
        return _get_node(_CONFIG, *cls.__parents__, cls.__node_name__, name)


class _Reference:

    def __init__(self, node_path: str):
        self.node_path = node_path
        self.node_names = node_path.split("/")

    def __get__(self, *args):
        try:
            return _get_node(_CONFIG, *self.node_names)
        except KeyError:
            try:
                return _get_node(_CONFIG_DEFAULT, *self.node_names)
            except KeyError:
                raise AttributeError(f"Cannot resolve node reference {self.node_path!r}")

    def __set__(self, instance, value) -> None:
        node = _get_node(_CONFIG, *self.node_names[:-1], setdefault=True)
        node[self.node_names[-1]] = value

    def __repr__(self):
        return f"<{self.__class__.__name__} descriptor with node_path={self.node_path!r}>"


def _get_node(root: dict, *path: str, setdefault: bool = False) -> Any:
    """
    Return the node in `root` under the given fully qualified `path`.

    `path` should be node names in the order parent -> child (excluding the root config node).

    If `setdefault` is True, create new nested dictionaries for missing nodes.
    Otherwise, raise KeyError if the node on the path cannot be found.
    """
    node = root
    for name in path:
        if setdefault:
            node = node.setdefault(name, {})
        else:
            # Avoid a TypeError in case the node had an empty value and thus was None.
            node = (node or {})[name]
    return node


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> _Reference:
    return _Reference(node.value)


yaml.SafeLoader.add_constructor("!REF", _ref_constructor)
