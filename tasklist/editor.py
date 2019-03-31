import urwid

from .types import Item, Heading


class HasState:

    signals = ["change", "postchange"]
    states = {}
    default_state = None
    change_to_same_state = False

    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = state if state is not None else self.default_state
        self.set_state(state)

    @property
    def state(self):
        return self._state

    def set_state(self, state, do_callback=True):
        if self._state == state and not self.change_to_same_state:
            return

        assert state in self.states, "{!r} invalid state: {!r}".format(self, state)

        old_state = self._state
        if do_callback and old_state is not None:
            self._emit('change', state)
        self._state = state

        self.set_state_text(self.states[state])
        self._invalidate()

        if do_callback and old_state is not None:
            self._emit('postchange', old_state)

    def set_state_text(self, state_data):
        raise NotImplementedError


class CheckBox(HasState, urwid.Text):

    states = {
        True: '[x]',
        False: '',
    }
    default_state = False

    def __init__(self, *args, **kwargs):
        super().__init__('', *args, **kwargs)

    def set_state_text(self, state_data):
        self.set_text(state_data)

    def toggle_state(self):
        self.set_state(not self._state)


class PriorityLabel(HasState, urwid.Text):

    states = {
        'a': '(a)',
        'b': '(b)',
        'c': '(c)',
        '': '',
    }
    default_state = ''
    change_to_same_state = True

    def __init__(self, *args, **kwargs):
        super().__init__('', *args, **kwargs)

    def set_state_text(self, state_data):
        self.set_text(state_data)


class LostFocusMonitor:

    """Container mixin to make child widgets emit lost_focus when losing focus.

    All the containers in the hierarchy should inherit this, otherwise
    lost_focus will be emitted only in some cases.

    Child widgets must declare they emit lost_focus; see EmitsLostFocus.

    Warning: This uses a private method of the container class, so it might
    break at any time, or have unintended consequences. Known to work with
    Pile and Column containers, no guarantees about others.

    """

    # Assumes parent does the following in constructor:
    # self._contents.set_focus_changed_callback(lambda f: self._invalidate())

    def __init__(self, *args, **kwargs):
        self._old_focus_position = None
        super().__init__(*args, **kwargs)

    def _invalidate(self):
        super()._invalidate()

        # self.focus_position raises IndexError if there's no contents.
        if not self.contents:
            return

        if self._old_focus_position != self.focus_position:
            self._old_focus_position = self.focus_position

            # Only the last, non-container widget emits lost_focus.
            widget = self
            while hasattr(widget, 'contents'):

                # We ignore when containers disappear.
                # Not sure this is entirely correct.
                try:
                    widget_options = widget.contents[widget.focus_position]
                except IndexError:
                    return
                widget, _ = widget_options

            urwid.emit_signal(widget, 'lost_focus')


class EmitsLostFocus:

    """Widgets expecting to emit lost_focus should inherit this."""

    signals = ['lost_focus']


class Disableable:

    """Mixin to make widgets selectable by setting widget.enabled."""

    def __init__(self, *args, enabled=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.enabled = enabled

    def selectable(self):
        return self.enabled


class OnEnter:

    """Mixin to make a widget do something on enter."""

    def __init__(self, *args, on_enter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.on_enter = on_enter

    def keypress(self, size, key):
        if key == 'enter':
            (self.on_enter or (lambda: None))()
            return None
        return super().keypress(size, key)


class FancyCheckBoxEdit(OnEnter, EmitsLostFocus, Disableable, urwid.Edit): pass


class FancyCheckBox(LostFocusMonitor, urwid.Columns):

    def sizing(self):
        return frozenset([urwid.FLOW])

    def __init__(self, priority='', state=False, label=''):
        self.bullet = urwid.SelectableIcon('-', 0)
        self.priority = PriorityLabel(state=priority)
        self.checkbox = CheckBox(state=state)
        self.label = FancyCheckBoxEdit('', label, enabled=False)
        super().__init__([
            ('pack', self.bullet),
            ('pack', self.checkbox),
            ('pack', self.priority),
            self.label,
        ], dividechars=1)

        def disable_label():
            self.label.enabled = False
            self.focus_position = 0

        urwid.connect_signal(self.label, 'lost_focus', disable_label)
        self.label.on_enter = disable_label

    def keypress(self, size, key):
        if not super().keypress(size, key):
            return None

        if key == 'x':
            self.checkbox.toggle_state()
            self._invalidate()
            return None

        if key == 'e':
            self.label.enabled = True
            self.focus_position = 3
            return None

        if key in 'abcd':
            self.priority.set_state({
                'a': 'a',
                'b': 'b',
                'c': 'c',
                'd': '',
            }[key])
            self._invalidate()
            return None

        return key


class CheckBoxList(LostFocusMonitor, urwid.Pile):

    def __init__(self, *args, move_key=None, move_target=None, **kwargs):
        super().__init__(*args, **kwargs)
        assert (move_key is None) + (move_target is None) != 1, (
            "either none or both of move_key and move_target must be given")
        self.move_key = move_key
        self.move_target = move_target


    # So we still have focus when there's no child element.
    def selectable(self):
        return True

    def _contents_modified(self, slc, new_items):
        super()._contents_modified(slc, new_items)

        def focus_on_the_next_element(_, __):
            if self.focus_position < len(self.contents) - 1:
                self.focus_position += 1

        for widget, _ in new_items:
            urwid.connect_signal(widget.priority, 'change', focus_on_the_next_element)

    def keypress(self, size, key):
        if not super().keypress(size, key):
            return None

        # TODO: Emit signals for added/removed items?

        if key == 'n':
            checkbox = FancyCheckBox()
            self.contents.append((checkbox, ('weight', 1)))
            self.focus_position = len(self.contents) - 1
            checkbox.keypress((100, ), 'e')
            return None

        if key == 'r':
            if self.contents:
                del self.contents[self.focus_position]
                if self.contents and self.focus_position > len(self.contents):
                    self.focus_position = len(self.contents) - 1
            return None

        if self.move_key and key == self.move_key:
            if self.contents:
                self.move_target.append(self.contents[self.focus_position])
                del self.contents[self.focus_position]
                if self.contents and self.focus_position > len(self.contents):
                    self.focus_position = len(self.contents) - 1
            return None

        return key


def edit(items, heading, move_key=None):
    move_target = []

    checkboxlist = CheckBoxList(
        [
            FancyCheckBox(
                state=item.checked,
                priority=item.priority,
                label=item.text,
            )
            for item in items
        ],
        move_key=move_key,
        move_target=move_target if move_key else None,
    )

    pile = urwid.Pile([
        urwid.Text('{} {}\n'.format('#' * heading.level, heading.text)),
        checkboxlist,
    ])

    fill = urwid.Filler(pile, 'top')

    def exit_on_q(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(fill, unhandled_input=exit_on_q)
    loop.run()

    def fancy_check_box_list_to_items(l):
        return [
            Item(fcb.label.get_edit_text(), fcb.checkbox.state, fcb.priority.state)
            for fcb, _ in l
        ]

    return (
        fancy_check_box_list_to_items(checkboxlist.contents),
        fancy_check_box_list_to_items(move_target),
    )



if __name__ == '__main__':

    from jinja2.utils import generate_lorem_ipsum

    items = [
        Item(generate_lorem_ipsum(n=1, html=False, min=1, max=9), False, '')
        for _ in range(20)
    ]
    items = edit(items, Heading('Lorem Ipsum', 1))
    for i in items:
        print(i)


