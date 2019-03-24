
class Renderer:

    def render_block(self, block):
        yield '{} {}\n'.format('#' * block.heading.level, block.heading.text)
        yield '\n'
        if block.items:
            for item in block.items:
                yield '- {}{}{}\n'.format(
                    '[x] ' if item.checked else '',
                    '({}) '.format(item.priority) if item.priority else '',
                    item.text,
                )
            yield '\n'

    def render_blocks(self, blocks):
        for block in blocks:
            yield from self.render_block(block)

    def render(self, blocks, file=None):
        lines = self.render_blocks(blocks)
        if file is None:
            return lines
        for line in lines:
            file.write(line)


render = Renderer().render


