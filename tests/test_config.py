from __future__ import absolute_import
import os
import copy
import pytest

from socks5man.config import Config, cfg, confbool
from socks5man.database import Database
from socks5man.exceptions import Socks5ConfigError
from socks5man.misc import set_cwd, create_cwd, cwd

from tests.helpers import CleanedTempFile


class TestConfig(object):

    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def setup(self):
        set_cwd(self.tempfile.mkdtemp())
        self.db = Database()
        self.db.connect(create=True)
        Config._cache = {}
        self.confbackup = copy.deepcopy(Config._conf)

    def teardown(self):
        Config._conf = self.confbackup

    def test_cfg_defaults(self):
        create_cwd(cwd())
        assert isinstance(cfg("socks5man", "verify_interval"), int)
        assert isinstance(cfg("socks5man", "bandwidth_interval"), int)
        assert isinstance(cfg("operationality", "ip_api"), (str))
        assert isinstance(cfg("operationality", "timeout"), int)
        assert isinstance(cfg("connection_time", "enabled"), bool)
        assert isinstance(cfg("connection_time", "timeout"), int)
        assert isinstance(cfg("connection_time", "hostname"), (str))
        assert isinstance(cfg("connection_time", "port"), int)
        assert isinstance(cfg("bandwidth", "enabled"), bool)
        assert isinstance(cfg("bandwidth", "download_url"), (str))
        assert isinstance(cfg("bandwidth", "times"), int)
        assert isinstance(cfg("bandwidth", "timeout"), int)
        assert isinstance(cfg("geodb", "geodb_url"), (str))
        assert isinstance(cfg("geodb", "geodb_md5_url"), (str))

    def test_cfg_values(self):
        create_cwd(cwd())
        assert cfg("socks5man", "verify_interval") == 300
        assert cfg("operationality", "ip_api") == "http://api.ipify.org"
        assert not cfg("bandwidth", "enabled")
        assert cfg("connection_time", "enabled")

    def test_cfg_invalid(self):
        create_cwd(cwd())
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "nonexistingkeystuffdogestosti")
        with pytest.raises(Socks5ConfigError):
            cfg("doges", "wut")

    def test_read_from_cache(self):
        create_cwd(cwd())
        Config._cache = {}
        assert cfg("operationality", "ip_api") == "http://api.ipify.org"
        assert "operationality" in Config._cache
        Config._cache["operationality"]["ip_api"] = "http://example.com"
        assert cfg("operationality", "ip_api") == "http://example.com"

    def test_missing_conf(self):
        create_cwd(cwd())
        os.remove(cwd("conf", "socks5man.conf"))
        Config._cache = {}
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "verify_interval")

    def test_invalid_conf(self):
        create_cwd(cwd())
        Config._cache = {}
        with open(cwd("conf", "socks5man.conf"), "w") as fw:
            fw.write("socks5man to dominate them all")
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "verify_interval")

    def test_unknown_section(self):
        create_cwd(cwd())
        Config._cache = {}
        del Config._conf["operationality"]
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "verify_interval")

    def test_unknown_option(self):
        create_cwd(cwd())
        Config._cache = {}
        Config._conf["operationality"]["ip_api"] = None
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "verify_interval")

    def test_invalid_optiontype(self):
        create_cwd(cwd())
        Config._cache = {}
        Config._conf["operationality"]["ip_api"] = int
        with pytest.raises(Socks5ConfigError):
            cfg("socks5man", "verify_interval")

    def test_confbool(self):
        assert confbool("yes")
        assert confbool("1")
        assert confbool("true")
        assert confbool("on")
        assert confbool("Yes")
        assert confbool("True")
        assert confbool("On")
        assert not confbool("off")
        assert not confbool("0")

    def test_config_read_clear_cache(self):
        create_cwd(cwd())
        Config._cache = {"test": "test"}
        Config().read()
        assert len(Config._cache) > 0
        assert "test" not in Config._cache
