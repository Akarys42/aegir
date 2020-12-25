import inspect
from itertools import chain
from typing import Dict, List, Optional

from smartconfig.exceptions import ConfigurationKeyError, DuplicateConfiguration, InvalidOperation
from smartconfig.parser import YamlLikeParser
from smartconfig.register import _register
from smartconfig.typehints import EntryType, _EntryMapping, _FilePath


def load_config_file(path: _FilePath) -> None:
    with open(path) as file:
        patch = YamlLikeParser(file.read(), file.name).parse()

    for path, entries in patch.items():
        if path in _register.configuration_for_module:
            _register.configuration_for_module[path]._patch_entries(entries)

        if path not in _register.global_configuration:
            _register.global_configuration[path] = {}
        _register.global_configuration[path].update(entries)


class _ConfigEntryMeta(type):
    def __getattribute__(self: "ConfigEntry", item: str):
        if not type(self) is ConfigEntry:
            raise InvalidOperation("Using _ConfigEntryMeta outside of ConfigEntry isn't currently supported.")

        if item.startswith('_'):
            return super().__getattribute__(item)

        if item not in self._configuration_mapping:
            raise ConfigurationKeyError(f"Entry {self._path} doesn't define any {item} entry.")

        return self._configuration_mapping[item]

    def __new__(mcs, name, bases, dict_):
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

        return super().__new__(mcs, name, bases, dict_)


class ConfigEntry(metaclass=_ConfigEntryMeta):
    _path: str
    _path_override: Optional[str] = None

    _configuration_mapping: Dict[str, EntryType]
    _defined_entries: List[str]

    @classmethod
    def _initialize_class(cls):
        cls._path = cls._path_override or inspect.getmodule(cls).__name__
        if cls._path in _register.configuration_for_module:
            raise DuplicateConfiguration(f"The entry {cls._path} already exist.")  # TODO: Add an FAQ link.

        _register.configuration_for_module[cls._path] = cls

    @classmethod
    def _fetch_configuration(cls):
        if cls._path in _register.global_configuration:
            cls._patch_entries(_register.global_configuration[cls._path])

    @classmethod
    def _check_undefined_entries(cls):
        for entry in cls._defined_entries:
            if entry not in cls._configuration_mapping:
                raise ConfigurationKeyError(f"Entry {entry} isn't defined.")

    @classmethod
    def _patch_entries(cls, patch: _EntryMapping):
        for key, value in patch.items():
            if key not in cls._defined_entries:
                raise ConfigurationKeyError(f"Entry {cls._path} doesn't define any {key} entry.")

            cls._configuration_mapping[key] = value

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls._initialize_class()
        cls._fetch_configuration()
        cls._check_undefined_entries()

    def __init__(self):
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
