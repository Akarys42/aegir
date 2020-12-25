class SmartconfigBaseException(Exception):
    pass


class DuplicateConfiguration(ValueError, SmartconfigBaseException):
    pass


class ConfigurationKeyError(KeyError, SmartconfigBaseException):
    pass


class InvalidOperation(RuntimeError, SmartconfigBaseException):
    pass


class MalformedYamlFile(SyntaxError, SmartconfigBaseException):
    pass
