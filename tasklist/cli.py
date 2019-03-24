import click

from .parser import parse
from .renderer import render
from .editor import edit
from .types import Block, Heading


@click.command()
@click.argument('file', type=click.File('w', lazy=True, atomic=True))
@click.argument('name')
def main(file, name):
    try:
        with open(file.name) as f:
            blocks = parse(f)
    except FileNotFoundError:
        blocks = []

    blocks_by_name = {b.heading.text: b for b in blocks}
    block = blocks_by_name.get(name)

    if not block:
        block = Block(Heading(name, 1), [])
        blocks.append(block)

    items = edit(list(block.items))
    block.items[:] = items

    render(blocks, file)


if __name__ == '__main__':
    main()


