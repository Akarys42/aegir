import logging
from pathlib import Path
from typing import Any

import yaml

_log = logging.getLogger(__name__)
_CONFIG: dict = {}
_SUFFIX_NODES = {
    "category": ("guild", "categories"),
    "channel": ("guild", "text_channels"),
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


class ConfigMeta(type):

    def __getattribute__(cls, name):
        if name.startswith("_"):
            # Normal behaviour for private attributes.
            return super().__getattribute__(name)

        # Split to get the suffix, which may determine where to find the config value.
        split_name = name.rsplit("_", 1)

        try:
            if len(split_name) > 1 and (node_path := _SUFFIX_NODES.get(split_name[1])):
                return _get_node(*node_path, split_name[0])
            else:
                # All other attributes are considered to be specific to the module.
                category = _CONFIG[cls.__module__] or {}
                return category[name]
        except KeyError:
            return super().__getattribute__(name)


class GlobalConfigMeta(type):

    def __new__(mcs, name, bases, namespace, **kwargs):
        namespace["__parents__"] = kwargs.pop("parents", ())
        return super().__new__(mcs, name, bases, namespace)

    def __getattribute__(cls, name):
        if name.startswith("_"):
            # Normal behaviour for private attributes.
            return super().__getattribute__(name)

        try:
            # Class name is the final qualifier before the attribute name itself.
            return _get_node(*cls.__parents__, cls.__name__.lower(), name)
        except KeyError:
            return super().__getattribute__(name)


def _get_node(*path: str) -> Any:
    """
    Return the node in the config under the given fully qualified `path`.

    `path` should be node names in the order parent -> child (excluding the root config node).

    Raise KeyError if the node cannot be found.
    """
    node = _CONFIG
    for name in path:
        # Avoid a TypeError in case the node had an empty value and thus was None.
        node = (node or {})[name]
    return node
