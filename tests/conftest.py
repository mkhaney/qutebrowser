# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2014-2015 Florian Bruhin (The Compiler) <mail@qutebrowser.org>
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

"""The qutebrowser test suite contest file."""

import os
import sys
import collections
import itertools
import logging

import pytest

import stubs as stubsmod
import logfail
from qutebrowser.config import config
from qutebrowser.utils import objreg, usertypes


try:
    import pytest_capturelog as capturelog_mod
except ImportError:
    # When using pytest for pyflakes/pep8/..., the plugin won't be available
    # but conftest.py will still be loaded.
    capturelog_mod = None


@pytest.yield_fixture(scope='session', autouse=True)
def fail_on_logging():
    handler = logfail.LogFailHandler()
    logging.getLogger().addHandler(handler)
    yield
    logging.getLogger().removeHandler(handler)
    handler.close()


@pytest.fixture(scope='session')
def stubs():
    """Provide access to stub objects useful for testing."""
    return stubsmod


@pytest.fixture(scope='session')
def unicode_encode_err():
    """Provide a fake UnicodeEncodeError exception."""
    return UnicodeEncodeError('ascii',  # codec
                              '',  # object
                              0,  # start
                              2,  # end
                              'fake exception')  # reason


@pytest.fixture(scope='session')
def qnam(qapp):
    """Session-wide QNetworkAccessManager."""
    from PyQt5.QtNetwork import QNetworkAccessManager
    nam = QNetworkAccessManager()
    nam.setNetworkAccessible(QNetworkAccessManager.NotAccessible)
    return nam


@pytest.fixture
def webpage(qnam):
    """Get a new QWebPage object."""
    from PyQt5.QtWebKitWidgets import QWebPage

    page = QWebPage()
    page.networkAccessManager().deleteLater()
    page.setNetworkAccessManager(qnam)
    return page


@pytest.fixture
def webframe(webpage):
    """Convenience fixture to get a mainFrame of a QWebPage."""
    return webpage.mainFrame()


@pytest.fixture
def fake_keyevent_factory():
    """Fixture that when called will return a mock instance of a QKeyEvent."""
    from unittest import mock
    from PyQt5.QtGui import QKeyEvent

    def fake_keyevent(key, modifiers=0, text=''):
        """Generate a new fake QKeyPressEvent."""
        evtmock = mock.create_autospec(QKeyEvent, instance=True)
        evtmock.key.return_value = key
        evtmock.modifiers.return_value = modifiers
        evtmock.text.return_value = text
        return evtmock

    return fake_keyevent


def pytest_collection_modifyitems(items):
    """Automatically add a 'gui' marker to all gui-related tests.

    pytest hook called after collection has been performed, adds a marker
    named "gui" which can be used to filter gui tests from the command line.
    For example:

        py.test -m "not gui"  # run all tests except gui tests
        py.test -m "gui"  # run only gui tests

    Args:
        items: list of _pytest.main.Node items, where each item represents
               a python test that will be executed.

    Reference:
        http://pytest.org/latest/plugins.html
    """
    for item in items:
        if 'qapp' in getattr(item, 'fixturenames', ()):
            item.add_marker('gui')
            if sys.platform == 'linux' and not os.environ.get('DISPLAY', ''):
                if 'CI' in os.environ:
                    raise Exception("No display available on CI!")
                skip_marker = pytest.mark.skipif(
                    True, reason="No DISPLAY available")
                item.add_marker(skip_marker)


def _generate_cmdline_tests():
    """Generate testcases for test_split_binding."""
    # pylint: disable=invalid-name
    TestCase = collections.namedtuple('TestCase', 'cmd, valid')
    separators = [';;', ' ;; ', ';; ', ' ;;']
    invalid = ['foo', '']
    valid = ['leave-mode', 'hint all']
    # Valid command only -> valid
    for item in valid:
        yield TestCase(''.join(item), True)
    # Invalid command only -> invalid
    for item in valid:
        yield TestCase(''.join(item), True)
    # Invalid command combined with invalid command -> invalid
    for item in itertools.product(invalid, separators, invalid):
        yield TestCase(''.join(item), False)
    # Valid command combined with valid command -> valid
    for item in itertools.product(valid, separators, valid):
        yield TestCase(''.join(item), True)
    # Valid command combined with invalid command -> invalid
    for item in itertools.product(valid, separators, invalid):
        yield TestCase(''.join(item), False)
    # Invalid command combined with valid command -> invalid
    for item in itertools.product(invalid, separators, valid):
        yield TestCase(''.join(item), False)
    # Command with no_cmd_split combined with an "invalid" command -> valid
    for item in itertools.product(['bind x open'], separators, invalid):
        yield TestCase(''.join(item), True)


@pytest.fixture(params=_generate_cmdline_tests())
def cmdline_test(request):
    """Fixture which generates tests for things validating commandlines."""
    # Import qutebrowser.app so all cmdutils.register decorators get run.
    import qutebrowser.app  # pylint: disable=unused-variable
    return request.param


@pytest.yield_fixture
def config_stub(stubs):
    """Fixture which provides a fake config object."""
    stub = stubs.ConfigStub(signal=stubs.FakeSignal())
    objreg.register('config', stub)
    yield stub
    objreg.delete('config')


@pytest.yield_fixture
def default_config():
    """Fixture that provides and registers an empty default config object."""
    config_obj = config.ConfigManager(configdir=None, fname=None, relaxed=True)
    objreg.register('config', config_obj)
    yield config_obj
    objreg.delete('config')


@pytest.yield_fixture
def key_config_stub(stubs):
    """Fixture which provides a fake key config object."""
    stub = stubs.KeyConfigStub()
    objreg.register('key-config', stub)
    yield stub
    objreg.delete('key-config')


@pytest.yield_fixture
def host_blocker_stub(stubs):
    """Fixture which provides a fake host blocker object."""
    stub = stubs.HostBlockerStub()
    objreg.register('host-blocker', stub)
    yield stub
    objreg.delete('host-blocker')


def pytest_runtest_setup(item):
    """Add some custom markers."""
    if not isinstance(item, item.Function):
        return

    if item.get_marker('posix') and os.name != 'posix':
        pytest.skip("Requires a POSIX os.")
    elif item.get_marker('windows') and os.name != 'nt':
        pytest.skip("Requires Windows.")
    elif item.get_marker('linux') and not sys.platform.startswith('linux'):
        pytest.skip("Requires Linux.")
    elif item.get_marker('osx') and sys.platform != 'darwin':
        pytest.skip("Requires OS X.")
    elif item.get_marker('not_frozen') and getattr(sys, 'frozen', False):
        pytest.skip("Can't be run when frozen!")
    elif item.get_marker('frozen') and not getattr(sys, 'frozen', False):
        pytest.skip("Can only run when frozen!")


class MessageMock:

    """Helper object for message_mock.

    Attributes:
        _monkeypatch: The pytest monkeypatch fixture.
        MessageLevel: An enum with possible message levels.
        Message: A namedtuple representing a message.
        messages: A list of Message tuples.
    """

    Message = collections.namedtuple('Message', ['level', 'win_id', 'text',
                                                 'immediate'])
    MessageLevel = usertypes.enum('Level', ('error', 'info', 'warning'))

    def __init__(self, monkeypatch):
        self._monkeypatch = monkeypatch
        self.messages = []

    def _handle(self, level, win_id, text, immediately=False):
        self.messages.append(self.Message(level, win_id, text, immediately))

    def _handle_error(self, *args, **kwargs):
        self._handle(self.MessageLevel.error, *args, **kwargs)

    def _handle_info(self, *args, **kwargs):
        self._handle(self.MessageLevel.info, *args, **kwargs)

    def _handle_warning(self, *args, **kwargs):
        self._handle(self.MessageLevel.warning, *args, **kwargs)

    def getmsg(self):
        """Get the only message in self.messages.

        Raises ValueError if there are multiple or no messages.
        """
        if len(self.messages) != 1:
            raise ValueError("Got {} messages but expected a single "
                             "one.".format(len(self.messages)))
        return self.messages[0]

    def patch(self, module_path):
        """Patch message.* in the given module (as a string)."""
        self._monkeypatch.setattr(module_path + '.error', self._handle_error)
        self._monkeypatch.setattr(module_path + '.info', self._handle_info)
        self._monkeypatch.setattr(module_path + '.warning',
                                  self._handle_warning)


@pytest.fixture
def message_mock(monkeypatch):
    """Fixture to get a MessageMock."""
    return MessageMock(monkeypatch)


FakeWindow = collections.namedtuple('FakeWindow', ['registry'])


@pytest.yield_fixture
def win_registry():
    """Fixture providing a window registry for win_id 0."""
    registry = objreg.ObjectRegistry()
    window = FakeWindow(registry)
    objreg.window_registry[0] = window
    yield registry
    del objreg.window_registry[0]


@pytest.yield_fixture
def tab_registry(win_registry):
    """Fixture providing a tab registry for win_id 0."""
    registry = objreg.ObjectRegistry()
    objreg.register('tab-registry', registry, scope='window', window=0)
    yield registry
    objreg.delete('tab-registry', scope='window', window=0)


@pytest.yield_fixture(autouse=True)
def caplog_bug_workaround(request):
    """WORKAROUND for pytest-capturelog bug.

    https://bitbucket.org/memedough/pytest-capturelog/issues/7/

    This would lead to LogFailHandler failing after skipped tests as there are
    multiple CaptureLogHandlers.
    """
    yield
    if capturelog_mod is None:
        return

    root_logger = logging.getLogger()
    caplog_handlers = [h for h in root_logger.handlers
                       if isinstance(h, capturelog_mod.CaptureLogHandler)]

    for h in caplog_handlers:
        root_logger.removeHandler(h)
        h.close()
