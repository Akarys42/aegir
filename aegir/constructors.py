from typing import Any, Dict, List, NoReturn

import yaml

from aegir._registry import get_attribute, get_node
from aegir.exceptions import ConfigurationError, ConfigurationKeyError

_constructor_mapping: Dict["AttributeReference", Any] = {}
_unchecked_constructors: List["AttributeReference"] = []


class AttributeReference:
    """
    A descriptor referencing an attribute in a config entry.

    Args:
        path: A dot-delimited path to the attribute being referenced.
    """

    def __init__(self, path: str) -> None:
        self.full_path = path

        if "." in path:
            self.path, self.attribute = path.rsplit(".", maxsplit=1)
        else:
            self.path = path
            self.attribute = None

    def check_circular_reference(self) -> None:
        """Raise ConfigurationError if a circular reference is detected."""
        visited_references = set()
        current_constructor = self

        while hasattr(current_constructor, "__get__"):
            if current_constructor in visited_references:
                raise ConfigurationError(
                    f"Circular reference starting at !REF {self.full_path}."
                )
            visited_references.add(current_constructor)

            # Only pass follow_descriptors for AttributeReference since it's a custom argument.
            if isinstance(current_constructor, AttributeReference):
                try:
                    current_constructor = current_constructor.__get__(
                        follow_descriptors=False
                    )
                except (ConfigurationError, ConfigurationKeyError):
                    # Reached the end of the chain.
                    break
            else:
                current_constructor = current_constructor.__get__()

    def __get__(self, *_, follow_descriptors: bool = True) -> Any:
        if self.attribute is not None:
            return get_attribute(self.path, self.attribute, follow_descriptors)
        else:
            return get_node(self.path, follow_descriptors)

    def __set__(self, *_) -> NoReturn:
        raise NotImplementedError("Setting the value of a reference is not supported.")

    def __repr__(self):
        return f"{self.__class__.__name__}(path={self.full_path})"


def _ref_constructor(loader: yaml.SafeLoader, node: yaml.Node) -> AttributeReference:
    """Return a descriptor which references another node."""
    ref = AttributeReference(node.value)
    _unchecked_constructors.append(ref)
    return ref
