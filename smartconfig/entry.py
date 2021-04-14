from itertools import chain
from typing import Any, Dict, MutableMapping, NoReturn, Optional, Tuple

from smartconfig import _registry
from smartconfig._registry import get_attribute, unload_defaults, used_paths
from smartconfig.exceptions import ConfigurationError, ConfigurationKeyError, InvalidOperation, PathConflict


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviour.

    See the documentation of `ConfigEntry`.

    Note: Using this metaclass outside of the library is currently not supported.
    """

    def __getattribute__(cls, name: str) -> Optional[Any]:
        """
        Look up the attribute through the configuration system.

        If the attribute's name starts with `_`, use the default Python behaviour for attribute lookup.
        Otherwise, retrieve the value from the loaded configurations or the default value.

        Args:
            name: Name of the attribute to retrieve.

        Raises:
            ConfigurationError: A node along the path is not a mapping node.
            ConfigurationKeyError: The attribute doesn't exist.
        """
        if name.startswith('_'):
            return super().__getattribute__(name)

        return get_attribute(cls.__path, name)

    def __new__(mcs, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None) -> type:
        """Create and return new instance (a class) of this type."""
        return super().__new__(mcs, name, bases, dict_)

    def _register_entry(cls) -> None:
        """Register the entry's path and store its default values in the global configuration."""
        current_node = _registry.global_configuration

        for node_name in cls.__path.split("."):
            current_node = current_node.setdefault(node_name, {})

            if not isinstance(current_node, MutableMapping):
                raise ConfigurationError(f"Node at path {cls.__path!r} isn't a mapping.")

        for key, value in cls.__dict__.items():
            # Ignore "private" attributes and only write values that aren't already defined.
            if not key.startswith('_') and key not in current_node:
                current_node[key] = value

        used_paths.add(cls.__path)

    def _check_undefined_entries(cls) -> None:
        """Raise `ConfigurationKeyError` if any attribute doesn't have a defined value."""
        for attribute in chain(cls.__dict__.keys(), getattr(cls, "__annotations__", ())):
            if not attribute.startswith('_'):
                try:
                    get_attribute(cls.__path, attribute)
                except (ConfigurationError, ConfigurationKeyError):
                    raise ConfigurationKeyError(f"Attribute {attribute!r} doesn't have a defined value.") from None

    def __init__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None):
        """Initialise the new entry."""
        super().__init__(name, bases, dict_)

        cls.__path = path or cls.__module__
        if cls.__path in _registry.used_paths:
            raise PathConflict(f"An entry at {cls.__path!r} already exists.")

        cls._register_entry()
        cls._check_undefined_entries()

    def __del__(cls) -> None:
        """Remove the default values from the global configuration and free the entry's path."""
        unload_defaults(cls.__path)
        used_paths.remove(cls.__path)

    def __repr__(cls) -> str:
        """Return a short representation of the entry."""
        if hasattr(cls, '__path'):
            return f"<_ConfigEntryMeta {cls.__name__} at {cls.__path!r}>"
        else:
            return f"<_ConfigEntryMeta {cls.__name__}>"

    def __eq__(cls, other: Any) -> bool:
        """Return True if this entry and the other point to the same path."""
        if not isinstance(other, _ConfigEntryMeta):
            return NotImplemented
        return cls.__path == other.__path


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for configuration entries.

    Values of class attributes can be overwritten by loading YAML configuration files. Otherwise, their given default
    values will be used. The exception is class attributes whose names begin with an underscore; they always behave like
    normal class attributes and therefore their values cannot be overwritten by config files.

    Supports equality comparison based on the value of `path`.

    Metaclass Args:
        path: Path to use for attribute lookup in the config.
            Default to the containing module's fully-qualified name when the value is None or an empty string.

    Raises:
        PathConflict: An entry is already registered at `path`.
        ConfigurationError: A node along `path` is not a mapping node.
        ConfigurationKeyError: A class attribute doesn't have a defined value.
        InvalidOperation: This class or a subclass of it is instantiated.
    """

    def __init__(self) -> NoReturn:
        """Raise `InvalidOperation` because creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
