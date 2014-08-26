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

"""Handling of HTTP cookies."""

from PyQt5.QtNetwork import QNetworkCookie, QNetworkCookieJar
from PyQt5.QtCore import QStandardPaths, QDateTime

from qutebrowser.config import config, lineparser
from qutebrowser.utils import misc as utils


class CookieJar(QNetworkCookieJar):

    """Our own cookie jar to save cookies to disk if desired."""

    def __init__(self, parent=None):
        super().__init__(parent)
        datadir = utils.get_standard_dir(QStandardPaths.DataLocation)
        self._linecp = lineparser.LineConfigParser(datadir, 'cookies')
        cookies = []
        for line in self._linecp:
            cookies += QNetworkCookie.parseCookies(line.encode('utf-8'))
        self.setAllCookies(cookies)

    def purge_old_cookies(self):
        """Purge expired cookies from the cookie jar."""
        # Based on:
        # http://qt-project.org/doc/qt-5/qtwebkitexamples-webkitwidgets-browser-cookiejar-cpp.html
        now = QDateTime.currentDateTime()
        cookies = [c for c in self.allCookies()
                   if c.isSessionCookie() or c.expirationDate() >= now]
        self.setAllCookies(cookies)

    def setCookiesFromUrl(self, cookies, url):
        """Add the cookies in the cookies list to this cookie jar.

        Args:
            cookies: A list of QNetworkCookies.
            url: The URL to set the cookies for.

        Return:
            True if one or more cookies are set for 'url', otherwise False.
        """
        if config.get('permissions', 'cookies-accept') == 'never':
            return False
        else:
            return super().setCookiesFromUrl(cookies, url)

    def save(self):
        """Save cookies to disk."""
        if not config.get('permissions', 'cookies-store'):
            # FIXME if this changed to false we should delete the old cookies
            return
        self.purge_old_cookies()
        lines = []
        for cookie in self.allCookies():
            if not cookie.isSessionCookie():
                lines.append(bytes(cookie.toRawForm()).decode('utf-8'))
        self._linecp.data = lines
        self._linecp.save()
