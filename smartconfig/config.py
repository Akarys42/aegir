import logging
import re
from pathlib import Path
from typing import Any, Tuple

import yaml

__all__ = ["ConfigMeta", "GlobalConfigMeta", "read_config"]

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
    else:
        raise FileNotFoundError(f"No config found at path {path!r}")


class _ConfigMetaBase(type):
    """
    Base for config metaclasses which maps default values and retrieves configured values.

    Subclasses need to implement a `_get_node_path` function which translates an attribute name to
    a tuple of a parent YAML node path and a final node name.
    """

    def __new__(mcs, name, bases, namespace):
        cls = super().__new__(mcs, name, bases, namespace)

        # Map all public attributes to the _CONFIG_DEFAULT dictionary.
        # The _Reference descriptor relies on this dictionary to function.
        for name, value in vars(cls).items():
            # Skip private names.
            if not name.startswith("_"):
                node_path, final_node = cls._get_node_path(name)
                parent_node = _get_node(_CONFIG_DEFAULT, *node_path, setdefault=True)
                parent_node[final_node] = value

        return cls

    def __getattribute__(cls, name: str) -> Any:
        """
        Return the value for the attribute `name` from the loaded config file.

        Attributes prefixed with "_" use the default `__getattribute__`. The default is also used
        if the attribute is not found in the loaded config.
        """
        if name.startswith("_"):
            # Normal behaviour for private attributes.
            return super().__getattribute__(name)

        try:
            node_path, final_node = cls._get_node_path(name)
            value = _get_node(_CONFIG, *node_path, final_node)

            # Use __get__ if the value is a descriptor (like _Reference).
            if hasattr(value, "__get__"):
                return value.__get__(None, cls)
            else:
                return value
        except KeyError:
            # Rely on default behaviour to return the default value (or raise an error).
            return super().__getattribute__(name)


class ConfigMeta(_ConfigMetaBase):
    """
    A metaclass which registers a class as a module-specific configuration.

    All public attributes of the class are mapped to YAML along with their default values.
    Attributes without default values (i.e. only annotated) are completely ignored. The YAML mapping
    exists internally; it is not written to any file. This facilitates the overriding of default
    values through the YAML file loaded by `read_config`.
    """

    def _get_node_path(cls, name: str) -> Tuple[Tuple[str, ...], str]:
        """
        Convert an attribute `name` to a parent YAML node path and a final node name.

        Try to use `_SUFFIX_NODES` to create the path. Otherwise, use the module's name as the path.
        """
        # Split to get the suffix, which may determine where to find the config value.
        split_name = name.rsplit("_", 1)

        if len(split_name) > 1 and (node_path := _SUFFIX_NODES.get(split_name[1])):
            return node_path, split_name[0]
        else:
            # All other attributes are considered to be specific to the module.
            return (cls.__module__,), name


class GlobalConfigMeta(_ConfigMetaBase):
    """
    A metaclass which registers a class as a global configuration.

    All public attributes of the class are mapped to YAML along with their default values.
    Attributes without default values (i.e. only annotated) are completely ignored. The YAML mapping
    exists internally; it is not written to any file. This facilitates the overriding of default
    values through the YAML file loaded by `read_config`.

    The attributes are mapped under a node named after the class. The class name is converted to
    snake case when mapped to YAML.

    By default, the class node is placed under the root YAML node. However, this can be customised
    through the optional `parents` parameter. It expects an iterable of parent node names ordered
    from parent -> child.

    Example:

    class MyClass(metaclass=GlobalConfigMeta, parents=("parent_one", "parent_two")):
        attribute_1: int = 123
        attribute_2: str = "hello"
        _private: str = "secret!"

    becomes the following YAML

    parent_one:
        parent_two:
            my_class:
                attribute_1: 123
                attribute_2: 'hello'
    """

    # By nickl- from https://stackoverflow.com/a/12867228/
    # Only guaranteed to work with ASCII names.
    _CAMEL_TO_SNAKE_RE = re.compile("((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))")

    def __new__(mcs, name, bases, namespace, **kwargs):
        namespace["__parents__"] = kwargs.pop("parents", ())
        namespace["__node_name__"] = mcs._CAMEL_TO_SNAKE_RE.sub(r"_\1", name).lower()
        return super().__new__(mcs, name, bases, namespace)

    def _get_node_path(cls, name: str) -> Tuple[Tuple[str, ...], str]:
        """
        Convert an attribute `name` to a parent YAML node path and a final node name.

        The node path consists of any given parent nodes and the class name. The final node name is
        the same as the attribute `name`.
        """
        return (*cls.__parents__, cls.__node_name__), name


class _Reference:
    """
    A descriptor which references another node in the YAML config.

    The given node path should be node names in the order parent -> child and delimited by a '/'.
    """

    def __init__(self, node_path: str):
        self.node_path = node_path
        self.node_names = node_path.split("/")

    def __get__(self, *args) -> Any:
        """
        Return the value of the referenced node.

        Attempt to get the node from the user's config. If not found, then try the default config.
        Raise an AttributeError if not found.
        """
        try:
            return _get_node(_CONFIG, *self.node_names)
        except KeyError:
            try:
                return _get_node(_CONFIG_DEFAULT, *self.node_names)
            except KeyError:
                raise AttributeError(f"Cannot resolve node reference {self.node_path!r}")

    def __set__(self, instance, value) -> None:
        """Set the value of the referenced node."""
        parent_node = _get_node(_CONFIG, *self.node_names[:-1], setdefault=True)
        parent_node[self.node_names[-1]] = value

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
    """
    Return a descriptor which references another node.

    `node` is the node whose value is used as a path to another node to reference.
    """
    return _Reference(node.value)


yaml.SafeLoader.add_constructor("!REF", _ref_constructor)
