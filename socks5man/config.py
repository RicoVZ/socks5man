from __future__ import absolute_import
import os
import configparser

from socks5man.exceptions import Socks5ConfigError
from socks5man.misc import cwd

def confbool(val):
    if val.lower() in ("true", "1", "yes", "on"):
        return True
    return False

class Config(object):

    _cache = {}
    _conf = {
        "socks5man": {
            "verify_interval": int,
            "bandwidth_interval": int
        },
        "operationality": {
            "ip_api": str,
            "timeout": int,
        },
        "connection_time": {
            "enabled": confbool,
            "timeout": int,
            "hostname": str,
            "port": int
        },
        "bandwidth": {
            "enabled": confbool,
            "download_url": str,
            "times": int,
            "timeout": int
        },
        "geodb": {
            "geodb_url": str,
            "geodb_md5_url": str
        }
    }

    def read(self):
        if Config._cache:
            Config._cache = {}

        config = configparser.ConfigParser()

        confpath = cwd("conf", "socks5man.conf")
        if not os.path.isfile(confpath):
            raise Socks5ConfigError(
                "Cannot read config. Config file '%s' does not exist" %
                confpath
            )
        try:
            config.read(confpath)
        except configparser.Error as e:
            raise Socks5ConfigError(
                "Cannot parse config file. Error: %s" % e
            )

        for section in config.sections():
            if section not in self._conf:
                raise Socks5ConfigError(
                    "Config has unknown config section '%s'. Add section to"
                    " the config class to prevent this error." % section
                )

            if section not in Config._cache:
                Config._cache[section] = {}

            for k in config.options(section):
                option_type = self._conf[section].get(k)
                if not option_type:
                    raise Socks5ConfigError(
                        "Unknown option '%s' in config section '%s'. Add the"
                        " option and its type to the config class to prevent"
                        " this error." % (k, section)
                    )

                value = config.get(section, k)
                try:
                    value = option_type(value)
                except ValueError as e:
                    raise Socks5ConfigError(
                        "Cannot cast value '%s' of option '%s' in section"
                        " '%s' to type '%s'. %s" % (
                            value, k, section, option_type, e
                        )
                    )

                Config._cache[section][k] = value

def cfg(*args):
    if not Config._cache:
        Config().read()

    val = None
    for arg in args:
        try:
            if val:
                val = val[arg]
            else:
                val = Config._cache[arg]
        except KeyError:
            raise Socks5ConfigError(
                "Tried to read non-existing config option: %s" % str(args)
            )

    return val
