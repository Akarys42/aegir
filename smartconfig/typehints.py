import os
from typing import Any, Dict, Union

# The possible types of an entry.
EntryType = Any
# A map of an attribute name to its value
_EntryMapping = Dict[str, EntryType]
# A map of a dotted path to its `_EntryMapping`.
_EntryMappingRegistry = Dict[str, _EntryMapping]

# The possible types of a file path.
_FilePath = Union[str, bytes, os.PathLike]
