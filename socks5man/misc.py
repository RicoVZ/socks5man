from __future__ import absolute_import
import hashlib
import os
import shutil
import sys
import tarfile

import socks5man

_path = None

def create_cwd(path=None):
    ignore = ["db_migration"]
    if not path:
        path = _path

    if not os.path.isdir(path):
        os.mkdir(path)

    for dir in os.listdir(cwd(internal=True)):
        if dir not in ignore and not os.path.exists(cwd(dir)):
            shutil.copytree(cwd(dir, internal=True), cwd(dir))

    unpack_mmdb(
        cwd("geodb", "geodblite.tar.gz"),
        cwd("geodb", "extracted", "geodblite.mmdb")
    )

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hash_md5.update(chunk)

    return hash_md5.hexdigest()

def unpack_mmdb(tarpath, to):
    with tarfile.open(tarpath) as tar:
        for member in tar:
            if not member.isfile():
                continue

            if os.path.splitext(member.name)[1] == ".mmdb":
                with open(to, "wb") as fw:
                    shutil.copyfileobj(tar.fileobj, fw, member.size)
                break

    geodb_hash = md5(tarpath)
    with open(cwd("geodb", ".version"), "w") as fw:
        fw.write(geodb_hash)

def set_cwd(path):
    global _path
    _path = os.path.expanduser(path)

def cwd(*args, **kwargs):
    if kwargs.get("internal"):
        return os.path.join(socks5man.__path__[0], "setupdata", *args)

    if not _path:
        set_cwd("~/.socks5man")

    if not os.path.isdir(_path):
        create_cwd(_path)

    return os.path.join(_path, *args)

def color(text, color_code):
    """Colorize text.
    @param text: text.
    @param color_code: color.
    @return: colorized text.
    """
    if sys.platform == "win32" and os.getenv("TERM") != "xterm":
        return text
    return "\x1b[%dm%s\x1b[0m" % (color_code, text)

def red(text):
    return color(text, 31)

def yellow(text):
    return color(text, 33)

class Singleton(type):
    """Singleton.
    @see: http://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                *args, **kwargs
            )
        return cls._instances[cls]
