import os
from typing import Dict, Union, List

EntryType = Union[List["EntryType"], Dict[str, "EntryType"], str, int, float]
_EntryMapping = Dict[str, EntryType]
_EntryMappingRegister = [Dict[str, _EntryMapping]]

_FilePath = Union[str, bytes, os.PathLike]
