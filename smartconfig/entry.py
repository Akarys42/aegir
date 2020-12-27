from itertools import chain
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from smartconfig.exceptions import ConfigurationKeyError, DuplicateConfiguration, InvalidOperation
from smartconfig._registry import registry
from smartconfig.typehints import _EntryMapping


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviors.

    Note: Using this metaclass outside of the library is currently not supported.
    """

    def __getattribute__(cls, item: str) -> Optional[Any]:
        """
        Special attribute lookup function.

        If the attribute name starts with `_`, normal lookup is done, otherwise _configuration_mapping is used.

        Args:
            item: Attribute to lookup

        Raises:
            ConfigurationKeyError: The item doesn't exist.
        """
        # Use the normal lookup for attribute starting with `_`
        if item.startswith('_'):
            return super().__getattribute__(item)

        if item not in cls._configuration_mapping:
            raise ConfigurationKeyError(f"Entry {cls._path} doesn't define any {item} entry.")

        return cls._configuration_mapping[item]

    def __new__(cls, name: str, bases: Tuple[type, ...], dict_: Dict[str, Any]) -> type:
        """Add special attribute to the new entry."""
        dict_["_configuration_mapping"] = {key: value for key, value in dict_.items() if not key.startswith('_')}

        names = chain(dict_.keys(), dict_.get('__annotations__', {}).keys())
        dict_["_defined_entries"] = {name for name in names if not name.startswith('_')}

        return super().__new__(cls, name, bases, dict_)


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for new configuration entries.

    Class attributes of the subclasses can be overwritten using YAML configuration files.
    The entry will use its default values and potentially directly override them with already loaded configurations,
    and will also be overwritten in the future by newly loaded configurations.

    The default path used by an entry is the name of the module it is defined in.

    Attributes:
        _path_override:
            Can be used to override the default `_path` setting.
    """

    _path_override: Optional[str] = None

    _path: str
    _configuration_mapping: _EntryMapping
    _defined_entries: List[str]

    @classmethod
    def _register_entry(cls) -> None:
        """Set the `_path` attribute and register the entry."""
        cls._path = cls._path_override or cls.__module__.__name__
        if cls._path in registry.configuration_for_module:
            raise DuplicateConfiguration(f"An entry at {cls._path} already exists.")  # TODO: Add an FAQ link.

        registry.configuration_for_module[cls._path] = cls

    @classmethod
    def _fetch_configuration(cls) -> None:
        """Load the configuration from the register and apply it."""
        if cls._path in registry.global_configuration:
            cls._patch_entries(registry.global_configuration[cls._path])

    @classmethod
    def _check_undefined_entries(cls) -> None:
        """Raise `ConfigurationKeyError` if any attribute doesn't have a concrete value."""
        for attribute in cls._defined_entries:
            if attribute not in cls._configuration_mapping:
                raise ConfigurationKeyError(f"Entry {attribute} isn't defined.")

    @classmethod
    def _patch_entries(cls, patch: _EntryMapping) -> None:
        """
        Override attributes using the given patch.

        Args:
            patch: Mapping of attribute names to their values

        Raises:
            ConfigurationKeyError: Trying to override an undefined attribute.
        """
        for key, value in patch.items():
            if key not in cls._defined_entries:
                raise ConfigurationKeyError(f"Entry {cls._path} doesn't define any {key} entry.")

            cls._configuration_mapping[key] = value

    def __init_subclass__(cls, **kwargs) -> None:
        """
        Initialize the new entry.

        Raises:
            DuplicateConfiguration: An entry is already registered for this path, use `_path_override`.
            ConfigurationKeyError: An attribute doesn't have a concrete value.
        """
        super().__init_subclass__(**kwargs)

        cls._register_entry()
        cls._fetch_configuration()
        cls._check_undefined_entries()

    def __init__(self) -> NoReturn:
        """Raises `InvalidOperation` as creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
