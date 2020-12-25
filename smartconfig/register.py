from typing import Dict

import smartconfig
from smartconfig.typehints import _EntryMappingRegister


class _Register:
    def __init__(self):
        self.global_configuration: _EntryMappingRegister = {}
        self.configuration_for_module: Dict[str, smartconfig.ConfigEntry] = {}


_register = _Register()
