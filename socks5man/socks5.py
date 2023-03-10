from __future__ import absolute_import
import logging
import socks
import sys
import time

from socks5man.config import cfg
from socks5man.database import Database
from socks5man.helpers import (
    get_over_socks5, is_ipv4, get_ipv4_hostname, approximate_bandwidth,
    is_reserved_ipv4
)

log = logging.getLogger(__name__)

# Required for socks connecting to work on Windows
if sys.platform == "win32":
    import win_inet_pton

db = Database()

class Socks5(object):
    """
    Socks5 wrapper class. Retrieve info and verify if socks
    is operational. Object is initialized with a socks5 database object by the
    manager class.
    """

    def __init__(self, db_socks5):
        self.db_socks5 = db_socks5

    def verify(self):
        """
        Test if this socks5 can be connected to and retrieve its own
        IP through the configured IP api. Automatically updates the
        'operational' value in the database

        :returns: True if server is operational, false otherwise
        :rtype: bool
        """
        operational = False
        ip = self.host
        if not is_ipv4(ip):
            ip = get_ipv4_hostname(ip)

        try:
            response = get_over_socks5(
                cfg("operationality", "ip_api"), self.host, self.port,
                username=self.username, password=self.password,
                timeout=cfg("operationality", "timeout")
            )
        except AttributeError:
            return operational

        if response:
            if ip == response.decode("utf-8"):
                operational = True

            # If a private ip is used, the api response will not match with
            # the configured host or its ip. There was however a response,
            # therefore we still mark it as operational
            elif self.private or (is_reserved_ipv4(ip) and is_ipv4(response.decode("utf-8"))):
                operational = True

        db.set_operational(self.id, operational)
        return operational

    def approx_bandwidth(self):
        """
        Calculate an approximate Mbit/s download speed using
        the file specified in the config to download. Automatically
        updated in the database

        :returns: An approximate download speed in Mbit/s
        :rtype: float
        """
        approx_bandwidth = approximate_bandwidth(
            self.host, self.port, username=self.username,
            password=self.password, times=cfg("bandwidth", "times"),
            timeout=cfg("bandwidth", "timeout")
        )
        db.set_approx_bandwidth(self.id, approx_bandwidth)
        return approx_bandwidth

    def measure_connection_time(self):
        """
        Measure the time it takes to connect to the specified connection
        test URL in the config. Result is automatically stored in the
        database

        :returns: An approximate connection time in seconds
        :rtype: float
        """
        s = socks.socksocket()
        s.set_proxy(
            socks.SOCKS5, self.host, self.port, username=self.username,
            password=self.password
        )

        s.settimeout(cfg("connection_time", "timeout"))
        start = time.time()
        try:
            s.connect((
                    cfg("connection_time", "hostname"),
                    cfg("connection_time", "port")
            ))
            s.close()
        # socket.error, socks.ProxyError
        except Exception as e:
            log.error("Error connecting in connection time test: %s", e)
            connect_time = None
        else:
            connect_time = time.time() - start

        db.set_connect_time(self.id, connect_time)
        return connect_time

    def to_dict(self):
        """
        Dump the underlying database object to a dictionary

        :returns: A dictionary containing all database values
        :rtype: dict
        """
        return self.db_socks5.to_dict()

    @property
    def id(self):
        """
        The server id

        :rtype: int
        """
        return self.db_socks5.id

    @property
    def host(self):
        """
        The server hostname/IP

        :rtype: str
        """
        if self.db_socks5.host:
            return self.db_socks5.host
        return None

    @property
    def port(self):
        """
        The server port

        :rtype: int
        """
        return self.db_socks5.port

    @property
    def country(self):
        """
        The country the server resides in

        :rtype: str
        """
        if self.db_socks5.country:
            return self.db_socks5.country
        return None

    @property
    def country_code(self):
        """
        The (ISO 3166-1 alpha-2) country code of the country the server
        resides in

        :rtype: str
        """
        return self.db_socks5.country_code

    @property
    def city(self):
        """
        The city the server resides in

        :rtype: str
        """
        if self.db_socks5.city:
            return self.db_socks5.city
        return None

    @property
    def username(self):
        """
        The username for this server

        :rtype: str
        """
        if self.db_socks5.username:
            return self.db_socks5.username
        return None

    @property
    def password(self):
        """
        The password for this server

        :rtype: str
        """
        return self.db_socks5.password

    @property
    def added_on(self):
        """
        The date and time this server was added

        :rtype: DateTime
        """
        return self.db_socks5.added_on

    @property
    def last_use(self):
        """
        The date and time this server was last acquired/used. This field
        is updated when a server is acquired by Manager().acquire()

        :rtype: DateTime
        """
        return self.db_socks5.last_use

    @property
    def last_check(self):
        """
        The date and time this server's operationality was last checked

        :rtype: DateTime
        """
        return self.db_socks5.last_check

    @property
    def operational(self):
        """
        Boolean that tells if the last operationality check was successful or
        not.

        :rtype: bool
        """
        return self.db_socks5.operational

    @property
    def bandwidth(self):
        """
        Approximate bandwidth down in Mbit/s. The bandwidth check is only
        performed if it is enabled in the socks5man.conf

        :rtype: float
        """
        return self.db_socks5.bandwidth

    @property
    def connect_time(self):
        """
        The approximate connection time in seconds

        :rtype: float
        """
        return self.db_socks5.connect_time

    @property
    def description(self):
        """
        The description of this server

        :rtype: str
        """
        if self.db_socks5.description:
            return self.db_socks5.description
        return None

    @property
    def private(self):
        """
        Boolean that tells if the server is private ip.

        :rtype: bool
        """
        return self.db_socks5.private


    def __repr__(self):
        return "<Socks5(host=%s, port=%s, country=%s, authenticated=%s)>" % (
            self.host, self.port, self.country, (
                self.username is not None and self.password is not None
            )
        )
