# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Bridge to provide readline-like shortcuts for QLineEdits."""

from PyQt5.QtWidgets import QApplication, QLineEdit

from qutebrowser.commands import utils as cmdutils
from qutebrowser.utils import usertypes as typ


class ReadlineBridge:

    """Bridge which provides readline-like commands for the current QLineEdit.

    Attributes:
        deleted: Mapping from widgets to their last deleted text.
    """

    def __init__(self):
        self.deleted = {}

    @property
    def widget(self):
        """Get the currently active QLineEdit."""
        w = QApplication.instance().focusWidget()
        if isinstance(w, QLineEdit):
            return w
        else:
            return None

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_backward_char(self):
        """Move back a character.

        This acts like readline's backward-char.
        """
        if self.widget is None:
            return
        self.widget.cursorBackward(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_forward_char(self):
        """Move forward a character.

        This acts like readline's forward-char.
        """
        if self.widget is None:
            return
        self.widget.cursorForward(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_backward_word(self):
        """Move back to the start of the current or previous word.

        This acts like readline's backward-word.
        """
        if self.widget is None:
            return
        self.widget.cursorWordBackward(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_forward_word(self):
        """Move forward to the end of the next word.

        This acts like readline's forward-word.
        """
        if self.widget is None:
            return
        self.widget.cursorWordForward(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_beginning_of_line(self):
        """Move to the start of the line.

        This acts like readline's beginning-of-line.
        """
        if self.widget is None:
            return
        self.widget.home(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_end_of_line(self):
        """Move to the end of the line.

        This acts like readline's end-of-line.
        """
        if self.widget is None:
            return
        self.widget.end(False)

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_unix_line_discard(self):
        """Remove chars backward from the cursor to the beginning of the line.

        This acts like readline's unix-line-discard.
        """
        if self.widget is None:
            return
        self.widget.home(True)
        self.deleted[self.widget] = self.widget.selectedText()
        self.widget.del_()

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_kill_line(self):
        """Remove chars from the cursor to the end of the line.

        This acts like readline's kill-line.
        """
        if self.widget is None:
            return
        self.widget.end(True)
        self.deleted[self.widget] = self.widget.selectedText()
        self.widget.del_()

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_unix_word_rubout(self):
        """Remove chars from the cursor to the beginning of the word.

        This acts like readline's unix-word-rubout.
        """
        if self.widget is None:
            return
        self.widget.cursorWordBackward(True)
        self.deleted[self.widget] = self.widget.selectedText()
        self.widget.del_()

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_kill_word(self):
        """Remove chars from the cursor to the end of the current word.

        This acts like readline's kill-word.
        """
        if self.widget is None:
            return
        self.widget.cursorWordForward(True)
        self.deleted[self.widget] = self.widget.selectedText()
        self.widget.del_()

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_yank(self):
        """Paste the most recently deleted text.

        This acts like readline's yank.
        """
        if self.widget is None or self.widget not in self.deleted:
            return
        self.widget.insert(self.deleted[self.widget])

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_delete_char(self):
        """Delete the character after the cursor.

        This acts like readline's delete-char.
        """
        if self.widget is None:
            return
        self.widget.del_()

    @cmdutils.register(instance='rl_bridge', hide=True,
                       modes=[typ.KeyMode.command, typ.KeyMode.prompt])
    def rl_backward_delete_char(self):
        """Delete the character before the cursor.

        This acts like readline's backward-delete-char.
        """
        if self.widget is None:
            return
        self.widget.backspace()
