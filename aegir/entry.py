import contextlib
from itertools import chain
from typing import Any, Dict, List, MutableMapping, NoReturn, Optional, Tuple

from aegir import _registry
from aegir._registry import get_attribute, unload_defaults, used_paths
from aegir.exceptions import (
    ConfigurationError,
    ConfigurationKeyError,
    InvalidOperation,
    PathConflict,
)


_unchecked_entries: List["_ConfigEntryMeta"] = []


def check_attributes() -> None:
    """
    For all unchecked entries, check that all their attributes have defined values.

    This is only useful if ``check_attributes`` was set to False after loading a configuration.

    Raises:
        ConfigurationKeyError: An attribute of an entry doesn't have a defined value.
    """
    while _unchecked_entries:
        _unchecked_entries.pop()._check_undefined_entries()


class _ConfigEntryMeta(type):
    """
    Metaclass used to define special ConfigEntry behaviour.

    See the documentation of :class:`ConfigEntry`.

    Note: Using this metaclass outside of the library is currently not supported.
    """

    def __getattribute__(cls, name: str) -> Any:
        """
        Look up the attribute through the configuration system.

        If the attribute's name starts with ``_``, use the default Python behaviour for attribute lookup.
        Otherwise, retrieve the value from the loaded configurations or the default value.

        Args:
            name: Name of the attribute to retrieve.

        Raises:
            ConfigurationError: A node along the path is not a mapping node.
            ConfigurationKeyError: The attribute doesn't exist.
        """
        if name.startswith("_"):
            return super().__getattribute__(name)

        return get_attribute(cls.__path, name)

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        dict_: Dict[str, Any],
        path: Optional[str] = None,
        check_attributes: bool = True,
    ) -> type:
        """Create and return new instance (a class) of this type."""
        return super().__new__(cls, name, bases, dict_)

    def _register_entry(cls) -> None:
        """Register the entry's path and store its default values in the global configuration."""
        node = _registry.get_node(cls.__path, create=True)
        if not isinstance(node, MutableMapping):
            raise ConfigurationError(
                f"Node at path {cls.__path!r} isn't a mutable mapping."
            )

        for key, value in cls.__dict__.items():
            # Ignore "private" attributes and only write values that aren't already defined.
            if not key.startswith("_") and key not in node:
                node[key] = value

        used_paths.add(cls.__path)

    def _check_undefined_entries(cls) -> None:
        """Raise :class:`ConfigurationKeyError` if any attribute doesn't have a defined value."""
        for attribute in chain(
            cls.__dict__.keys(), getattr(cls, "__annotations__", ())
        ):
            if not attribute.startswith("_"):
                try:
                    get_attribute(cls.__path, attribute)
                except (ConfigurationError, ConfigurationKeyError):
                    raise ConfigurationKeyError(
                        f"Attribute {attribute!r} doesn't have a defined value."
                    ) from None

    def __init__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        dict_: Dict[str, Any],
        path: Optional[str] = None,
        check_attributes: bool = True,
    ):
        """Initialise the new entry."""
        super().__init__(name, bases, dict_)

        cls.__path = path or cls.__module__
        if cls.__path in _registry.used_paths:
            raise PathConflict(f"An entry at {cls.__path!r} already exists.")

        cls._register_entry()
        if check_attributes:
            cls._check_undefined_entries()
        else:
            _unchecked_entries.append(cls)

    def __del__(cls) -> None:
        """Remove the default values from the global configuration and free the entry's path."""
        try:
            unload_defaults(cls.__path)
        except (ConfigurationError, ConfigurationKeyError):
            # Fail silently because the same error may have already been raised while the object was being initialised.
            # There's no way to distinguish such case from the state being modified after successful initialisation.
            # Besides, there's nothing that can be done for cleanup if the node can't be retrieved.
            return

        # If the node has already been cleaned up we don't want this to error out
        with contextlib.suppress(KeyError):
            used_paths.remove(cls.__path)

    def __repr__(cls) -> str:
        """Return a short representation of the entry."""
        if cls is ConfigEntry:
            return super().__repr__()
        else:
            return f"<ConfigEntry {cls.__qualname__!r} at {cls.__path!r}>"


class ConfigEntry(metaclass=_ConfigEntryMeta):
    """
    Base class for configuration entries.

    Values of class attributes can be overwritten by loading YAML configuration files. Otherwise, their given default
    values will be used. The exception is class attributes whose names begin with an underscore; they always behave like
    normal class attributes and therefore their values cannot be overwritten by config files.

    Args:
        path (str): Path to use for attribute lookup in the config.
            Default to the containing module's fully-qualified name when the value is None or an empty string.
        check_attributes (bool): True if a check should be performed for attributes without defined values.
            If False, :func:`check_attributes()` can be manually called later. Default to True.

    Raises:
        PathConflict: An entry is already registered at ``path``.
        ConfigurationError: A node along ``path`` is not a mapping node.
        ConfigurationKeyError: A class attribute doesn't have a defined value.
        InvalidOperation: This class or a subclass of it is instantiated.
    """

    def __init__(self) -> NoReturn:
        """Raise :class:`InvalidOperation` because creating instances isn't allowed."""
        raise InvalidOperation("Creating instances of ConfigEntry isn't allowed.")
