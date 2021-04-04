from typing import Any

import yaml

from smartconfig._registry import get_attribute, get_node
from smartconfig.exceptions import InvalidOperation

_used_constructors = set()


class AttributeReference:
    """
    A descriptor referencing an attribute in a config entry.

    Args:
        path: A dot-delimited path to the attribute being referenced.
    """

    def __init__(self, path: str) -> None:
        if path in _used_constructors:
            raise InvalidOperation("Cannot point a REF constructor to another one.")
        _used_constructors.add(path)

        self.full_path = path

        if '.' in path:
            self.path, self.attribute = path.rsplit('.', maxsplit=1)
        else:
            self.path = path
            self.attribute = None

    def __get__(self, *_) -> Any:
        if self.attribute is not None:
            return get_attribute(self.path, self.attribute)
        else:
            return get_node(self.path)

    def __set__(self, *_) -> None:
        return

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.full_path})"


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> AttributeReference:
    """Return a descriptor which references another node."""
    return AttributeReference(node.value)
