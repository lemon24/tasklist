import urwid


class HasState:

    signals = ["change", "postchange"]
    states = {}
    change_to_same_state = False

    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = None
        self.set_state(state)

    def set_state(self, state, do_callback=True):
        if self._state == state and not self.change_to_same_state:
            return

        assert state in self.states, "{!r} invalid state: {!r}".format(self, state)

        old_state = self._state
        if do_callback and old_state is not None:
            self._emit('change', state)
        self._state = state

        self.set_state_text(self.states[state])

        if do_callback and old_state is not None:
            self._emit('postchange', old_state)

    def set_state_text(self, state_data):
        raise NotImplementedError


class CheckBox(HasState, urwid.SelectableIcon):

    """Minimal version of urwid.CheckBox (no label, no mixed state)."""

    states = {
        True: ("[x]", 1),
        False: ("[ ]", 1),
    }

    def __init__(self, state=False, **kwargs):
        super().__init__('', state=state, **kwargs)

    def set_state_text(self, state_data):
        text, cursor_position = state_data
        self.set_text(text)
        self._cursor_position = cursor_position

    def toggle_state(self):
        self.set_state(not self._state)

    def keypress(self, size, key):
        if self._command_map[key] == urwid.ACTIVATE or key == 'x':
            self.toggle_state()
            return None
        return key


class PriorityLabel(HasState, urwid.Text):

    states = {
        'high': 'a',
        'medium': 'b',
        'low': 'c',
        'none': ' ',
    }
    change_to_same_state = True

    def __init__(self, state='none', **kwargs):
        super().__init__('', state=state, **kwargs)

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
        if self._old_focus_position != self.focus_position:
            self._old_focus_position = self.focus_position

            # Only the last, non-container widget emits lost_focus.
            widget = self
            while hasattr(widget, 'contents'):
                widget = widget.contents[widget.focus_position][0]
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

    def __init__(self, priority='none', state=False, label=''):
        self.priority = PriorityLabel(priority, align='right')
        self.checkbox = CheckBox(state)
        self.label = FancyCheckBoxEdit('', label, enabled=False)
        super().__init__([
            (2, self.priority),
            (4, self.checkbox),
            self.label,
        ])

        def disable_label():
            self.label.enabled = False
            self.focus_position = 1

        urwid.connect_signal(self.label, 'lost_focus', disable_label)
        self.label.on_enter = disable_label

    def keypress(self, size, key):
        if key == 'e':
            self.label.enabled = True
            self.focus_position = 2
            return None
        if not self.label.enabled and key in 'abcd':
            self.priority.set_state({
                'a': 'high',
                'b': 'medium',
                'c': 'low',
                'd': 'none',
            }[key])
            return None
        return super().keypress(size, key)


class CheckBoxList(LostFocusMonitor, urwid.Pile):

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

        if key == 'n':
            if not any(c.label.enabled for c, _ in self.contents):
                checkbox = FancyCheckBox()
                self.contents.append((checkbox, ('weight', 1)))
                self.focus_position = len(self.contents) - 1
                checkbox.keypress(1, 'e')
            return None

        return key


if __name__ == '__main__':

    from jinja2.utils import generate_lorem_ipsum

    labels = [
        generate_lorem_ipsum(n=1, html=False, min=1, max=9)
        for _ in range(20)
    ]

    pile = CheckBoxList([FancyCheckBox(label=label) for label in labels])
    fill = urwid.Filler(pile, 'top')

    def exit_on_q(key):
        if key in ('q', 'Q'):
            raise urwid.ExitMainLoop()

    loop = urwid.MainLoop(fill, unhandled_input=exit_on_q)
    loop.run()

