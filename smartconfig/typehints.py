from typing import Dict, Union, List

EntryType = Union[List["EntryType"], Dict[str, "EntryType"], str, int, float]
EntryMapping = Dict[str, EntryType]
EntryMappingRegister = [Dict[str, EntryMapping]]
