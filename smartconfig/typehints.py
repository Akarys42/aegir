import os
from typing import Dict, Union, List

EntryType = Union[List["EntryType"], Dict[str, "EntryType"], str, int, float]
EntryMapping = Dict[str, EntryType]
EntryMappingRegister = [Dict[str, EntryMapping]]

_FilePath = Union[str, bytes, os.PathLike]
