from __future__ import absolute_import
import datetime
import pytest

from socks5man.database import Database
from socks5man.exceptions import Socks5CreationError
from socks5man.manager import Manager
from socks5man.misc import set_cwd, create_cwd, cwd
from socks5man.socks5 import Socks5

from tests.helpers import CleanedTempFile
from six.moves import range

class TestManager(object):

    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def setup(self):
        set_cwd(self.tempfile.mkdtemp())
        self.db = Database()
        self.db.connect(create=True)

    def test_acquire(self):
        past = datetime.datetime.now()
        for c in ["United States", "China", "Germany"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, c, "Unknown",
                city="Unknown", operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        m = Manager()
        socks5_1 = m.acquire()
        socks5_2 = m.acquire()
        socks5_3 = m.acquire()
        socks5_4 = m.acquire()
        assert socks5_1.id == 1
        assert socks5_1.last_use > past
        assert socks5_2.id == 2
        assert socks5_2.last_use > past
        assert socks5_3.id == 3
        assert socks5_3.last_use > past
        assert socks5_4.id == 1
        assert socks5_4.last_use > socks5_1.last_use

    def test_acquire_country(self):
        for c in ["United States", "China", "Germany"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, c, "Unknown",
                city="Unknown", operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        m = Manager()
        socks5_1 = m.acquire(country="germany")
        assert socks5_1.id == 3
        assert socks5_1.country == "Germany"
        socks5_2 = m.acquire(country="france")
        assert socks5_2 is None

    def test_acquire_no_operational(self):
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "Unknown",
            city="Unknown", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        self.db.add_socks5(
            "8.8.8.8", 1337, "china", "Unknown",
            city="Unknown", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        m = Manager()
        socks5_1 = m.acquire()
        assert socks5_1 is None
        socks5_2 = m.acquire(country="china")
        assert socks5_2 is None

        self.db.add_socks5(
            "8.8.8.8", 1337, "france", "Unknown",
            city="Unknown", operational=True, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        socks5_3 = m.acquire()
        assert socks5_3.id == 3

    def test_acquire_city(self):
        for c in ["Dogedown", "Amsterdam", "Tallinn"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, "Unknown", "Unknown",
                city=c, operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        m = Manager()
        socks5_1 = m.acquire(city="tallinn")
        assert socks5_1.id == 3
        assert socks5_1.city == "Tallinn"
        socks5_2 = m.acquire(city="Nowhere")
        assert socks5_2 is None

    def test_acquire_countrycode(self):
        for c in ["DE", "CA", "NL"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, "Unknown", c,
                city="Unknown", operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        m = Manager()
        socks5_1 = m.acquire(country_code="ca")
        assert socks5_1.id == 2
        assert socks5_1.country_code == "CA"
        socks5_2 = m.acquire(country_code="FR")
        assert socks5_2 is None

    def test_acquire_mbps(self):
        for c in ["DE", "CA", "NL", "NL", "PL"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, "Unknown", c,
                city="Unknown", operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        self.db.set_approx_bandwidth(2, 5.33)
        self.db.set_approx_bandwidth(3, 19.811)
        self.db.set_approx_bandwidth(4, 7.134)
        self.db.set_approx_bandwidth(5, 28.134)

        m = Manager()
        socks5_1 = m.acquire(min_mbps_down=4)
        socks5_2 = m.acquire(min_mbps_down=4, country_code="nl")
        socks5_3 = m.acquire(min_mbps_down=1, country_code="de")
        assert socks5_1.id == 5
        assert socks5_2.id == 3
        assert socks5_3 is None

    def test_acquire_conntime(self):
        for c in ["DE", "CA", "NL", "NL", "PL"]:
            self.db.add_socks5(
                "8.8.8.8", 1337, "Unknown", c,
                city="Unknown", operational=True, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        self.db.set_connect_time(2, 0.02)
        self.db.set_connect_time(3, 0.1)
        self.db.set_connect_time(4, 0.0054)
        self.db.set_connect_time(5, 1.3)

        m = Manager()
        socks5_1 = m.acquire(max_connect_time=0.01)
        socks5_2 = m.acquire(max_connect_time=0.2, country_code="nl")
        socks5_3 = m.acquire(max_connect_time=0.5, country_code="pl")
        socks5_4 = m.acquire(max_connect_time=0.0001)
        assert socks5_1.id == 4
        assert socks5_2.id == 3
        assert socks5_3 is None
        assert socks5_4 is None

    def test_add(self):
        create_cwd(path=cwd())
        m = Manager()
        res = m.add("8.8.8.8", 1337, description="Many wow")
        assert res.id == 1
        assert res.host == "8.8.8.8"
        assert res.port == 1337
        assert res.country == "United States"
        assert res.country_code == "US"
        assert res.username is None
        assert res.password is None
        all_socks = self.db.list_socks5()
        assert len(all_socks) == 1
        assert all_socks[0].id == 1
        assert all_socks[0].host == "8.8.8.8"
        assert all_socks[0].port == 1337
        assert all_socks[0].username is None
        assert all_socks[0].password is None
        assert all_socks[0].country == "United States"
        assert all_socks[0].country_code == "US"

    def test_add_description(self):
        create_cwd(path=cwd())
        m = Manager()
        res = m.add("8.8.8.8", 1337, description="Many wow")
        assert res.id == 1
        assert res.host == "8.8.8.8"
        assert res.port == 1337
        all_socks = self.db.list_socks5()
        assert len(all_socks) == 1
        assert all_socks[0].id == 1
        assert all_socks[0].host == "8.8.8.8"
        assert all_socks[0].port == 1337
        assert all_socks[0].description == "Many wow"

    def test_add_invalid_entry(self):
        create_cwd(path=cwd())
        m = Manager()
        with pytest.raises(Socks5CreationError):
            m.add("u8a8asd8a8sdad.cheese", -9812381, description="Many wow")

    def test_add_hostname(self):
        create_cwd(path=cwd())
        m = Manager()
        res = m.add("example.com", 1337)
        assert res.id == 1
        assert res.country == "United States"
        assert res.country_code == "US"
        assert res.city == "Norwell"
        assert res.host == "example.com"
        assert res.port == 1337
        all_socks = self.db.list_socks5()
        assert len(all_socks) == 1
        assert all_socks[0].host == "example.com"
        assert all_socks[0].port == 1337
        assert all_socks[0].country == "United States"
        assert all_socks[0].country_code == "US"

    def test_add_invalid_auth_usage(self):
        create_cwd(path=cwd())
        m = Manager()
        with pytest.raises(Socks5CreationError):
            m.add("example.com", 1337, username="Hello")
        with pytest.raises(Socks5CreationError):
            m.add("example.com", 1337, password="Hello")

    def test_add_auth(self):
        create_cwd(path=cwd())
        m = Manager()
        res = m.add("example.com", 1337, username="Hello", password="Bye")
        assert res.id == 1
        all_socks = self.db.list_socks5()
        assert len(all_socks) == 1
        assert all_socks[0].host == "example.com"
        assert all_socks[0].port == 1337
        assert all_socks[0].username == "Hello"
        assert all_socks[0].password == "Bye"

    def test_add_dnsport(self):
        create_cwd(path=cwd())
        m = Manager()
        res = m.add("example.com", 1337, dnsport=5050)
        assert res.id == 1
        all_socks = self.db.list_socks5()
        assert len(all_socks) == 1
        assert all_socks[0].dnsport == 5050
        assert all_socks[0].host == "example.com"
        assert all_socks[0].port == 1337

    def test_add_duplicate(self):
        create_cwd(path=cwd())
        m = Manager()
        m.add("example.com", 1337)
        with pytest.raises(Socks5CreationError):
            m.add("example.com", 1337)

    def test_bulk_add(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "8.8.8.8",
                "port": 4242
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 2
        allsocks = self.db.list_socks5()
        assert len(allsocks) == 2
        assert allsocks[0].country == "United States"
        assert allsocks[1].country == "United States"

    def test_bulk_add_missinginfo(self):
        create_cwd(path=cwd())
        servers = [
            {
                "port": 4242
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 1

    def test_bulk_add_faultyinfo(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "98asdj9a8sdj9adsuiuiuiasd.cheese",
                "port": 4242
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 1

    def test_bulk_add_invalid_auth_usage(self):
        create_cwd(path=cwd())
        m = Manager()
        servers1 = [
            {
                "host": "8.8.8.8",
                "port": 4242,
                "password": "suchsecure"
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        servers2 = [
            {
                "host": "8.8.8.8",
                "port": 4242
            },
            {
                "host": "example.com",
                "username": "doge",
                "port": 9133
            }
        ]

        t1 = m.bulk_add(servers1)
        t2 = m.bulk_add(servers2)
        assert t1 == 1
        assert t2 == 1

    def test_bulk_add_strport(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "8.8.8.8",
                "port": "4242"
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 2
        assert self.db.view_socks5(host="8.8.8.8", port=4242).port == 4242

    def test_bulk_add_description(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "8.8.8.8",
                "port": 4242
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers, description="Very wow") == 2
        s = self.db.view_socks5(host="8.8.8.8", port=4242)
        assert s.port == 4242
        assert s.description == "Very wow"

    def test_bulk_add_auth(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "8.8.8.8",
                "port": 4242,
                "username": "hello",
                "password": "bye"
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 2
        allsocks = self.db.list_socks5()
        assert allsocks[0].username == "hello"
        assert allsocks[0].password == "bye"

    def test_bulk_dnsport(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "8.8.8.8",
                "port": 4242,
                "dnsport": 5050
            },
            {
                "host": "example.com",
                "port": 9133
            }
        ]
        m = Manager()
        assert m.bulk_add(servers) == 2
        allsocks = self.db.list_socks5()
        assert allsocks[0].dnsport == 5050

    def test_bulk_add_nonew(self):
        create_cwd(path=cwd())
        servers = [
            {
                "host": "Shouldnotexistsstuff789as7h8asdj8asd.tosti",
                "port": 4242
            },
            {
                "host": "example.com",
                "port": None
            }
        ]
        m = Manager()
        with pytest.raises(Socks5CreationError):
            m.bulk_add(servers)

    def test_delete_socks5(self):
        self.db.add_socks5(
            "8.8.8.8", 1337, "germany", "Unknown",
            city="Unknown", operational=False, username="doge",
            password="wow", description="Such wow, many socks5"
        )
        assert self.db.view_socks5(1).id == 1
        m = Manager()
        m.delete(1)
        assert self.db.view_socks5(1) is None

    def test_delete_all(self):
        for x in range(10):
            self.db.add_socks5(
                "8.8.8.8", x, "germany", "Unknown",
                city="Unknown", operational=False, username="doge",
                password="wow", description="Such wow, many socks5"
            )

        assert len(self.db.list_socks5()) == 10
        m = Manager()
        m.delete_all()
        assert len(self.db.list_socks5()) == 0

    def test_list_socks5(self):
        for x in range(10):
            self.db.add_socks5(
                "8.8.8.8", x, "germany", "Unknown",
                city="Unknown", operational=False, username="doge",
                password="wow", description="Such wow, many socks5"
            )
        m = Manager()
        all_socks = m.list_socks5()
        assert len(all_socks) == 10
        for s in all_socks:
            assert isinstance(s, Socks5)

    def test_list_socks5_description(self):
        for x in range(3):
            self.db.add_socks5(
                "8.8.8.8", x, "germany", "Unknown",
                city="Unknown", operational=False, username="doge",
                password="wow", description="google dns"
            )
        for x in range(3):
            self.db.add_socks5(
                "1.1.1.1", x, "germany", "Unknown",
                city="Unknown", operational=False, username="doge",
                password="wow", description="cloudflare dns"
            )
        m = Manager()
        all_socks = m.list_socks5(description="google dns")
        assert len(all_socks) == 3
        for s in all_socks:
            assert isinstance(s, Socks5)

        all_socks = m.list_socks5(description="cloudflare dns")
        assert len(all_socks) == 3
        for s in all_socks:
            assert isinstance(s, Socks5)
