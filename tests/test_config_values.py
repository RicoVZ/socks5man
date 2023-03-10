from __future__ import absolute_import
import re
import socket
import urllib.request

from socks5man.config import cfg
from socks5man.misc import set_cwd, create_cwd, cwd

from tests.helpers import CleanedTempFile

class TestConfigValues(object):
    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def setup(self):
        set_cwd(self.tempfile.mkdtemp())

    def test_ip_api(self):
        """Verify that the default ip api returns an actual ip"""
        create_cwd(cwd())
        res = urllib.request.urlopen(
            cfg("operationality", "ip_api"),
            timeout=cfg("operationality", "timeout")
        )
        assert res.getcode() == 200
        assert re.match(rb"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", res.read())

    def test_measure_time_host(self):
        """Verify that the default connection measurement still accepts
         connections"""
        create_cwd(cwd())
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(cfg("connection_time", "timeout"))
        s.connect((
            cfg("connection_time", "hostname"), cfg("connection_time", "port")
        ))
        s.close()

    def test_download_url(self):
        """Verify that the url used to measure an approximate bandwidth
        is still available"""
        create_cwd(cwd())
        res = urllib.request.urlopen(
            cfg("bandwidth", "download_url"),
            timeout=cfg("bandwidth", "timeout")
        )
        assert res.getcode() == 200
        assert len(res.read()) > 0

    def test_geoipdb_hash_url(self):
        create_cwd(cwd())
        res = urllib.request.urlopen(cfg("geodb", "geodb_md5_url"))
        assert res.getcode() == 200
        assert len(res.read()) == 32
