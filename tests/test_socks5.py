from __future__ import absolute_import
import datetime
import mock
import socket
import sys

from socks5man.database import Database
from socks5man.misc import set_cwd, create_cwd, cwd
from socks5man.socks5 import Socks5

from tests.helpers import CleanedTempFile

class TestSocks5(object):
    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def setup(self):
        set_cwd(self.tempfile.mkdtemp())
        self.db = Database()
        self.db.connect(create=True)

    def test_attrs(self):
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "DE",
            city="Frankfurt", operational=True, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        self.db.set_approx_bandwidth(1, 10.55)
        self.db.set_connect_time(1, 0.07)
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)

        assert s.id == 1
        assert s.host == "8.8.8.8"
        assert s.port == 1337
        assert s.country == "germany"
        assert s.city == "Frankfurt"
        assert s.country_code == "DE"
        assert s.username == "doge"
        assert s.password == "wow"
        assert s.description == "Such wow, many socks5"
        assert s.operational
        assert s.bandwidth == 10.55
        assert s.connect_time == 0.07
        assert s.last_use is None
        assert s.last_check is None
        assert isinstance(s.added_on, datetime.datetime)

    def test_attrs_invalid(self):
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "DE",
            city="Frankfurt", operational=True, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        self.db.set_approx_bandwidth(1, 10.55)
        self.db.set_connect_time(1, 0.07)
        db_socks5 = self.db.view_socks5(1)
        db_socks5.host = ""
        db_socks5.country = ""
        db_socks5.city = ""
        db_socks5.username = ""
        db_socks5.description = ""
        s = Socks5(db_socks5)
        assert s.host is None
        assert s.country is None
        assert s.city is None
        assert s.username is None
        assert s.description is None

    @mock.patch("socks5man.socks5.get_over_socks5")
    def test_verify(self, mg):
        create_cwd(cwd())
        mg.return_value = b"8.8.8.8"
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        assert s.verify()
        mg.assert_called_once_with(
            "http://api.ipify.org", "8.8.8.8", 1337, username="doge",
            password="wow", timeout=3
        )
        db_socks5_2 = self.db.view_socks5(1)
        assert db_socks5_2.operational

    @mock.patch("socks5man.socks5.get_over_socks5")
    def test_verify_fail(self, mg):
        create_cwd(cwd())
        mg.return_value = None
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "DE",
            city="Frankfurt", operational=True, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        assert not s.verify()
        db_socks5_2 = self.db.view_socks5(1)
        assert not db_socks5_2.operational

    @mock.patch("socks5man.socks5.get_over_socks5")
    def test_verify_private(self, mg):
        create_cwd(cwd())
        mg.return_value = b"8.8.8.8"
        self.db.add_socks5(
            "192.168.0.50", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5",
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        assert s.verify()
        db_socks5_2 = self.db.view_socks5(1)
        assert db_socks5_2.operational

    @mock.patch("socks5man.socks5.get_over_socks5")
    def test_verify_hostname(self, mg):
        create_cwd(cwd())
        mg.return_value = b"93.184.216.34"
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        assert s.verify()
        db_socks5_2 = self.db.view_socks5(1)
        assert db_socks5_2.operational

    @mock.patch("socks5man.socks5.approximate_bandwidth")
    def test_approx_bandwidth(self, ma):
        create_cwd(cwd())
        ma.return_value = 15.10
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        res = s.approx_bandwidth()
        assert res == 15.10
        ma.assert_called_once_with(
            "example.com", 1337, username="doge", password="wow",
            times=2, timeout=10
        )
        db_socks5_2 = self.db.view_socks5(1)
        assert db_socks5_2.bandwidth == 15.10

    @mock.patch("socks5man.socks5.approximate_bandwidth")
    def test_approx_bandwidth_fail(self, ma):
        create_cwd(cwd())
        ma.return_value = None
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        res = s.approx_bandwidth()
        assert res == None
        db_socks5_2 = self.db.view_socks5(1)
        assert db_socks5_2.bandwidth is None

    @mock.patch("socks5man.socks5.socks")
    def test_measure_conn_time(self, ms):
        create_cwd(cwd())
        socksocket = mock.MagicMock()
        ms.socksocket.return_value = socksocket
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        res = s.measure_connection_time()

        assert isinstance(res, float)
        socksocket.set_proxy.assert_called_once_with(
            ms.SOCKS5, "example.com", 1337, username="doge", password="wow"
        )
        socksocket.settimeout.assert_called_once_with(3)
        socksocket.connect.assert_called_once_with(
            ("api.ipify.org", 80)
        )
        assert self.db.view_socks5(1).connect_time == res

    @mock.patch("socks5man.socks5.socks")
    def test_measure_conn_time_fail(self, ms):
        create_cwd(cwd())
        socksocket = mock.MagicMock()
        ms.socksocket.return_value = socksocket
        socksocket.connect.side_effect = socket.error
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        db_socks5 = self.db.view_socks5(1)
        s = Socks5(db_socks5)
        s.measure_connection_time() is None
        self.db.view_socks5(1).connect_time is None

    def test_socks5_to_dict(self):
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        s = self.db.view_socks5(1)
        socks5 = Socks5(s)
        d = socks5.to_dict()
        assert d["host"] == b"example.com"
        assert d["port"] == 1337
        assert d["country"] == b"germany"
        assert d["country_code"] == b"DE"
        assert d["city"] == b"Frankfurt"
        assert not d["operational"]
        assert d["username"] == b"doge"
        assert d["password"] == b"wow"
        assert d["description"] == b"Such wow, many socks5"
        assert d["added_on"] == socks5.added_on.strftime("%Y-%m-%d %H:%M:%S")

    def test_repr(self):
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        s = self.db.view_socks5(1)
        socks5 = Socks5(s)
        assert repr(socks5) == "<Socks5(host=example.com, port=1337, country=germany, authenticated=True)>"

    def test_repr_nonauth(self):
        self.db.add_socks5(
            "example.com", 1337, "germany", "DE",
            city="Frankfurt", operational=False,
            description="Such wow, many socks5"
        )
        s = self.db.view_socks5(1)
        socks5 = Socks5(s)
        assert repr(socks5) == "<Socks5(host=example.com, port=1337, country=germany, authenticated=False)>"

    def test_win_imported_win_inet_pton(self):
        if sys.platform == "win32":
            assert "win_inet_pton" in sys.modules
        else:
            assert "win_inet_pton" not in sys.modules

