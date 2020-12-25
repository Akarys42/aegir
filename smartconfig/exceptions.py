class SmartconfigBaseException(Exception):
    """Base exception of `smartconfig` library."""
    pass


class DuplicateConfiguration(ValueError, SmartconfigBaseException):
    """Two configuration entries point to the same path. Use `_path_override` to bypass this restriction."""
    pass


class ConfigurationKeyError(KeyError, SmartconfigBaseException):
    """An invalid key name has been used."""
    pass


class InvalidOperation(RuntimeError, SmartconfigBaseException):
    """An invalid operation has been performed."""
    pass


class MalformedYamlFile(SyntaxError, SmartconfigBaseException):
    """The YAML-Like configuration file is malformed."""
    # TODO: Add some attribute to this exception.
    pass
