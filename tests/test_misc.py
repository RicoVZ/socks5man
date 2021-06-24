from __future__ import absolute_import
import mock
import os
import tempfile

from geoip2 import database as geodatabase

import socks5man
from socks5man.misc import (
    set_cwd, cwd, create_cwd, unpack_mmdb, md5
)
from tests.helpers import CleanedTempFile

class TestCWD(object):

    def setup_class(self):
        self.tmpfile = CleanedTempFile()

    def teardown_class(self):
        self.tmpfile.clean()

    def test_set_cwd(self):
        tmpdir = self.tmpfile.mkdtemp()
        set_cwd(tmpdir)
        from socks5man.misc import _path
        assert _path == tmpdir

    def test_cwd_normal(self):
        tmpdir = self.tmpfile.mkdtemp()
        set_cwd(tmpdir)
        assert cwd("conf") == os.path.join(tmpdir, "conf")

    @mock.patch("socks5man.misc.create_cwd")
    def test_cwd_nonexist(self, mc):
        tempdir = os.path.join(tempfile.gettempdir(), "UTvYHUvitYV")
        set_cwd(tempdir)
        cwd("test")
        mc.assert_called_once()

    def test_cwd_internal(self):
        tmpdir = self.tmpfile.mkdtemp()
        set_cwd(tmpdir)
        p = cwd("conf", "socks5man.conf", internal=True)
        p2 = os.path.join(
            socks5man.__path__[0], "setupdata", "conf", "socks5man.conf"
        )
        assert p == p2

    def test_create_cwd(self):
        tmpdir = self.tmpfile.mkdtemp()
        set_cwd(tmpdir)
        assert os.listdir(tmpdir) == []
        create_cwd(tmpdir)

        assert os.path.isfile(os.path.join(tmpdir, "conf", "socks5man.conf"))
        assert os.path.isfile(
            os.path.join(tmpdir, "geodb", "extracted", "geodblite.mmdb")
        )
        assert os.path.isfile(os.path.join(tmpdir, "geodb", ".version"))
        assert os.path.exists(
            os.path.join(tmpdir, "geodb", "geodblite.tar.gz")
        )

class TestOther(object):

    def setup_class(self):
        self.tempfile = CleanedTempFile()

    def teardown_class(self):
        self.tempfile.clean()

    def test_md5(self):
        fd, path = self.tempfile.mkstemp()

        os.write(fd, b"tosti")
        os.close(fd)
        assert md5(path) == "9e796589d183889f5c65af8b736490bb"

    def test_unpack_mmdb(self):
        tmpdir = self.tempfile.mkdtemp()
        set_cwd(tmpdir)
        tar_p = cwd("geodb", "geodblite.tar.gz", internal=True)
        assert os.listdir(tmpdir) == []
        os.mkdir(os.path.join(tmpdir, "geodb"))
        mmdb_p = os.path.join(tmpdir, "test.mmdb")
        unpack_mmdb(tarpath=tar_p, to=mmdb_p)
        assert os.path.isfile(mmdb_p)
        version_file = os.path.join(tmpdir, "geodb", ".version")
        assert os.path.isfile(version_file)
        assert md5(tar_p) == open(version_file, "r").read()
        r = geodatabase.Reader(mmdb_p)
        geodata = r.city("8.8.8.8")
        assert geodata.country.name.lower() == "united states"
