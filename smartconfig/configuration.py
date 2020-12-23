from typing import Dict, List

EntryType = ...


class ConfigEntryMeta(type):
    def __getattribute__(self: "ConfigEntry", item: str):
        if item.startswith('_'):
            return super().__getattribute__(item)

        if item not in self._configuration_mapping:
            raise ...

        return self._configuration_mapping[item]

    def __new__(mcs, name, bases, dict_):
        configuration_mapping = {}
        defined_entries = []

        dict_["_configuration_mapping"] = configuration_mapping
        dict_["_defined_entries"] = defined_entries

        return super().__new__(mcs, name, bases, dict_)


class ConfigEntry(metaclass=ConfigEntryMeta):
    _configuration_mapping: Dict[str, EntryType]
    _defined_entries: List[str]

    @classmethod
    def _initialize_class(cls):
        cls._defined_entries = [name for name in cls.__annotations__.keys() if not name.startswith('_')]
        cls._configuration_mapping = {key: value for key, value in cls.__dict__.items() if not key.startswith('_')}

    @classmethod
    def _fetch_configuration(cls):
        ...

    @classmethod
    def _check_undefined_entries(cls):
        for entry in cls._defined_entries:
            if entry not in cls._configuration_mapping:
                raise ...

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        cls._initialize_class()
        cls._fetch_configuration()
        cls._check_undefined_entries()

    def __init__(self):
        raise ...
