import re
from typing import List, Optional

from smartconfig.typehints import EntryMappingRegister


TAB_SIZE = 4
INDENT_RE = re.compile(r'^ +')


def _normalize_line(line: str) -> str:
    return line.strip().replace('\t', '').replace(' ', '').split('#', maxsplit=1)[0]


def _get_indent_size(line: str) -> int:
    return INDENT_RE.match(line).end()


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
        line = line.replace('\t', ' ' * TAB_SIZE)

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

    def _parse_line(self, line: str):
        if ':' in line:
            name, value = line.split(':', maxsplit=1)
            if not value:
                self._indent(name)
            else:
                path = '.'.join(self.indent_path)

                if path not in self.parse_tree:
                    self.parse_tree[path] = {}
                self.parse_tree[path][name] = value

    def parse(self) -> EntryMappingRegister:
        for line in self.content_iterator:
            self._process_indent(line)
            self._parse_line(_normalize_line(line))

        return self.parse_tree
