from collections import namedtuple


Heading = namedtuple('Heading', 'text level')
Item = namedtuple('Item', 'text checked priority')
Block = namedtuple('Block', 'heading items')


