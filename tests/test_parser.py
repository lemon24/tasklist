import pytest

from parser import Heading, Item, Block, ParseError, parse


data = [
    ('', ' ', '\n', '\n ', '\n\n',
        []),

    ('# one', '\n# one', '#   one', '# one\n\n', '\n\n# one\n\n',
        [Block(Heading('one', 1), [])]),

    ('# one\n# two\n', '\n\n#   one\n# two\n\n',
        [Block(Heading('one', 1), []), Block(Heading('two', 1), [])]),
    ('# one\n## two\n',
        [Block(Heading('one', 1), []), Block(Heading('two', 2), [])]),
    ('## one\n# two\n',
        [Block(Heading('one', 2), []), Block(Heading('two', 1), [])]),
    ('## one\n## two\n',
        [Block(Heading('one', 2), []), Block(Heading('two', 2), [])]),

    ('# one\n- two', '# one\n* two', '# one\n*   two\n',
        '# one\n- []two', '# one\n- [] two', '# one\n- [ ] two', '# one\n-  [ ]  two',
        '# one\n- ()two', '# one\n- () two', '# one\n- ( ) two', '# one\n-  ( )  two',
        '# one\n- []()two', '# one\n- [] ()two', '# one\n- []() two',
        '# one\n- [] () two', '# one\n- [ ] ( ) two',
        '# one\n- [  ] (  ) two', '# one\n-  [  ]  (  )  two',
        [Block(Heading('one', 1), [Item('two', False, 'none')])]),

    ('# one\n- [x] two', '# one\n- [X] two', '# one\n- [ x ]two',
        [Block(Heading('one', 1), [Item('two', True, 'none')])]),

    ('# one\n- (a) two', '# one\n- (A) two', '# one\n- ( a )two',
        [Block(Heading('one', 1), [Item('two', False, 'high')])]),

    ('# one\n- (b) two', '# one\n- (B) two',
        [Block(Heading('one', 1), [Item('two', False, 'medium')])]),

    ('# one\n- (c) two', '# one\n- (C) two',
        [Block(Heading('one', 1), [Item('two', False, 'low')])]),

]
data = [(i, line[-1]) for line in data for i in line[:-1]]

@pytest.mark.parametrize('input, expected', data)
def test_parse(input, expected):
    assert parse(input) == expected


errors = [
    ('text', ' # heading', ' - list', ' * list',
        ("unknown markup", 0)),
    ('# one\ntext', '# one\n # heading', '# one\n - list', '# one\n * list',
        ("unknown markup", 1)),

    ('- one', '- one\n# two',
        ("item before first heading", 0)),

    ('# one\n-[]two', '# one\n-[] two',
        '# one\n-()two', '# one\n-() two',
        '# one\n-[]()two', '# one\n-[] ()two',
        ("unknown markup", 1)),

    ('# one\n- [a] two', '# one\n- [n] two', '# one\n- [a](x) two',
        ("only the following allowed for checked: ' x'", 1)),

     ('# one\n- (x) two', '# one\n- (n) two',
        ("only the following allowed for priority: ' abc'", 1)),

]
errors = [(i, line[-1]) for line in errors for i in line[:-1]]

@pytest.mark.parametrize('input, error_args', errors)
def test_parse_error(input, error_args):
    with pytest.raises(ParseError) as excinfo:
        parse(input)
    assert excinfo.value.args == error_args


error_str = [
    (('message', ), 'message'),
    (('message', None), 'message'),
    (('message', 0), 'message (line 1)'),
    (('message', 1), 'message (line 2)'),
]
@pytest.mark.parametrize('error_args, error_str', error_str)
def test_parse_error_str(error_args, error_str):
    assert str(ParseError(*error_args)) == error_str

