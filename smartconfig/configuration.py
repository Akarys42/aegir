import inspect
from itertools import chain
from typing import Any, Dict, List, Optional, Tuple

from smartconfig.exceptions import ConfigurationKeyError, DuplicateConfiguration, InvalidOperation
from smartconfig.parser import YamlLikeParser
from smartconfig.register import _register
from smartconfig.typehints import _EntryMapping, _FilePath


def load_config_file(path: _FilePath) -> None:
    """
    Load a YAML-like configuration file and update configuration entries.

    The values set in the YAML-like file will override values already defined in the `ConfigEntry`.
    For each section, the name of previous sections will be concatenated in order to make the full path of the entry
    to override.

    See `smartconfig.YamlLikeParser` for more details on the syntax.

    Args:
        path: The path to the configuration file. Can be a string or an object defining `os.PathLike`.

    Raises:
        MalformedYamlFile: The configuration file is malformed.
        FileNotFoundError: The configuration file doesn't exist.
        IOError: An error occurred when reading the file.
    """
    with open(path) as file:
        patch = YamlLikeParser(file.read(), file.name).parse()

    for path, entries in patch.items():
        # Patch every already existing entries.
        if path in _register.configuration_for_module:
            _register.configuration_for_module[path]._patch_entries(entries)

        # Update the global register for future entries to use.
        if path not in _register.global_configuration:
            _register.global_configuration[path] = {}
        _register.global_configuration[path].update(entries)


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
        configuration_mapping = {key: value for key, value in dict_.items() if not key.startswith('_')}
        defined_entries = {
            name
            for name
            in chain(
                dict_.keys(),
                dict_.get('__annotations__', {}).keys()
            )
            if not name.startswith('_')
        }

        dict_["_configuration_mapping"] = configuration_mapping
        dict_["_defined_entries"] = defined_entries

        return super().__new__(cls, name, bases, dict_)


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Baseclass for new configuration entries.

    Class attributes of the subclasses can be overwrote using YAML-like configuration files.
    The entry will use its default values and potentially directly override them with already loaded configurations,
    and will also be overwrote in future by newly loaded configurations.

    The path used by an entry is by default the `__name__` attribute of the module it is defined in.

    Attributes:
        _path_override:
            Can be used to override the default `_path` setting.
        _path:
            Path used to reference this entry in the configuration files. Shouldn't be manually set.
        _configuration_mapping:
            Current mapping of attributes. Shouldn't be manually set.
        _defined_entries:
            List of attributes being registered on the class,
            either by giving a concrete value or a typehint. Shouldn't be manually set.
    """

    _path_override: Optional[str] = None

    _path: str
    _configuration_mapping: _EntryMapping
    _defined_entries: List[str]

    @classmethod
    def _register_entry(cls) -> None:
        """Set the `_path` attribute and register the entry."""
        cls._path = cls._path_override or inspect.getmodule(cls).__name__
        if cls._path in _register.configuration_for_module:
            raise DuplicateConfiguration(f"The entry {cls._path} already exist.")  # TODO: Add an FAQ link.

        _register.configuration_for_module[cls._path] = cls

    @classmethod
    def _fetch_configuration(cls) -> None:
        """Load the configuration from the register and apply it."""
        if cls._path in _register.global_configuration:
            cls._patch_entries(_register.global_configuration[cls._path])

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
