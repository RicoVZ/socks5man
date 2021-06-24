from __future__ import absolute_import
import os
import shutil
import tempfile


class CleanedTempFile(object):

    def __init__(self):
        self.dirs = []
        self.files = []

    def clean(self):
        for d in self.dirs:
            if os.path.exists(d):
                shutil.rmtree(d)

        for f in self.files:
            if os.path.isfile(f):
                os.remove(f)

    def mkdtemp(self):
        tmpdir = tempfile.mkdtemp()
        self.dirs.append(tmpdir)
        return tmpdir

    def mkstemp(self):
        fd, path = tempfile.mkstemp()
        self.files.append(path)
        return fd, path
