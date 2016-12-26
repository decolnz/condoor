"""Protocols module providing different protocol handlers."""


from collections import defaultdict

from condoor.protocols.base import Protocol
from condoor.protocols.ssh import SSH
from condoor.protocols.telnet import Telnet
from condoor.protocols.telnet import TelnetConsole

protocol2object = defaultdict(
    Protocol, {
        'ssh': SSH,
        'telnet': Telnet,
        'telnet_console': TelnetConsole,
        'ssh_console': SSH,
    }
)


def make_protocol(protocol_name, device):
    """Factory function providing the Protocol object."""
    return protocol2object[protocol_name](device)
