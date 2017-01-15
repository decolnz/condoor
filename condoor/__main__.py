#!/usr/bin/env python
"""The condoor command line implementation."""

try:
    import click
except ImportError:
    print("Install click python package\n pip install click")
    exit()

import logging
import urlparse

import condoor


def echo_info(conn):
    """Print detected information."""
    click.echo("General information:")
    click.echo(" Hostname: {}".format(conn.hostname))
    click.echo(" HW Family: {}".format(conn.family))
    click.echo(" HW Platform: {}".format(conn.platform))
    click.echo(" SW Type: {}".format(conn.os_type))
    click.echo(" SW Version: {}".format(conn.os_version))
    click.echo(" Prompt: {}".format(conn.prompt))
    click.echo(" Console connection: {}".format(conn.is_console))

    click.echo("\nUDI:")
    click.echo(" PID: {}".format(conn.pid))
    click.echo(" Description: {}".format(conn.description))
    click.echo(" Name: {}".format(conn.name))
    click.echo(" SN: {}".format(conn.sn))
    click.echo(" VID: {}".format(conn.vid))


class URL(click.ParamType):
    """URL type validator."""

    name = 'url'

    def convert(self, value, param, ctx):
        """Convert to URL scheme."""
        if not isinstance(value, tuple):
            parsed = urlparse.urlparse(value)
            if parsed.scheme not in ('telnet', 'ssh'):
                self.fail('invalid URL scheme (%s).  Only telnet and ssh URLs are '
                          'allowed' % parsed, param, ctx)
        return value


log_levels = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "ERROR": logging.ERROR,
    "NONE": logging.NOTSET,
}


@click.command()
@click.option("--url", multiple=True, required=True, envvar='CONDOOR_URLS', type=URL(),
              help='The connection url to the host (i.e. telnet://user:pass@hostname). '
                   'The --url option can be repeated to define multiple jumphost urls. '
                   'If no --url option provided the CONDOOR_URLS environment variable is used.')
@click.option("--log-path", default=None, type=click.Path(),
              help="The logging path. If no path specified condoor logs are sent to stdout and session logs "
                   "are sent to stderr.")
@click.option("--log-level", type=click.Choice(["NONE", "DEBUG", "INFO", "ERROR"]),
              show_default=True, default='ERROR',
              help='Logging level.')
@click.option("--log-session", is_flag=True,
              help="Log terminal session.")
@click.option("--force-discovery", is_flag=True,
              help="Force full device discovery.")
@click.option("--cmd", multiple=True, default=[],
              help='The command to be send to the device. The --cmd option can be repeated multiple times.')
@click.option("--print-info", is_flag=True,
              help="Print the discovered information.")
def run(url, cmd, log_path, log_level, log_session, force_discovery, print_info):
    """Main function."""
    log_level = log_levels[log_level]
    conn = condoor.Connection("host", list(url), log_session=log_session, log_level=log_level, log_dir=log_path)
    try:
        conn.connect(force_discovery=force_discovery)
        if print_info:
            echo_info(conn)

        for command in cmd:
            result = conn.send(command)
            print("\nCommand: {}".format(command))
            print("Result: \n{}".format(result))
    except (condoor.ConnectionError, condoor.ConnectionAuthenticationError, condoor.ConnectionTimeoutError,
            condoor.InvalidHopInfoError, condoor.CommandSyntaxError, condoor.CommandTimeoutError,
            condoor.CommandError, condoor.ConnectionError) as excpt:
        click.echo(excpt)
    finally:
        conn.disconnect()
    return


if __name__ == '__main__':
    run()  # pylint: disable=no-value-for-parameter
