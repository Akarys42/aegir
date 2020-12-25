from typing import Dict

import smartconfig
from smartconfig.typehints import _EntryMappingRegister


class _Register:
    """
    Internal register used to reference entries.

    Attributes:
        global_configuration: A mapping of dotted paths to a mapping of attribute names and its value.
        configuration_for_module: A mapping of dotted paths to the corresponding entry.
    """

    def __init__(self):
        self.global_configuration: _EntryMappingRegister = {}
        self.configuration_for_module: Dict[str, smartconfig.ConfigEntry] = {}


# Global register value shared across all entries and function calls.
_register = _Register()
