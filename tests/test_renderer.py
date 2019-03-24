import io

import pytest

from tasklist.renderer import render
from tasklist.types import Heading, Item, Block


def test_render():
    blocks = [
        Block(Heading('one', 2), [
        ]),
        Block(Heading('two', 1), [
            Item('item two-one', False, ''),
            Item('item two-two', True, ''),
            Item('item two-three', False, 'a'),
        ]),
        Block(Heading('three', 2), [
            Item('item three-one', True, 'b'),
        ]),
    ]

    string = """\
## one

# two

- item two-one
- [x] item two-two
- (a) item two-three

## three

- [x] (b) item three-one

"""

    assert ''.join(render(blocks)) == string

    file = io.StringIO()
    render(blocks, file)
    assert file.getvalue() == string


