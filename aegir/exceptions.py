class AegirException(Exception):
    """Base exception of the ``aegir`` library."""

    pass


class PathConflict(ValueError, AegirException):
    """
    Two configuration entries point to the same path.

    Specify a different path through the ``path`` argument of the metaclass.
    """

    pass


class ConfigurationKeyError(AttributeError, AegirException):
    """An invalid key name has been used."""

    pass


class InvalidOperation(RuntimeError, AegirException):
    """An invalid operation has been performed."""

    pass


class ConfigurationError(ValueError, AegirException):
    """The provided configuration is invalid."""

    pass
