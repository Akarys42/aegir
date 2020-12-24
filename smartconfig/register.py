from typing import Dict

import smartconfig
from smartconfig.typehints import EntryMappingRegister


class Register:
    def __init__(self):
        self.global_configuration: EntryMappingRegister = {}
        self.configuration_for_module: Dict[str, smartconfig.ConfigEntry] = {}


register = Register()
