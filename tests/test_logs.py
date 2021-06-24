from __future__ import absolute_import
import logging
import mock
import os
import tempfile

log = logging.getLogger(__name__)

from socks5man.logs import init_loggers
from socks5man.misc import set_cwd

@mock.patch("socks5man.logs.red")
@mock.patch("socks5man.logs.yellow")
def test_init_logger(my, mr):
    tmpdir = tempfile.mkdtemp()
    set_cwd(tmpdir)
    assert not os.path.exists(os.path.join(tmpdir, "socks5man.log"))
    init_loggers(logging.DEBUG)
    log.error("TEST")
    log.warning("TEST")
    assert os.path.isfile(os.path.join(tmpdir, "socks5man.log"))
    my.assert_called_once()
    mr.assert_called_once()
