import re
import textwrap
from ast import literal_eval
from dataclasses import dataclass
from typing import List, Optional

from smartconfig.typehints import EntryMappingRegister, EntryType

TAB_SIZE = 4
INDENT_RE = re.compile(r'^ +')


def _normalize_line(line: str) -> str:
    return line.strip().replace('\t', '').replace(' ', '').split('#', maxsplit=1)[0]


def _get_indent_size(line: str) -> int:
    return INDENT_RE.match(line).end()


@dataclass
class TypeParseResult:
    result: EntryType
    parse_back: Optional[str]


class YamlLikeParser:
    def __init__(self, content: str) -> None:
        self.content = content.split('\n')
        self.content_iterator = filter(lambda line: len(line.strip()) > 0, iter(self.content))

        self.indent_size: Optional[int] = None
        self.indent_level: int = 0
        self.expected_indent_level: int = 0

        self.indent_path: List[str] = []

        self.parse_tree: EntryMappingRegister = {}

    def _process_indent(self, line: str) -> None:
        line = line.expandtabs(TAB_SIZE)

        if not self.indent_size and line.startswith(' '):
            self.indent_size = _get_indent_size(line)

        if self.indent_size:
            size = _get_indent_size(line)

            level, parity = divmod(size, self.indent_size)
            if parity != 0:
                raise ...

            if level < self.indent_level:
                self._dedent(self.indent_level - level)
                self.indent_level = level
                return

            if level > self.indent_level:
                if level != self.expected_indent_level:
                    raise ...
                self.indent_level = level

    def _indent(self, path: str) -> None:
        self.indent_path.append(path)
        self.expected_indent_level += 1

    def _dedent(self, level: int) -> None:
        self.indent_path = self.indent_path[:-level]
        self.expected_indent_level -= level

    def _parse_multiline_string(self) -> TypeParseResult:
        buffer = ''

        while ':' not in _normalize_line((line := next(self.content_iterator))):
            buffer += '\n' + line

        return TypeParseResult(textwrap.dedent(buffer), line)

    def _parse_multiline_list(self, start_line: str) -> TypeParseResult:
        buffer = [self._parse_simple(start_line[1:])]

        while _normalize_line((line := next(self.content_iterator))).startswith('-'):
            buffer.append(self._parse_simple(_normalize_line(line)[1:]))

        return TypeParseResult(buffer, line)

    def _parse_type(self, line: str) -> EntryType:
        if line == '|':
            result = self._parse_multiline_string()
        elif line.startswith('-'):
            result = self._parse_multiline_list(line)
        else:
            return self._parse_simple(line)

        if result.parse_back:
            self._process_indent(result.parse_back)
            self._parse_line(_normalize_line(result.parse_back))
        return result.result

    @staticmethod
    def _parse_simple(line: str) -> EntryType:
        try:
            return literal_eval(line)
        except ValueError:
            if line.isalnum():
                return line
            else:
                raise ...

    def _parse_line(self, line: str):
        if ':' in line:
            name, value = line.split(':', maxsplit=1)
            if not value:
                self._indent(name)
            else:
                path = '.'.join(self.indent_path)

                if path not in self.parse_tree:
                    self.parse_tree[path] = {}
                self.parse_tree[path][name] = self._parse_type(value)

    def parse(self) -> EntryMappingRegister:
        for line in self.content_iterator:
            self._process_indent(line)
            self._parse_line(_normalize_line(line))

        return self.parse_tree
