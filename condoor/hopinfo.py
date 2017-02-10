"""Provides HopInfo class implementation and factory function."""

from urlparse import urlparse, parse_qs
from urllib import unquote

from condoor.exceptions import InvalidHopInfoError

# Standard protocol to port mapping
protocol2port_map = {
    'telnet': 23,
    'ssh': 22,
}


def make_hop_info_from_url(url, verify_reachability=None):
    """Factory function to build HopInfo object from url.

    It allows only telnet and ssh as a valid protocols.

    Args:
        url (str): The url string describing the node. i.e.
            telnet://username@1.1.1.1. The protocol, username and address
            portion of url is mandatory. Port and password is optional.
            If port is missing the standard protocol -> port mapping is done.
            The password is optional i.e. for TS access directly to console
            ports.
            The path part is treated as additional password required for some
            systems, i.e. enable password for IOS devices.:
            telnet://<username>:<password>@<host>:<port>/<enable_password>
            <enable_password> is optional

        verify_reachability: This is optional callable returning boolean
            if node is reachable. It can be used to verify reachability
            of the node before making a connection. It can speedup the
            connection process when node not reachable especially with
            telnet having long timeout.

    Returns:
        HopInfo object or None if url is invalid or protocol not supported

    """
    parsed = urlparse(url)
    username = None if parsed.username is None else unquote(parsed.username)  # It's None if not exists
    password = None if parsed.password is None else unquote(parsed.password)  # It's None if not exists

    try:
        enable_password = parse_qs(parsed.query)["enable_password"][0]
    except KeyError:
        enable_password = None

    hop_info = HopInfo(
        parsed.scheme,
        parsed.hostname,
        username,
        password,
        parsed.port,
        enable_password,
        verify_reachability=verify_reachability
    )
    if hop_info.is_valid():
        return hop_info
    raise InvalidHopInfoError


class HopInfo(object):
    """HopInfo class contains implementation.

    It maintain all the information needed for node (jump host or device) access.
    """

    def __init__(
            self,
            protocol,
            hostname,
            username,
            password=None,
            port=None,
            enable_password=None,
            verify_reachability=None):
        """
        Initialize the HopInfo object.

        Args:
            protocol (str): 'telnet' or 'ssh'. The other protocols are not
                implemented.
            hostname (str): The hostname or IP address of the node
            username (str): The username for node access
            password (str): The password for provided username. This
                argument is optional and can be omitted. i.e. ssh hey auth
                or TS without authentication.
            port (number): Optional TCP port number. If not provided the
                the standard mapping for telnet and ssh is done automatically.
            verify_reachability (callable): This is optional callable returning
                True if if node is reachable. It can be used to verify
                reachability of the node before making a connection.
                It can speedup the connection process when node not
                reachable especially with telnet having long timeout.
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.protocol = protocol
        self.enable_password = enable_password if enable_password != "" else None

        # if port not provided map port based on protocol standards
        self.port = port if port else \
            protocol2port_map.get(self.protocol, None)

        self.verify_reachability = verify_reachability

    def is_valid(self):
        """Return if protocol is valid."""
        if self.protocol not in ['telnet', 'ssh']:
            return False
        return True

    def is_reachable(self):
        """Return if host is reachable."""
        if self.verify_reachability and \
                hasattr(self.verify_reachability, '__call__'):
            return self.verify_reachability(host=self.hostname, port=self.port)
        # assume is reachable if can't verify
        return True

    def __repr__(self):
        """Return string representation of the class."""
        if self.username is None:
            repr_str = "{}://{}:{}".format(self.protocol, self.hostname, self.port)
        else:
            repr_str = "{}://{}@{}:{}".format(self.protocol, self.username, self.hostname, self.port)
        return repr_str
