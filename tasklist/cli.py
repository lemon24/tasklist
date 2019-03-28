import click

from .parser import parse
from .renderer import render


@click.group(chain=True)
@click.argument('file', type=click.File('w', lazy=True, atomic=True))
def cli(file):
    pass


@cli.resultcallback()
def process_file(processors, file):
    try:
        with open(file.name) as f:
            blocks = parse(f)
    except FileNotFoundError:
        blocks = []

    for processor in processors:
        processor(blocks)

    render(blocks, file)


@cli.command()
@click.argument('name')
def edit(name):
    from .editor import edit
    from .types import Block, Heading

    def processor(blocks):
        blocks_by_name = {b.heading.text: b for b in blocks}
        block = blocks_by_name.get(name)

        if not block:
            block = Block(Heading(name, 1), [])
            blocks.append(block)

        items = edit(list(block.items), block.heading)
        block.items[:] = items

    return processor


if __name__ == '__main__':
    cli()


