from itertools import chain
from typing import Any, Dict, NoReturn, Optional, Tuple

from smartconfig import _registry
from smartconfig.exceptions import ConfigurationKeyError, InvalidOperation, PathConflict


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviors.

    Note: Using this metaclass outside of the library is currently not supported.

    The lookup of attributes can be customized by subclassing this metaclass and changing `_get_attribute_path`.
    """

    def __getattribute__(cls, name: str) -> Optional[Any]:
        """
        Lookup the attribute through the configuration system.

        If the attribute name starts with `_`, normal lookup is done, otherwise registry.global_configuration is used.

        Args:
            name: Attribute to lookup

        Raises:
            ConfigurationKeyError: The item doesn't exist.
        """
        # Use the normal lookup for attribute starting with `_`
        if name.startswith('_'):
            return super().__getattribute__(name)

        path, attribute = cls._get_attribute_path(name)

        if path not in _registry.global_configuration or attribute not in _registry.global_configuration[path]:
            # We try to look it up from the class
            try:
                return super().__getattribute__(name)
            except AttributeError:
                raise ConfigurationKeyError(
                    f"Entry {cls.__name__!r} at {path!r} has no attribute {attribute!r}."
                ) from None

        return _registry.global_configuration[path][attribute]

    def __new__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None) -> type:
        """
        Add the `__defined_attributes` and `__path_override` attributes to the new entry.

        Args:
            path: Custom path used for this entry instead of the module name.
        """
        names = chain(dict_.keys(), dict_.get('__annotations__', {}).keys())
        dict_[f"{cls.__name__}__defined_attributes"] = {name for name in names if not name.startswith('_')}

        dict_[f"{cls.__name__}__path_override"] = path

        return super().__new__(cls, name, bases, dict_)

    def _register_entry(cls) -> None:
        """Set the `__path` attribute and register the entry."""
        cls.__path = cls.__path_override or cls.__module__
        if cls.__path in _registry.configuration_for_module:
            raise PathConflict(f"An entry at {cls.__path!r} already exists.")  # TODO: Add an FAQ link.

        _registry.configuration_for_module[cls.__path] = cls

    def _check_undefined_entries(cls) -> None:
        """Raise `ConfigurationKeyError` if any attribute doesn't have a defined value."""
        for attribute in cls.__defined_attributes:
            try:
                if hasattr(cls, attribute):
                    continue
            except ConfigurationKeyError:
                if attribute not in _registry.global_configuration[cls.__path]:
                    raise ConfigurationKeyError(f"Attribute {attribute!r} isn't defined.") from None

    def _get_attribute_path(cls, attribute_name: str) -> Tuple[str, str]:
        """
        Returns which path to use to lookup the attribute.

        By default `(cls.__path, attribute_name)` will be returned.

        Args:
            attribute_name: The name of the attribute to lookup.

        Returns:
            A tuple with the configuration path as the first element and the element name to lookup.
        """
        return cls.__path, attribute_name

    def __init__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None):
        """
        Initialize the new entry.

        Raises:
            PathConflict: An entry is already registered for this path, use the `path` metaclass argument.
            ConfigurationKeyError: An attribute doesn't have a defined value.
        """
        super().__init__(name, bases, dict_)

        cls._register_entry()
        cls._check_undefined_entries()

    def __repr__(cls) -> str:
        """Return a short representation of the entry."""
        if hasattr(cls, '__path'):
            return f"<_ConfigEntryMeta {cls.__name__} at {cls.__path!r}>"
        else:
            return f"<_ConfigEntryMeta {cls.__name__}>"

    def __eq__(cls, other: Any) -> bool:
        """Return true if this entry and the other point to the same path."""
        if not isinstance(other, _ConfigEntryMeta):
            return NotImplemented
        return cls.__path == other.__path


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for new configuration entries.

    Class attributes of the subclasses can be overwritten using YAML configuration files.
    The entry will use its default values and potentially directly override them with already loaded configurations,
    and will also be overwritten in the future by newly loaded configurations.

    The default path used by an entry is the name of the module it is defined in, or the `path` metaclass argument.
    """

    def __init__(self) -> NoReturn:
        """Raises `InvalidOperation` as creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
