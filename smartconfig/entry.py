from itertools import chain
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from smartconfig._registry import registry
from smartconfig.exceptions import ConfigurationKeyError, DuplicateConfiguration, InvalidOperation


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviors.

    Note: Using this metaclass outside of the library is currently not supported.
    """

    def __getattribute__(cls, item: str) -> Optional[Any]:
        """
        Special attribute lookup function.

        If the attribute name starts with `_`, normal lookup is done, otherwise registry.global_configuration is used.

        Args:
            item: Attribute to lookup

        Raises:
            ConfigurationKeyError: The item doesn't exist.
        """
        # Use the normal lookup for attribute starting with `_`
        if item.startswith('_'):
            return super().__getattribute__(item)

        if item not in registry.global_configuration[cls._path]:
            raise ConfigurationKeyError(f"Entry {cls._path} doesn't define any {item} entry.")

        return registry.global_configuration[cls._path][item]

    def __new__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any], path: Optional[str] = None) -> type:
        """
        Add special attribute to the new entry.

        Args:
            path: Custom path used for this entry instead of the module name.
        """
        names = chain(dict_.keys(), dict_.get('__annotations__', {}).keys())
        dict_["_defined_entries"] = {name for name in names if not name.startswith('_')}

        dict_["_path_override"] = path

        return super().__new__(cls, name, bases, dict_)

    def __repr__(cls) -> str:
        """Return a short representation of the entry."""
        return f"<{cls.__name__} entry at {cls._path}>"

    def __eq__(cls, other: Any) -> bool:
        """Return true if this entry and the other point to the same path."""
        if not isinstance(other, _ConfigEntryMeta):
            return NotImplemented
        return cls._path == other._path


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for new configuration entries.

    Class attributes of the subclasses can be overwritten using YAML configuration files.
    The entry will use its default values and potentially directly override them with already loaded configurations,
    and will also be overwritten in the future by newly loaded configurations.

    The default path used by an entry is the name of the module it is defined in, or the `path` metaclass argument.
    """

    _path: str
    _path_override: Optional[str]
    _defined_entries: List[str]

    @classmethod
    def _register_entry(cls) -> None:
        """Set the `_path` attribute and register the entry."""
        cls._path = cls._path_override or cls.__module__
        if cls._path in registry.configuration_for_module:
            raise DuplicateConfiguration(f"An entry at {cls._path} already exists.")  # TODO: Add an FAQ link.

        registry.global_configuration[cls._path] = {
            key: value for key, value in cls.__dict__.items() if not key.startswith('_')
        }

        registry.configuration_for_module[cls._path] = cls

    @classmethod
    def _check_undefined_entries(cls) -> None:
        """Raise `ConfigurationKeyError` if any attribute doesn't have a concrete value."""
        for attribute in cls._defined_entries:
            if attribute not in registry.global_configuration[cls._path]:
                raise ConfigurationKeyError(f"Entry {attribute} isn't defined.")

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize the new entry.

        Raises:
            DuplicateConfiguration: An entry is already registered for this path, use `_path_override`.
            ConfigurationKeyError: An attribute doesn't have a concrete value.
        """
        super().__init_subclass__(**kwargs)

        cls._register_entry()
        cls._check_undefined_entries()

    def __init__(self) -> NoReturn:
        """Raises `InvalidOperation` as creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
