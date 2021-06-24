from __future__ import absolute_import
from __future__ import print_function
import click
import csv
import logging
import os
import sys
import subprocess

from socks5man.database import Database, SCHEMA_VERSION
from socks5man.exceptions import Socks5manError
from socks5man.logs import init_loggers
from socks5man.manager import Manager
from socks5man.tools import verify_all, update_geodb
from socks5man.misc import cwd


log = logging.getLogger(__name__)
m = Manager()
db = Database()

@click.group()
@click.option("-d", "--debug", is_flag=True, help="Enable debug logging")
@click.pass_context
def main(ctx, debug):
    """This tool can be used to manage your socks5 servers.
    Each subcommand has its own help information."""
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    init_loggers(level)

    if db.db_migratable():
        log.error(
            "Database schema version mismatch. Expected: %s. Optionally make "
            "a backup of '%s' and then apply automatic database migration "
            "by using: 'socks5man migrate'",
            SCHEMA_VERSION, cwd("socks5man.db")
        )

        if ctx.invoked_subcommand != "migrate":
            exit(1)

@main.command()
@click.option("-r", "--repeated", is_flag=True, help="Continuously keep verifying all servers at the interval specified in the config")
@click.option("--operational", is_flag=True, help="Only verify socks5 servers that are currently marked as operational")
@click.option("--non-operational", is_flag=True, help="Only verify socks5 servers that are currently marked as not operational")
@click.option("--unverified", is_flag=True, help="Only verify socks5 servers that have never been verified/tested to be operational")
def verify(repeated, operational, non_operational, unverified):
    """Verify if the servers are operational."""
    if operational:
        operational = True
    elif non_operational:
        operational = False

    try:
        verify_all(repeated, operational, unverified)
    except KeyboardInterrupt:
        log.warning("CTRL+C detected! exiting.")
        sys.exit(0)

@main.command()
@click.argument("host")
@click.argument("port", type=click.INT)
@click.option("-u", "--username", help="Username for this socks5 server")
@click.option("-p", "--password", help="Password for this socks5 server")
@click.option("-d", "--description", help="Description for this socks5 server")
@click.option("-pi", "--private", is_flag=True, help="Private server ip")
def add(host, port, username, password, description, private):
    """Add socks5 server."""
    if username and not password or password and not username:
        log.warning(
            "Both a username and password need to be provided if the socks5"
            " server is authenticated"
        )
        sys.exit(1)

    try:
        entry = m.add(
            host, port, username=username, password=password,
            description=description, private=private
        )
    except Socks5manError as e:
        log.error("Failed to add socks5 server: %s", e)
        sys.exit(1)

    log.info(
        "Added socks5 '%s:%s', country=%s, country code=%s, city=%s",
        entry.host, entry.port, entry.country, entry.country_code, entry.city
    )

@main.command("bulk-add")
@click.argument("file_path")
@click.option("-d", "--description", help="Description for this socks5 server bulk")
def bulk_add(file_path, description):
    """Bulk add socks5 servers from CSV file. It does not verify if any of
     the provided servers already exist."""
    if not os.path.isfile(file_path):
        log.error("File '%s' does not exist", file_path)
        sys.exit(1)

    if not os.access(file_path, os.R_OK):
        log.error("No read access on file '%s'", file_path)
        sys.exit(1)

    with open(file_path, "rb") as fp:
        try:
            socks5s = [socks5 for socks5 in csv.DictReader(fp)]
        except csv.Error as e:
            log.error("Error reading CSV file: %s", e)
            sys.exit(1)

    if not socks5s:
        log.warning("No socks5 servers to add")
        sys.exit(1)

    try:
        count = m.bulk_add(socks5s, description=description)
        if count:
            log.info("Successfully bulk added %s servers", count)
        else:
            log.error(
                "Failed to bulk add servers. See log for more information"
            )
    except Socks5manError as e:
        log.error("Failed to bulk add: %s", e)
        sys.exit(1)

@main.command("update-geodb")
def geo():
    """Update version of the used Maxmind geodb, and update the geo IP
    information for each existing server."""
    update_geodb()

@main.command()
@click.argument("socks5_ids", nargs=-1, required=False, type=click.INT)
@click.option("--everything", is_flag=True, help="Delete all socks5 servers")
@click.option("--non-operational", is_flag=True, help="Delete all socks5 servers that are not operational")
@click.option("--idrange", help="Delete the given range of socks5 ids. Example: 5-10")
def delete(socks5_ids, everything, non_operational, idrange):
    """Remove the specified socks5 servers. The deletion flags and paramaters
    cannot be mixed."""
    if socks5_ids:
        for socksid in socks5_ids:
            log.info("Deleting socks5 server with id: %s", socksid)
            try:
                m.delete(socks5_id=socksid)
            except Socks5manError as e:
                log.error("Error deleting socks5 id %s. Error: %s", e)

    elif non_operational:
        to_delete = [s.id for s in m.list_socks5(operational=False)]
        try:
            db.bulk_delete_socks5(to_delete)
        except Socks5manError as e:
            log.error(
                "Error bulk deleting socks5s. Error: %s", e
            )
            sys.exit(1)

        log.info("Removed %s non-operational socks5 servers", len(to_delete))

    elif idrange:
        intrange = idrange.split("-")
        if len(intrange) < 2:
            log.error("Invalid integer range. Must provide 2 integers")
            sys.exit(1)

        for i in intrange:
            if not i.isdigit():
                log.error("Invalid integer: %s", i)
                sys.exit(1)

        start, end = intrange
        try:
            db.bulk_delete_socks5([s for s in range(int(start), int(end)+1)])
        except Socks5manError as e:
            log.error("Error bulk deleting socks5s. Error: %s", e)
            sys.exit(1)

        log.info("Deleted socks5 servers matching the ID range")

    elif everything:
        try:
            m.delete_all()
        except Socks5manError as e:
            log.error("Error deleting all socks5 server: %s", e)
            sys.exit(1)

        log.info("Removed all socks5 servers")

@main.command()
@click.option("--country", help="Filtery by the country of a socks5 ip")
@click.option("--code", help="Filter by the 2-letter country code")
@click.option("--city", help="Filter by the city of a socks5 ip")
@click.option("--host", help="Filtery by a hostname/ip")
@click.option("--operational", is_flag=True, help="Filter by socks5 servers that were tested to be operational")
@click.option("--non-operational", is_flag=True, help="Filter by socks5 servers that are not operational or untested")
@click.option("--count", is_flag=True, help="Display the number of matching socks5s")
@click.option("--export", type=click.Path(), help="Export as CSV to given file path")
def list(country, code, city, host, operational, non_operational, count,
         export):
    """List or export all socks5 servers."""
    if not operational:
        operational = None
    elif non_operational:
        operational = False

    socks5s = m.list_socks5(
        country=country, country_code=code, city=city,
        host=host, operational=operational
    )

    if not socks5s:
        log.warning("No (matching) socks5 servers found")
        sys.exit(1)

    if count:
        log.info("%s matching socks5 servers found.", len(socks5s))
        sys.exit(0)

    if not export:
        print((
            "{:<4} {:<12} {:<20} {:<5} {:<16} {:<12} {:<16} {:<16} {:<16}{:<16}".format(
                "ID", "Operational", "Host", "Port", "Country", "Country Code", "City",
                "Username", "Password", "Description",
            )
        ))
        for socks5 in socks5s:
            print(
                "{:<4} {:<12} {:<20} {:<5} {:<16} {:<12} {:<16} {:<16} {:<16} {:<16}".format(
                    socks5.id, "Yes" if socks5.operational else "No", socks5.host, socks5.port,
                    socks5.country, socks5.country_code, socks5.city,
                    socks5.username if socks5.username else "", socks5.password if socks5.password else "",
                    socks5.description if socks5.description else ""
                )
            )

        sys.exit(0)

    if os.path.exists(export):
        log.error("Path '%s' exists", export)
        sys.exit(1)

    with open(export, "wb") as fw:
        csv_w = csv.writer(fw)
        header = True
        for socks5 in socks5s:
            socks5_d = socks5.to_dict()
            if header:
                csv_w.writerow(list(socks5_d.keys()))
                header = False

            csv_w.writerow(list(socks5_d.values()))


@main.command()
@click.option("--revision", default="head", help="Migrate to a specific version")
def migrate(revision):
    if not db.db_migratable():
        log.info("Database schema is already at the latest version")
        exit(0)

    try:
        subprocess.check_call(
            ["alembic", "upgrade", revision],
            cwd=cwd("db_migration", internal=True)
        )
    except subprocess.CalledProcessError as e:
        log.exception("Database migration failed. %s", e)
        exit(1)

    log.info("Database migration successful!")
