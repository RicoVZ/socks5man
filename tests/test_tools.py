from __future__ import absolute_import
import mock
import socket

from socks5man.config import Config
from socks5man.database import Database
from socks5man.misc import set_cwd, create_cwd, cwd
from socks5man.tools import verify_all

from tests.helpers import CleanedTempFile

class TestVerifyAll(object):
    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def setup(self):
        set_cwd(self.tempfile.mkdtemp())
        self.db = Database()
        self.db.connect(create=True)

    @mock.patch("socks5man.tools.Socks5")
    def test_success(self, ms):
        create_cwd(cwd())
        socks5 = mock.MagicMock()
        socks5.host = "8.8.8.8"
        socks5.port = 4242
        ms.return_value = socks5
        self.db.add_socks5("8.8.8.8", 4242, "Germany", "DE")

        verify_all()
        socks5.verify.assert_called_once()
        socks5.measure_connection_time.assert_called_once()
        socks5.approx_bandwidth.assert_not_called()

    @mock.patch("socks5man.tools.Socks5")
    def test_fail(self, ms):
        create_cwd(cwd())
        socks5 = mock.MagicMock()
        socks5.host = "8.8.8.8"
        socks5.port = 4242
        socks5.verify.return_value = False
        ms.return_value = socks5
        self.db.add_socks5("8.8.8.8", 4242, "Germany", "DE")

        verify_all()
        socks5.verify.assert_called_once()
        socks5.measure_connection_time.assert_not_called()
        socks5.approx_bandwidth.assert_not_called()

    @mock.patch("socks5man.tools.Socks5")
    def test_bandwidth(self, ms):
        create_cwd(cwd())
        socks5 = mock.MagicMock()
        socks5.host = "8.8.8.8"
        socks5.port = 4242
        ms.return_value = socks5
        self.db.add_socks5("8.8.8.8", 4242, "Germany", "DE")
        Config._cache["bandwidth"]["enabled"] = True

        verify_all()
        socks5.verify.assert_called_once()
        socks5.measure_connection_time.assert_called_once()
        socks5.approx_bandwidth.assert_called_once()
        Config._cache["bandwidth"]["enabled"] = False

    @mock.patch("socks5man.tools.Socks5")
    def test_conntime_fail(self, ms):
        create_cwd(cwd())
        socks5 = mock.MagicMock()
        socks5.host = "8.8.8.8"
        socks5.port = 4242
        socks5.measure_connection_time.return_value = False
        ms.return_value = socks5
        self.db.add_socks5("8.8.8.8", 4242, "Germany", "DE")
        Config._cache["bandwidth"]["enabled"] = True

        verify_all()
        socks5.verify.assert_called_once()
        socks5.measure_connection_time.assert_called_once()
        socks5.approx_bandwidth.assert_not_called()
        Config._cache["bandwidth"]["enabled"] = False

    @mock.patch("socks5man.tools.urllib.request.urlopen")
    @mock.patch("socks5man.tools.Socks5")
    def test_download_verify_fail(self, ms, mu):
        create_cwd(cwd())
        socks5 = mock.MagicMock()
        socks5.host = "8.8.8.8"
        socks5.port = 4242
        ms.return_value = socks5
        mu.side_effect = socket.error
        self.db.add_socks5("8.8.8.8", 4242, "Germany", "DE")
        Config._cache["bandwidth"]["enabled"] = True

        verify_all()
        socks5.verify.assert_called_once()
        socks5.measure_connection_time.assert_called_once()
        mu.assert_called_once_with(mock.ANY, timeout=5)
        socks5.approx_bandwidth.assert_not_called()
        Config._cache["bandwidth"]["enabled"] = False
