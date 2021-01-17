"""
Internal register used to reference entries.

Attributes:
    global_configuration: A mapping of dotted paths to a mapping of attribute names and its value.
    configuration_for_module: A mapping of dotted paths to the corresponding entry.
"""

from typing import Dict

import smartconfig
from smartconfig.typehints import _EntryMappingRegistry


global_configuration: _EntryMappingRegistry = {}
configuration_for_module: Dict[str, "smartconfig.ConfigEntry"] = {}
