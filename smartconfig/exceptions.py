class SmartconfigException(Exception):
    """Base exception of the `smartconfig` library."""
    pass


class PathConflict(ValueError, SmartconfigException):
    """
    Two configuration entries point to the same path.

    Specify a different path through the `path` argument of the metaclass.
    """
    pass


class ConfigurationKeyError(AttributeError, SmartconfigException):
    """An invalid key name has been used."""
    pass


class InvalidOperation(RuntimeError, SmartconfigException):
    """An invalid operation has been performed."""
    pass


class ConfigurationError(ValueError, SmartconfigException):
    """The provided configuration is invalid."""
    pass
