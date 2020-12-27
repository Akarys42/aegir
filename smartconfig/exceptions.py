class SmartconfigException(Exception):
    """Base exception of `smartconfig` library."""
    pass


class DuplicateConfiguration(ValueError, SmartconfigException):
    """Two configuration entries point to the same path. Use `_path_override` to bypass this restriction."""
    pass


class ConfigurationKeyError(KeyError, SmartconfigException):
    """An invalid key name has been used."""
    pass


class InvalidOperation(RuntimeError, SmartconfigException):
    """An invalid operation has been performed."""
    pass


class MalformedYamlFile(SyntaxError, SmartconfigException):
    """
    The YAML-Like configuration file is malformed.

    Args:
        msg: Formatted exception message.
        source_file: Name of the source file.
        line_no: Line number that triggered the error.
        line: Line that triggered the error.
    """
    def __init__(self, msg: str, source_file: str, line_no: int, line: str) -> None:
        self.source_file = source_file
        self.line_no = line_no
        self.line = line

        super().__init__(msg)
