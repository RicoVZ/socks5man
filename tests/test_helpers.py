from __future__ import absolute_import
import mock
import urllib.request, urllib.error, urllib.parse

from socks5man.helpers import (
    Dictionary, is_ipv4, is_reserved_ipv4, GeoInfo, get_ipv4_hostname,
    validify_host_port, get_over_socks5, approximate_bandwidth
)
from socks5man.misc import set_cwd, create_cwd

from tests.helpers import CleanedTempFile

def test_dictionary():
    d = {
        "hello": 10,
        "stuff": False,
        "tosti": "Yes"
    }
    d2 = Dictionary(d)
    assert d2.hello == 10
    assert not d2.stuff
    assert d2.tosti == "Yes"

def test_is_reserve_ipv4():
    reserved = [
        "127.0.0.1", "192.168.0.29", "172.16.18.10", "169.254.13.3",
        "10.0.10.11", "0.0.0.9", "255.255.255.0", "192.88.99.17"
    ]
    for ip in reserved:
        assert is_reserved_ipv4(ip)

    public = [
        "8.8.8.8", "45.19.77.17", "8.8.4.4", "123.38.177.1", "192.167.1.1",
        "11.0.0.1", "1.0.0.0"
    ]
    for ip in public:
        assert not is_reserved_ipv4(ip)

    assert not is_reserved_ipv4("NoAnIPADDRessd124")

def test_is_ipv4():
    ipv4 = [
        "8.8.8.8", "45.19.77.17", "8.8.4.4", "123.38.177.1", "192.167.1.1",
        "11.0.0.1", "1.0.0.0", "127.0.0.1", "192.168.0.29", "172.16.18.10",
        "169.254.13.3", "10.0.10.11", "0.0.0.9", "255.255.255.0",
        "192.88.99.17"
    ]

    for ip in ipv4:
        assert is_ipv4(ip)

    hostnames = ["example.com", "hostname.example.com"]
    for h in hostnames:
        assert not is_ipv4(h)

    ipv6 = ["2001:db8:85a3:8d3:1319:8a2e:370", "0:0:0:0:0:0:0:1"]

    for ipv6 in ipv6:
        assert not is_ipv4(ipv6)

class TestGeoInfo(object):

    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def test_ipv4info(self):
        tmppath = self.tempfile.mkdtemp()
        set_cwd(tmppath)
        create_cwd(tmppath)

        geo = GeoInfo()
        res = geo.ipv4info("93.184.216.34")
        assert res["country"] == "United States"
        assert res["country_code"] == "US"
        assert res["city"] == "Norwell"

    def test_ipv4info_unknown(self):
        tmppath = self.tempfile.mkdtemp()
        set_cwd(tmppath)
        create_cwd(tmppath)

        geo = GeoInfo()
        res = geo.ipv4info("10.0.0.5")
        assert res["country"] == "unknown"
        assert res["country_code"] == "unknown"
        assert res["city"] == "unknown"

    def test_ipv4info_invalid(self):
        tmppath = self.tempfile.mkdtemp()
        set_cwd(tmppath)
        create_cwd(tmppath)

        geo = GeoInfo()
        res = geo.ipv4info("8adna87dasd87asd")
        assert res["country"] == "unknown"
        assert res["country_code"] == "unknown"
        assert res["city"] == "unknown"

def test_get_ipv4_hostname():
    ip = get_ipv4_hostname("example.com")
    assert ip == "93.184.216.34"

def test_get_ipv4_hostname_invalid():
    ip = get_ipv4_hostname("nonexisting.stuff.tosti")
    assert ip is None

def test_validify_host_port():
    res = validify_host_port("8.8.8.8", 4000)
    assert res.ip == "8.8.8.8"
    assert res.port == 4000
    res2 = validify_host_port("example.com", "7823")
    assert is_ipv4(res2.ip)
    assert res2.port == 7823
    # Invalid hostname
    res3 = validify_host_port("someinvalidhostanme.tosti", 4000)
    assert res3 is None
    res4 = validify_host_port("example.com", 65537)
    assert res4 is None
    res5 = validify_host_port("example.com", -10)
    assert res5 is None
    res6 = validify_host_port("example.com", "65536")
    assert res6 is None
    res7 = validify_host_port("example.com", "-1")
    assert res7 is None
    res8 = validify_host_port("example.com", "0")
    assert res8 is None
    res9 = validify_host_port("example.com", "doges")
    assert res9 is None
    res10 = validify_host_port("example.com", None)
    assert res10 is None
    res11 = validify_host_port(None, 8132)
    assert res11 is None

@mock.patch("socks5man.helpers.socket")
@mock.patch("urllib.request.urlopen")
@mock.patch("socks5man.helpers.socks")
def test_get_over_socks5(ms, mu, mss):
    mss.socket = "DOGE"
    mss._socketobject = "socket"
    httpresponse = mock.MagicMock()
    httpresponse.read.return_value = "many content, such wow"
    mu.return_value = httpresponse
    ms.socksocket = "socksocket"
    res = get_over_socks5(
        "http://example.com", "8.8.8.8", 1337, username="many",
        password="doge", timeout=10
    )
    ms.set_default_proxy.assert_called_once_with(
        ms.SOCKS5, "8.8.8.8", 1337, username="many", password="doge"
    )
    mu.assert_called_once_with("http://example.com", timeout=10)
    assert res == "many content, such wow"
    assert mss.socket == "DOGE"

@mock.patch("socks5man.helpers.socket")
@mock.patch("urllib.request.urlopen")
@mock.patch("socks5man.helpers.socks")
def test_get_over_socks5_fail(ms, mu, mss):
    mss.socket = "DOGE"
    mss._socketobject = "socket"
    httpresponse = mock.MagicMock()
    httpresponse.read.side_effect = urllib.error.URLError("Error")
    mu.return_value = httpresponse
    ms.socksocket = "socksocket"
    res = get_over_socks5(
        "http://example.com", "8.8.8.8", 1337, username="many",
        password="doge", timeout=10
    )
    assert res is None
    assert mss.socket == "DOGE"

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_8(mg, mc, mt):
    data = "A"*1000000
    mg.side_effect = data, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 2, 1, 2
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10,
        times=2
    )
    mg.assert_any_call(
        "http://example.com/1MB.bin", "8.8.8.8", 1337, username="doge",
        password="suchwow", timeout=10
    )
    assert mg.call_count == 2
    assert speed == 8

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_25_45(mg, mc, mt):
    data = "A"*1000000
    mg.side_effect = data, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 1.55, 1, 1.22
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10
    )
    assert round(speed, 2) == 25.45

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_instant(mg, mc, mt):
    data = "A"*1000000
    mg.side_effect = data, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 1, 1, 1
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10
    )
    assert speed == 8000

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_0_87(mg, mc, mt):
    data = "A"*1000000
    mg.side_effect = data, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 10.1, 1, 10.2
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10
    )
    assert round(speed, 2) == 0.87

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_maxfail(mg, mc, mt):
    data = "A"*1000000
    mg.side_effect = None, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 1, 10.1
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10
    )
    assert round(speed, 2) == 0.44

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_smallfile(mg, mc, mt):
    data = "A"*100000
    mg.side_effect = data, data
    mc.return_value = "http://example.com/1MB.bin"
    mt.side_effect = 1, 1, 1, 1
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10
    )
    assert speed == 880.0

@mock.patch("time.time")
@mock.patch("socks5man.helpers.cfg")
@mock.patch("socks5man.helpers.get_over_socks5")
def test_approximate_bandwidth_failed(mg, mc, mt):
    mg.side_effect = None, None
    mc.return_value = "http://example.com/1MB.bin"
    speed = approximate_bandwidth(
        "8.8.8.8", 1337, username="doge", password="suchwow", timeout=10,
        times=2, maxfail=1
    )
    assert speed is None

