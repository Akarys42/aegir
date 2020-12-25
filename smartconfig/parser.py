import re
import textwrap
from ast import literal_eval
from dataclasses import dataclass
from typing import List, NoReturn, Optional

from smartconfig.exceptions import MalformedYamlFile
from smartconfig.typehints import EntryType, _EntryMappingRegister

TAB_SIZE = 4
INDENT_RE = re.compile(r'^ +')


def _normalize_line(line: str) -> str:
    """Normalize the line by stripping, removing spaces, tabs, and comments."""
    return line.strip().replace('\t', '').replace(' ', '').split('#', maxsplit=1)[0]


def _get_indent_size(line: str) -> int:
    """Use `INDENT8RE` to get the number of spaces before the first character in the line."""
    return INDENT_RE.match(line).end()


@dataclass
class _TypeParseResult:
    """
    Result of a type parsing operation.

    Attributes:
        result: The actual result of the parse.
        parse_back: A line to parse back if the parser consumed one more line.
    """

    result: EntryType
    parse_back: Optional[str]


class YamlLikeParser:
    """
    Parse a YAML-like configuration file.

    Arbitrary nested blocks are supported, and they are concatenated to make the final path.
    Values are parsed using `ast.literal_eval`, and given as string if it failed and the value is alphanumerical.
    Multiline strings starting with `|` and bullet lists using `-` are supported.
    """

    def __init__(self, content: str, source_file: Optional[str] = "<input>") -> None:
        """
        Initialize a new parser.

        Note: Actual parsing is done using the `parse` method.

        Args:
            content: Content of the file to parse
            source_file: Name of the file, used in error handling. `<input>` by default.
        """
        self.content = content
        self.content_iterator = filter(lambda line: len(line.strip()) > 0, iter(self.content))
        self.source_file = source_file

        # Size of each indentation level.
        self.indent_size: Optional[int] = None
        # Current indentation level.
        self.indent_level: int = 0
        # Expected indentation level on the next line.
        self.expected_indent_level: int = 0

        self.indent_path: List[str] = []

        self.parse_tree: _EntryMappingRegister = {}

    def _abort(self, message: str) -> NoReturn:
        """Abort the parsing and raise `MalformedYamlFile` with the given message."""
        # Tuple of every line taht could have been used in `content_iterator`
        parsed_content = tuple(filter(lambda line: len(line.strip()) > 0, self.content.split('\n')))

        remaining_lines = len(tuple(self.content_iterator))
        line_no = len(parsed_content) - remaining_lines

        exception = f"{message}:\n{self.source_file}:{line_no} | {parsed_content[line_no - 1].strip()}"
        raise MalformedYamlFile(exception)

    def _process_indent(self, line: str) -> None:
        """
        Check indentation level and call `_dedent` if needed.

        Args:
            line: Line to check indentation on. Shouldn't be normalized.

        Raises:
             MalformedYamlFile: Indent size doesn't match indentation size or unexpected indent
        """
        line = line.expandtabs(TAB_SIZE)

        # We don't know the size of the indentation level, so we define it.
        if not self.indent_size and line.startswith(' '):
            self.indent_size = _get_indent_size(line)

        # We continue only if we know the size of an indent.
        if self.indent_size:
            size = _get_indent_size(line)

            # If the parity isn't 0, we have an odd number of spaces that can't form a full indent level.
            level, parity = divmod(size, self.indent_size)
            if parity != 0:
                self._abort("Indent size doesn't match indentation size")

            # The indentation level has been reduced, we dedent.
            if level < self.indent_level:
                self._dedent(self.indent_level - level)
                self.indent_level = level

            # The indentation level has been augmented.
            elif level > self.indent_level:
                # We check if we expected this indent.
                if level != self.expected_indent_level:
                    self._abort("Unexpected indent")

                # We set the new indentation level, and leave the `_indent` call to `_parse_line`.
                self.indent_level = level

    def _indent(self, path: str) -> None:
        """
        Register an indent.

        Args:
            path: The name of the new indented section.
        """
        self.indent_path.append(path)
        self.expected_indent_level += 1

    def _dedent(self, level: int) -> None:
        """
        Register a dedent.

        Args:
            level: The amount of levels to dedent.
        """
        self.indent_path = self.indent_path[:-level]
        self.expected_indent_level -= level

    def _parse_multiline_string(self) -> _TypeParseResult:
        """
        Parse a multiline string.

        The string starts on the next line, and continue until a line with `:` is found.

        Returns:
            The parsed dedented string and the last line as a parse-back.
        """
        buffer = ''

        while ':' not in _normalize_line((line := next(self.content_iterator))):
            buffer += '\n' + line

        # We consumed one more line because we had to check if it contains a `:`, so we parse it back.
        return _TypeParseResult(textwrap.dedent(buffer), line)

    def _parse_multiline_list(self, start_line: str) -> _TypeParseResult:
        """
        Parse a bullet list.

        Starts on the given `start_line` and continue until a line not starting with `-` is found.

        Args:
            start_line: The first line of the bullet line. Should be normalized.

        Returns:
            The list and the last line as a parse-back.
        """
        buffer = [self._parse_simple(start_line[1:])]

        while _normalize_line((line := next(self.content_iterator))).startswith('-'):
            buffer.append(self._parse_simple(_normalize_line(line)[1:]))

        # We consumed one more line because we had to check if it started with `-`, so we parse it back.
        return _TypeParseResult(buffer, line)

    def _parse_type(self, line: str) -> EntryType:
        """
        Parse an object.

        It will delegate parsing to one of the multiline parsers, or will fallback on `_parse_simple`, and process
        the `_TypeParseResult`.

        Args:
            line: The object to parse.

        Returns:
            The parsed object
        """
        if line == '|':
            result = self._parse_multiline_string()
        elif line.startswith('-'):
            result = self._parse_multiline_list(line)
        else:
            return self._parse_simple(line)

        # If we have a parse back, we run a normal line processing routine.
        if result.parse_back:
            self._process_indent(result.parse_back)
            self._parse_line(_normalize_line(result.parse_back))
        return result.result

    def _parse_simple(self, line: str) -> EntryType:
        """
        Parse a simple inline object using `ast.literal_eval`.

        It will first try to parse using `literal_eval`, and if it fails it will return it as a string if it is fully
        alphanumerical, otherwise it will raise MalformedYamlFile.

        Args:
            line: The object to parse.

        Returns:
            The parsed object

        Raises:
            MalformedYamlFile: `ast.literal_eval` couldn't parse it and the string isn't alphanumerical.
        """
        try:
            return literal_eval(line)
        except (ValueError, SyntaxError):
            if line.isalnum():
                return line
            else:
                # If the parsing failed and the object isn't alnum, we can assume that it is a typo.
                self._abort(f"Failed to parse value {line}")

    def _parse_line(self, line: str) -> None:
        """
        Parse one line.

        This function will split the line in half around `:`.
        If there is no value on the right side, it will call `_indent`, otherwise it will create a dotted path by
        joining the whole indent path, and map the name on the left side to the parsed value on the right side inside
        this path.

        Args:
            line: The line to parse. Should be normalized.
        """
        # We skip lines without `:`
        if ':' in line:
            name, value = line.split(':', maxsplit=1)

            # No value has been set here, it is probably an indent.
            if not value:
                self._indent(name)
            else:
                path = '.'.join(self.indent_path)

                if path not in self.parse_tree:
                    self.parse_tree[path] = {}
                self.parse_tree[path][name] = self._parse_type(value)

    def parse(self) -> _EntryMappingRegister:
        """
        Run the whole parse routine and return the parse tree.

        Returns:
            A mapping of dotted paths to a mapping of attribute names and its value.
        """
        for line in self.content_iterator:
            self._process_indent(line)
            self._parse_line(_normalize_line(line))

        return self.parse_tree
