import logging
import os
import socket
import shutil
import time
import urllib2

from socks5man.config import cfg
from socks5man.database import Database
from socks5man.helpers import GeoInfo, is_ipv4, get_ipv4_hostname
from socks5man.misc import cwd, unpack_mmdb
from socks5man.socks5 import Socks5

log = logging.getLogger(__name__)
db = Database()

def verify_all(repeated=False, operational=None, unverified=None):

    last_bandwidth = None
    bandwidth_checked = False
    download_verified = False
    if repeated:
        log.info("Starting continuous verification")

    while True:
        socks5_list = db.list_socks5(
            operational=operational, unverified=unverified
        )
        log.debug("Verifying %s socks5 servers", len(socks5_list))
        for socks5 in socks5_list:
            socks5 = Socks5(socks5)

            log.info(
                "Testing socks5 server: '%s:%s'", socks5.host, socks5.port
            )
            if socks5.verify():
                log.info("Operationality check: OK")
            else:
                log.warning(
                    "Operationality check (%s:%s): FAILED",
                    socks5.host, socks5.port
                )
                continue

            if cfg("connection_time", "enabled"):
                con_time = socks5.measure_connection_time()
                if con_time:
                    log.debug("Measured connection time: %s", con_time)
                else:
                    log.warning(
                        "Connection time measurement failed for: '%s:%s'",
                        socks5.host, socks5.port
                    )
                    continue

            if cfg("bandwidth", "enabled"):
                if last_bandwidth:
                    waited = time.time() - last_bandwidth
                    if waited < cfg("socks5man", "bandwidth_interval"):
                        continue

                if not download_verified:
                    download_url = cfg("bandwidth", "download_url")
                    try:
                        urllib2.urlopen(download_url, timeout=5)
                        download_verified = True
                    except (socket.error, urllib2.URLError) as e:
                        log.error(
                            "Failed to download speed test file: '%s'. Please"
                            " verify the configured file is still online!"
                            " Without this file, it is not possible to"
                            " approximate the bandwidth of a socsk5 server."
                            " Error: %s", download_url, e
                        )
                        continue

                bandwidth_checked = True
                bandwidth = socks5.approx_bandwidth()
                if bandwidth:
                    log.debug(
                        "Approximate bandwidth: %s Mbit/s down", bandwidth
                    )
                else:
                    log.warning(
                        "Bandwidth approximation test failed for: '%s:%s'",
                        socks5.host, socks5.port
                    )

        if bandwidth_checked:
            bandwidth_checked = False
            last_bandwidth = time.time()

        if not repeated:
            break

        time.sleep(cfg("socks5man", "verify_interval"))

def update_geodb():
    version_file = cwd("geodb", ".version")
    if not os.path.isfile(version_file):
        log.error("No geodb version file '%s' is missing", version_file)
        return

    with open(version_file, "rb") as fp:
        current_version = fp.read()

    try:
        latest_version = urllib2.urlopen(cfg("geodb", "geodb_md5_url")).read()
    except urllib2.URLError as e:
        log.error("Error retrieving latest geodb version hash: %s", e)
        return

    if current_version == latest_version:
        log.info("GeoIP database at latest version")
        return

    extracted = cwd("geodb", "extracted")
    renamed = None
    if os.path.exists(extracted):
        renamed = cwd("geodb", "old-extracted")
        os.rename(extracted, renamed)

    try:
        url = cfg("geodb", "geodb_url")
        log.info("Downloading latest version: '%s'", url)
        mmdbtar = urllib2.urlopen(url).read()
    except urllib2.URLError as e:
        log.error(
            "Failed to download new mmdb tar. Is the URL correct? %s", e
        )
        if renamed:
            log.error("Restoring old version..")
            os.rename(renamed, extracted)
        return

    tarpath = cwd("geodb", "geodblite.tar.gz")
    with open(tarpath, "wb") as fw:
        fw.write(mmdbtar)

    os.mkdir(extracted)

    unpack_mmdb(tarpath, cwd("geodb", "extracted", "geodblite.mmdb"))
    log.info("Version update complete")

    if renamed:
        log.debug("Removing old version")
        shutil.rmtree(renamed)

    log.info("Updating geo IP information for all existing servers")
    GeoInfo.georeader = None
    for socks5 in db.list_socks5():
        log.debug(
            "Updating server: '%s'. Current country: %s",
            socks5.host, socks5.country
        )
        ip = socks5.host
        if not is_ipv4(ip):
            ip = get_ipv4_hostname(ip)

        geoinfo = GeoInfo.ipv4info(ip)
        old = (socks5.country, socks5.country_code, socks5.city)
        new = (geoinfo["country"], geoinfo["country_code"], geoinfo["city"])
        if old == new:
            log.debug("Geo IP info unchanged")
            continue

        log.debug(
            "Geo IP info changed. New country=%s, country_code=%s, city=%s",
            geoinfo["country"], geoinfo["country_code"], geoinfo["city"]
        )
        db.update_geoinfo(
            socks5.id, country=geoinfo["country"],
            country_code=geoinfo["country_code"], city=geoinfo["city"]
        )
