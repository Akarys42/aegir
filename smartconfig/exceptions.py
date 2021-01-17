class SmartconfigException(Exception):
    """Base exception of `smartconfig` library."""
    pass


class DuplicateConfiguration(ValueError, SmartconfigException):
    """
    Two configuration entries point to the same path.

    Provide a `path` argument to the metaclass to bypass this restriction.
    """
    pass


class ConfigurationKeyError(KeyError, SmartconfigException):
    """An invalid key name has been used."""
    pass


class InvalidOperation(RuntimeError, SmartconfigException):
    """An invalid operation has been performed."""
    pass
