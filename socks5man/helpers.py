from __future__ import absolute_import
import logging
import socket
import socks
import struct
import time
import urllib.request
import urllib.error

from socks5man.config import cfg
from socks5man.constants import IANA_RESERVERD_IPV4_RANGES
from socks5man.misc import cwd

from geoip2 import database as geodatabase
from geoip2.errors import GeoIP2Error

log = logging.getLogger(__name__)

class Dictionary(dict):
    """Custom dict support reading keys as attributes"""

    def __getattr__(self, key):
        return self.get(key, None)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

def is_reserved_ipv4(ip):
    """Check if the IP belongs to reserved addr_block.
    @param ip: IP address to verify.
    @return: boolean representing whether the IP belongs to
    a private addr_block or not.
    """

    for addr_block in IANA_RESERVERD_IPV4_RANGES:
        try:
            ipaddr = struct.unpack(">I", socket.inet_aton(ip))[0]
            netaddr, bits = addr_block.split("/")
            network_low = struct.unpack(">I", socket.inet_aton(netaddr))[0]
            network_high = network_low | (1 << (32 - int(bits))) - 1

            if ipaddr <= network_high and ipaddr >= network_low:
                return True
        except:
            continue

    return False

def is_ipv4(ip):
    """Try to parse string as Ipv4. Return True if success, False
    otherwise"""
    try:
        if not isinstance(ip, type(str)):
            ip = str(ip)
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

class GeoInfo(object):

    georeader = None

    @staticmethod
    def ipv4info(ip):
        """Returns a dict containing the country, country_code, and city for
        a given IPv4 address"""
        result = {
            "country": "unknown",
            "country_code": "unknown",
            "city": "unknown"
        }

        if not GeoInfo.georeader:
            georeader = geodatabase.Reader(
                cwd("geodb", "extracted", "geodblite.mmdb")
            )

        if is_reserved_ipv4(ip):
            return result

        try:
            geodata = georeader.city(ip)
            if geodata.country.name:
                result["country"] = geodata.country.name
            if geodata.country.iso_code:
                result["country_code"] = geodata.country.iso_code
            if geodata.city.name:
                result["city"] = geodata.city.name
        except (GeoIP2Error, ValueError):
            return result

        return result

def get_ipv4_hostname(hostname):
    """Get IPv4 for specified hostname. Return None on fail"""
    try:
        return socket.gethostbyname(hostname)
    except socket.gaierror:
        return None

def validify_host_port(host, port):
    """Returns a dict with ip and port if both are valid, otherwise
    returns None"""

    if not host:
        return None

    if not is_ipv4(host):
        host = get_ipv4_hostname(host)
        if not host:
            return None

    if not port:
        return None

    try:
        port = int(port)
    except ValueError:
        return None

    if port < 1 or port > 65534:
        return None

    return Dictionary(
        ip=host,
        port=port
    )

def get_over_socks5(url, host, port, username=None, password=None, timeout=3):
    """Make a HTTP GET request over socks5 of the given URL"""

    socks.set_default_proxy(socks.SOCKS5, host, port, username=username, password=password)

    response = None
    clean_socket = socket.socket
    try:
        socket.socket = socks.socksocket
        response = urllib.request.urlopen(url, timeout=timeout).read()
    except urllib.error.URLError as e:
        log.error("Error making HTTP GET over socks5: %s", e)
    finally:
        socket.socket = clean_socket
    return response

def approximate_bandwidth(host, port, username=None, password=None,
                          maxfail=1, times=2, timeout=10):
    """Tries to determine the average download speed in Mbit/s.
    Higher 'times' values will result in more accurate speeds, but will
    take a longer time.
    specified socks5. This value is subtracted from the total time it takes
    to download a test file.
    @param maxfail: The maximum amount of times the socks5 is allowed to
    timeout before the measurement should stop
    @param times: The amount of times the test file should be downloaded.
    Optimal amount would be 3-4.
    """
    total = 0
    fails = 0
    test_url = cfg("bandwidth", "download_url")

    for t in range(times):
        start = time.time()
        response = get_over_socks5(
            test_url, host, port, username=username, password=password,
            timeout=timeout
        )
        if not response:
            if fails >= maxfail:
                return None
            fails += 1
            continue

        took = time.time() - start

        # Calculate the approximate Mbit/s
        try:
            speed = (len(response) / took) / 1000000 * 8
        except ZeroDivisionError:
            # Can be thrown if the download was instant. To still calculate
            # a speed, use 0.001 as the time it took
            speed = (len(response) / 0.001) / 1000000 * 8

        # If the used file to measure is smaller than approx 1 MB,
        # add a small amount as the small size might cause the TCP window
        # to stay small
        if len(response) < 1000000:
            speed += speed * 0.1

        total += speed

    return total / times
