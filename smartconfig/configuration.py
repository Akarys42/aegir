import inspect
from itertools import chain
from typing import Dict, List, Optional

from smartconfig.register import register
from smartconfig.typehints import EntryType, EntryMapping


class ConfigEntryMeta(type):
    def __getattribute__(self: "ConfigEntry", item: str):
        if item.startswith('_'):
            return super().__getattribute__(item)

        if item not in self._configuration_mapping:
            raise ...

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


class ConfigEntry(metaclass=ConfigEntryMeta):
    _path: str
    _path_override: Optional[str] = None

    _configuration_mapping: Dict[str, EntryType]
    _defined_entries: List[str]

    @classmethod
    def _initialize_class(cls):
        cls._path = cls._path_override or inspect.getmodule(cls).__name__
        if cls._path in register.configuration_for_module:
            raise ...

        register.configuration_for_module[cls._path] = cls

    @classmethod
    def _fetch_configuration(cls):
        if cls._path in register.global_configuration:
            cls._patch_entries(register.global_configuration[cls._path])

    @classmethod
    def _check_undefined_entries(cls):
        for entry in cls._defined_entries:
            if entry not in cls._configuration_mapping:
                raise ...

    @classmethod
    def _patch_entries(cls, patch: EntryMapping):
        for key, value in patch.items():
            if key not in cls._defined_entries:
                raise ...

            cls._configuration_mapping[key] = value

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls._initialize_class()
        cls._fetch_configuration()
        cls._check_undefined_entries()

    def __init__(self):
        raise ...
