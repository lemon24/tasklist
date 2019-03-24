import re
import io
from collections import Counter

from .types import Block, Heading, Item


class ParseError(Exception):

    def __init__(self, message, line=None):
        super().__init__(message, line)
        self.message = message
        self.line = line

    def __str__(self):
        message = self.message
        if self.line is not None:
            message = "{} (line {})".format(message, self.line + 1)
        return message


class Parser:

    empty_re = re.compile(r'\s*$')

    heading_re = re.compile(r"""
        (?P<hashes> \#+)
        \s+
        (?P<text> .*) $
    """, re.VERBOSE)

    item_re = re.compile(r"""
        (?P<bullet> [-*])
        \s+
        ( \[ \s* (?P<checked> \S+)? \s* \] \s* )?
        ( \( \s* (?P<priority> \S+)? \s* \) \s* )?
        (?P<text> .*) $
    """, re.VERBOSE)

    def is_empty(self, line):
        return bool(self.empty_re.match(line))

    def parse_heading(self, line, line_no):
        match = self.heading_re.match(line)
        if not match:
            return None

        return Heading(match.group('text'), len(match.group('hashes')))

    def parse_item(self, line, line_no):
        match = self.item_re.match(line)
        if not match:
            return None

        checked = (match.group('checked') or '').lower()
        if checked and checked != 'x':
            raise ParseError("only the following allowed for checked: ' x'", line_no)

        priority = (match.group('priority') or '').lower()
        if priority and priority not in ('a', 'b', 'c'):
            raise ParseError("only the following allowed for priority: ' abc'", line_no)

        return Item(
            match.group('text'),
            bool(checked),
            priority,
        )

    def parse_into_values(self, lines):
        for line_no, line in enumerate(lines):
            line = line.rstrip('\n')

            if self.is_empty(line):
                continue

            value = (
                self.parse_heading(line, line_no) or
                self.parse_item(line, line_no)
            )
            if value:
                yield line_no, value
                continue

            raise ParseError("unknown markup", line_no)

    def parse_into_blocks(self, file):
        heading = None
        items = []

        for line_no, value in self.parse_into_values(file):
            if isinstance(value, Heading):
                if heading:
                    yield heading, items
                else:
                    assert not items, "item before first heading"

                heading = value
                items = []

            elif isinstance(value, Item):
                if not heading:
                    raise ParseError("item before first heading", line_no)

                items.append(value)

            else:
                assert False, "unexpected value type: {!r} (line {})".format(value, line_no)

        if heading:
            yield heading, items

    def parse(self, file):
        if isinstance(file, str):
            file = io.StringIO(file)

        blocks = [
            Block(heading, items)
            for heading, items in self.parse_into_blocks(file)
        ]

        headings = [b.heading.text for b in blocks]
        heading_counts = Counter(headings)
        duplicate_headings = [h for h in headings if heading_counts[h] > 1]
        if duplicate_headings:
            raise ParseError("headings appear multiple times: " +
                             ', '.join(repr(h) for h in duplicate_headings))

        return blocks


parse = Parser().parse


