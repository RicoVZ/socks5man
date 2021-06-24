from __future__ import absolute_import
import time

import pytest

from socks5man.database import Database, AlembicVersion, SCHEMA_VERSION
from socks5man.exceptions import Socks5manDatabaseError
from socks5man.misc import set_cwd
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

    def test_add_socks5(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            description="Very wow"*100
        )
        s2id = self.db.add_socks5(
            "10.8.8.8", 4242, "Germany", "DE"
        )
        s3id = self.db.add_socks5(
            "11.8.8.8", 4343, "Germany", "DE",  username="test",
            password="pass", dnsport=5050
        )
        s4id = self.db.add_socks5(
            "12.8.8.8", 4444, "Germany", "DE",  username="test",
            password="pass", operational=True
        )

        s1 = self.db.view_socks5(s1id)
        s2 = self.db.view_socks5(s2id)
        s3 = self.db.view_socks5(s3id)
        s4 = self.db.view_socks5(s4id)
        assert s1id is not None
        assert isinstance(s2id, int)
        assert s1.host == "9.8.8.8"
        assert s1.city == "Berlin"
        assert s1.description == "Very wow"*100
        assert not s1.operational
        assert s2.host == "10.8.8.8"
        assert s2.port == 4242
        assert s2.country == "Germany"
        assert s2.country_code == "DE"
        assert s3.host == "11.8.8.8"
        assert s3.username == "test"
        assert s3.password == "pass"
        assert s3.port == 4343
        assert s3.dnsport == 5050
        assert s4.host == "12.8.8.8"
        assert s4.port == 4444
        assert s4.operational

    def test_add_socks5_error(self):
        with pytest.raises(Socks5manDatabaseError):
            self.db.add_socks5(
                "8.8.8.8", 7121, "Germany", "DE", operational="veryboolean"
            )

    def test_add_socks5_invalid_country(self):
        with pytest.raises(Socks5manDatabaseError):
            self.db.add_socks5(
                "8.8.8.8", 7121, None, "DE"
            )
    def test_add_socks5_invalid_country_code(self):
        with pytest.raises(Socks5manDatabaseError):
            self.db.add_socks5(
                "8.8.8.8", 7121, "Germany", None
            )
    def test_add_socks5_invalid_host(self):
        with pytest.raises(Socks5manDatabaseError):
            self.db.add_socks5(
                None, 7121, "Germany", "DE"
            )
    def test_add_socks5_invalid_port(self):
        with pytest.raises(Socks5manDatabaseError):
            self.db.add_socks5(
                "8.8.8.8", None, "Germany", "DE"
            )

    def test_repr(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            description="Very wow Very wow"
        )
        s2id = self.db.add_socks5(
            "12.8.8.8", 4444, "Germany", "DE",  username="test",
            password="pass", operational=True
        )
        s = self.db.view_socks5(s1id)
        s2 = self.db.view_socks5(s2id)
        assert repr(
            s) == "<Socks5(host=9.8.8.8, port=4141, country=Germany, authenticated=False, description=Very wow Very wow)>"
        assert repr(
            s2) == "<Socks5(host=12.8.8.8, port=4444, country=Germany, authenticated=True, description=None)>"

    def test_remove_socks5(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            description="Very wow" * 100
        )
        assert self.db.view_socks5(id1).id == id1
        self.db.remove_socks5(id1)
        assert self.db.view_socks5(id1) is None

    def test_list_socks5_operational(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(operational=True)
        assert len(res) == 1
        assert res[0].id == s2id

        res = self.db.list_socks5(operational=False)
        assert len(res) == 1
        assert res[0].id == s1id

        res = self.db.list_socks5()
        assert len(res) == 2

    def test_list_socks5_country(self):
        self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(country="france")
        assert len(res) == 1
        assert res[0].id == s2id

        res = self.db.list_socks5(country="FranCE")
        assert len(res) == 1
        assert res[0].id == s2id

    def test_list_socks5_country_code(self):
        self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(country_code="fr")
        assert len(res) == 1
        assert res[0].id == s2id

        res = self.db.list_socks5(country_code="FR")
        assert len(res) == 1
        assert res[0].id == s2id

    def test_list_socks5_city(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        s3id = self.db.add_socks5(
            "9.10.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(city="berlin")
        assert len(res) == 1
        assert res[0].id == s1id

        res = self.db.list_socks5(city="paris")
        assert len(res) == 2
        assert res[0].id == s2id
        assert res[1].id == s3id

    def test_list_socks5_host(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        self.db.add_socks5(
            "9.10.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(host="9.8.8.8")
        assert len(res) == 2
        assert res[0].id == s1id
        assert res[1].id == s2id

        res = self.db.list_socks5(host="1.2.3.4")
        assert len(res) == 0

    def test_list_socks5_host_listarg(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        s3id = self.db.add_socks5(
            "9.10.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        self.db.add_socks5(
            "10.10.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )

        res = self.db.list_socks5(host=["9.8.8.8", "9.10.8.8"])
        assert len(res) == 3
        assert res[0].id == s1id
        assert res[1].id == s2id
        assert res[2].id == s3id

    def test_view_socks5(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        assert self.db.view_socks5(s1id).host == "9.8.8.8"
        assert self.db.view_socks5(2) is None
        assert self.db.view_socks5(host="9.8.8.8", port=4141).host == "9.8.8.8"

        with pytest.raises(Socks5manDatabaseError):
            self.db.view_socks5(host="9.8.8.8")
        with pytest.raises(Socks5manDatabaseError):
            self.db.view_socks5(port=4141)
        with pytest.raises(Socks5manDatabaseError):
            self.db.view_socks5()

    def test_find_socks5(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        s3id = self.db.add_socks5(
            "9.8.8.8", 4241, "France", "FR", city="Paris",
            operational=True
        )
        assert self.db.find_socks5()[0].id == s2id
        assert self.db.find_socks5()[0].id == s3id
        assert self.db.find_socks5()[0].id == s2id
        assert len(self.db.find_socks5(limit=1000)) == 2

    def test_find_socks5_no_usage_update(self):
        s1id = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=False
        )
        s2id = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=True
        )
        s3id = self.db.add_socks5(
            "9.8.8.8", 4241, "France", "FR", city="Paris",
            operational=True
        )
        assert self.db.find_socks5(update_usage=False)[0].id == s2id
        assert self.db.find_socks5(update_usage=False)[0].id == s2id
        assert self.db.find_socks5(update_usage=False)[0].id == s2id
        assert len(self.db.find_socks5(limit=1000)) == 2

    def test_find_socks5_country(self):
        self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "Belgium", "BE", operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=False
        )
        res = self.db.find_socks5(country="germany")
        assert len(res) == 1
        assert res[0].country == "Germany"
        assert len(self.db.find_socks5(country="france")) == 0

    def test_find_socks5_country_code(self):
        self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "Belgium", "BE", operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", city="Paris",
            operational=False
        )
        res = self.db.find_socks5(country_code="de")
        assert len(res) == 1
        assert res[0].country == "Germany"
        assert len(self.db.find_socks5(country="fr")) == 0

    def test_find_socks5_city(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=True
        )
        id2 = self.db.add_socks5(
            "10.8.8.8", 4141, "Germany", "DE", city="Berlin",
            operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "Belgium", "BE", operational=True
        )
        self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", operational=True, city="Paris"
        )

        assert self.db.find_socks5(city="berlin")[0].id == id1
        assert self.db.find_socks5(city="berlin")[0].id == id2
        assert self.db.find_socks5(city="berlin")[0].id == id1
        assert len(self.db.find_socks5(city="amsterdam")) == 0

    def test_find_socks5_mbpsdown(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE",
            operational=True
        )
        id2 = self.db.add_socks5(
            "10.8.8.8", 4141, "Germany", "DE",
            operational=True
        )
        id3 = self.db.add_socks5(
            "9.8.8.8", 4141, "Belgium", "BE", operational=True
        )
        id4 = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", operational=True
        )

        self.db.set_approx_bandwidth(id1, 10.1)
        self.db.set_approx_bandwidth(id2, 32.183)
        self.db.set_approx_bandwidth(id3, 0.148)

        assert self.db.find_socks5(min_mbps_down=15.7)[0].id == id2
        assert self.db.find_socks5(min_mbps_down=10)[0].id == id1
        assert self.db.find_socks5(min_mbps_down=10)[0].id == id2
        assert self.db.find_socks5(min_mbps_down=40) == []

    def test_find_socks5_conntime(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE",
            operational=True
        )
        id2 = self.db.add_socks5(
            "10.8.8.8", 4141, "Germany", "DE",
            operational=True
        )
        id3 = self.db.add_socks5(
            "9.8.8.8", 4141, "Belgium", "BE", operational=True
        )
        id4 = self.db.add_socks5(
            "9.8.8.8", 4141, "France", "FR", operational=True
        )

        self.db.set_connect_time(id1, 0.53)
        self.db.set_connect_time(id2, 0.043)
        self.db.set_connect_time(id3, 0.44)

        assert self.db.find_socks5(max_connect_time=0.5)[0].id == id2
        assert self.db.find_socks5(max_connect_time=0.5)[0].id == id3
        assert self.db.find_socks5(max_connect_time=0.5)[0].id == id2
        assert self.db.find_socks5(max_connect_time=0.001) == []

    def test_bulk_add(self):
        s = [
            {
                "host": "8.8.8.8",
                "port": 4242,
                "country": "ads",
                "country_code": "ad"
            },
            {
                "host": "example.com",
                "port": 9133,
                "country": "ads",
                "country_code": "ad"
            }
        ]
        assert len(self.db.list_socks5()) == 0
        self.db.bulk_add_socks5(s)
        assert len(self.db.list_socks5()) == 2

    def test_bulk_add_missing_fields(self):
        s = [
            {
                "host": "8.8.8.8",
                "port": 4242,
                "country": "ads"
            },
            {
                "host": "example.com",
                "port": 9133,
                "country": "ads",
                "country_code": "ad"
            }
        ]
        with pytest.raises(Socks5manDatabaseError):
            self.db.bulk_add_socks5(s)

    def test_set_operational(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE",
            operational=False
        )
        assert not self.db.view_socks5(id1).operational
        self.db.set_operational(id1, True)
        s2 = self.db.view_socks5(id1)
        assert s2.operational
        time.sleep(0.01)
        self.db.set_operational(id1, False)
        s3 = self.db.view_socks5(id1)
        assert not s3.operational
        assert s3.last_check > s2.last_check

    def test_set_operational_nonexist(self):
        # Should not raise exception
        self.db.set_operational(8127313, True)

    def test_set_connect_time(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE",
            operational=False
        )
        assert self.db.view_socks5(id1).connect_time is None
        self.db.set_connect_time(id1, 0.5)
        assert self.db.view_socks5(id1).connect_time == 0.5

    def test_set_bandwidth(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4141, "Germany", "DE",
            operational=False
        )
        assert self.db.view_socks5(id1).bandwidth is None
        self.db.set_approx_bandwidth(id1, 10.24)
        assert self.db.view_socks5(id1).bandwidth == 10.24

    def test_delete(self):
        for x in range(25):
            self.db.add_socks5(
                "9.8.8.8", x, "Germany", "DE",
                operational=False
            )
        assert len(self.db.list_socks5()) == 25
        self.db.delete_all_socks5()
        assert len(self.db.list_socks5()) == 0

    def test_bulk_delete_socks5(self):
        ids = []
        for x in range(25):
            i = self.db.add_socks5(
                "9.8.8.8", x, "Germany", "DE",
                operational=False
            )
            if x <= 12:
                ids.append(i)
        assert len(self.db.list_socks5()) == 25
        self.db.bulk_delete_socks5(ids)
        assert len(self.db.list_socks5()) == 12
        for i in ids:
            assert self.db.view_socks5(socks5_id=i) is None

    def test_big_bulk_delete(self):
        bulk_socks = [{
            "host": "8.8.8.8",
            "port": 4242,
            "country": "Germany",
            "country_code": "DE"
        } for x in range(2000)]

        self.db.bulk_add_socks5(bulk_socks)
        id1 = self.db.add_socks5(
            "9.8.8.8", 4242, "Germany", "DE",
            operational=True
        )
        assert len(self.db.list_socks5()) == 2001
        self.db.bulk_delete_socks5(
            [s.id for s in self.db.list_socks5(operational=False)]
        )
        workingsocks = self.db.list_socks5()
        assert len(workingsocks) == 1
        assert workingsocks[0].operational

    def test_update_geoinfo(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4242, "Germany", "DE",
            operational=False
        )
        id2 = self.db.add_socks5(
            "9.8.8.8", 4243, "Germany", "DE",
            operational=False
        )
        s = self.db.view_socks5(id1)
        assert s.country == "Germany"
        assert s.city is None
        assert s.country_code == "DE"
        self.db.update_geoinfo(
            id1, country="France", country_code="FR", city="Paris"
        )
        s2 = self.db.view_socks5(id1)
        assert s2.country == "France"
        assert s2.city == "Paris"
        assert s2.country_code == "FR"
        s3 = self.db.view_socks5(id2)
        assert s3.country == "Germany"
        assert s3.city is None
        assert s3.country_code == "DE"

    def test_update_geoninfo_invalid_country(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4242, "Germany", "DE",
            operational=False
        )
        with pytest.raises(Socks5manDatabaseError):
            self.db.update_geoinfo(
                id1, country=None, country_code="FR", city="Paris"
            )

    def test_update_geoninfo_invalid_country_code(self):
        id1 = self.db.add_socks5(
            "9.8.8.8", 4242, "Germany", "DE",
            operational=False
        )
        with pytest.raises(Socks5manDatabaseError):
            self.db.update_geoinfo(
                id1, country="France", country_code=None, city="Paris"
            )

    def test_schema_latest_version(self):
        ses = self.db.Session()
        try:
            v = ses.query(AlembicVersion.version_num).first()
            assert v.version_num == SCHEMA_VERSION
        finally:
            ses.close()

    def test_db_migratable_true(self):
        ses = self.db.Session()
        try:
            v = ses.query(AlembicVersion).first()
            v.version_num = "sdfsdfsf"
            ses.add(v)
            ses.commit()
        finally:
            ses.close()

        assert self.db.db_migratable()

    def test_db_migratable_false(self):
        assert not self.db.db_migratable()


