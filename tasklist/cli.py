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


@cli.command()
@click.argument('source')
@click.argument('dest')
def copy(source, dest):
    def processor(blocks):
        blocks_by_name = {b.heading.text: b for b in blocks}
        source_block = blocks_by_name.get(source)

        if not source_block or not source_block.items:
            return

        dest_block = blocks_by_name.get(dest)
        if not dest_block:
            dest_block = Block(Heading(name, 1), [])
            blocks.append(dest_block)

        dest_block.items.extend(source_block.items)

    return processor


@cli.command()
@click.argument('source')
@click.argument('dest')
def move(source, dest):
    def processor(blocks):
        blocks_by_name = {b.heading.text: b for b in blocks}
        source_block = blocks_by_name.get(source)

        if not source_block or not source_block.items:
            return

        dest_block = blocks_by_name.get(dest)
        if not dest_block:
            dest_block = Block(Heading(name, 1), [])
            blocks.append(dest_block)

        dest_block.items.extend(source_block.items)
        source_block.items[:] = []

    return processor


@cli.command('set')
@click.argument('name')
@click.option('--checked/--no-checked', default=None)
@click.option('--priority', type=click.Choice(['a', 'b', 'c', '']))
def set_(name, checked, priority):
    # FIXME: Passing --checked or --priority shows help text.

    def processor(blocks):
        blocks_by_name = {b.heading.text: b for b in blocks}
        block = blocks_by_name.get(name)

        if not block or not block.items:
            return

        def update_item(item):
            if checked is not None:
                item = item._replace(checked=checked)
            if priority is not None:
                item = item._replace(priority=priority)
            return item

        block.items[:] = [update_item(item) for item in block.items]

    return processor



if __name__ == '__main__':
    cli()


