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
@click.option('--bind-move', nargs=2, metavar='KEY NAME')
def edit(name, bind_move):
    from .editor import edit
    from .types import Block, Heading

    def processor(blocks):
        move_key, move_target = bind_move if bind_move else (None, None)

        blocks_by_name = {b.heading.text: b for b in blocks}
        block = blocks_by_name.get(name)

        if not block:
            block = Block(Heading(name, 1), [])
            blocks.append(block)

        items, moved_items = edit(list(block.items), block.heading, move_key=move_key)
        block.items[:] = items

        if move_key and moved_items:
            move_target_block = blocks_by_name.get(move_target)
            if not move_target_block:
                move_target_block = Block(Heading(move_target, 1), [])
                blocks.append(move_target_block)
            move_target_block.items.extend(moved_items)

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


