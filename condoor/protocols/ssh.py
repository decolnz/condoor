"""Provides SSH driver class."""

from functools import partial
import logging
import pexpect

from condoor.fsm import FSM, action
from condoor.utils import pattern_to_str
from condoor.protocols.base import Protocol
from condoor.actions import a_send_password, a_authentication_error, a_send, a_unable_to_connect, a_save_last_pattern,\
    a_send_line

from condoor.exceptions import ConnectionError, ConnectionTimeoutError
from condoor.config import CONF

logger = logging.getLogger(__name__)


MODULUS_TOO_SMALL = "modulus too small"
PROTOCOL_DIFFER = "Protocol major versions differ"
NEWSSHKEY = "fingerprint is"
KNOWN_HOSTS = "added.*to the list of known hosts"
HOST_KEY_FAILED = "key verification failed"

_C = CONF['protocol']['ssh']


class SSH(Protocol):
    """SSH protocol implementation."""

    def __init__(self, device):
        """Initialize SSH object."""
        super(SSH, self).__init__(device)

    def get_command(self, version=2):
        """Return the SSH protocol specific command to connect."""
        if self.username:
            # Not supported on SunOS
            # "-o ConnectTimeout={}
            command = "ssh " \
                      "-o UserKnownHostsFile=/dev/null " \
                      "-o StrictHostKeyChecking=no " \
                      "-{} " \
                      "-p {} {}@{}".format(version, self.port, self.username, self.hostname)
        else:
            command = "ssh " \
                      "-o UserKnownHostsFile=/dev/null " \
                      "-o StrictHostKeyChecking=no " \
                      "-{} " \
                      "-p {} {}".format(version, self.port, self.hostname)
        return command

    def connect(self, driver):
        """Connect using the SSH protocol specific FSM."""
        #                      0                    1                 2
        events = [driver.password_re, self.device.prompt_re, driver.unable_to_connect_re,
                  #   3          4              5               6                   7
                  NEWSSHKEY, KNOWN_HOSTS, HOST_KEY_FAILED, MODULUS_TOO_SMALL, PROTOCOL_DIFFER,
                  #      8              9
                  driver.timeout_re, pexpect.TIMEOUT]

        transitions = [
            (driver.password_re, [0, 1, 4, 5], -1, partial(a_save_last_pattern, self), 0),
            (self.device.prompt_re, [0], -1, partial(a_save_last_pattern, self), 0),
            #  cover all messages indicating that connection was not set up
            (driver.unable_to_connect_re, [0], -1, a_unable_to_connect, 0),
            (NEWSSHKEY, [0], 1, partial(a_send_line, "yes"), 10),
            (KNOWN_HOSTS, [0, 1], 0, None, 0),
            (HOST_KEY_FAILED, [0], -1, ConnectionError("Host key failed", self.hostname), 0),
            (MODULUS_TOO_SMALL, [0], 0, self.fallback_to_sshv1, 0),
            (PROTOCOL_DIFFER, [0], 4, self.fallback_to_sshv1, 0),
            (PROTOCOL_DIFFER, [4], -1, ConnectionError("Protocol version differs", self.hostname), 0),
            (pexpect.TIMEOUT, [0], 5, partial(a_send, "\r\n"), 10),
            (pexpect.TIMEOUT, [5], -1, ConnectionTimeoutError("Connection timeout", self.hostname), 0),
            (driver.timeout_re, [0], -1, ConnectionTimeoutError("Connection timeout", self.hostname), 0),
        ]

        logger.debug("EXPECTED_PROMPT={}".format(pattern_to_str(self.device.prompt_re)))
        fsm = FSM("SSH-CONNECT", self.device, events, transitions, timeout=_C['connect_timeout'],
                  searchwindowsize=160)
        return fsm.run()

    def authenticate(self, driver):
        """Authenticate using the SSH protocol specific FSM."""
        #              0                     1                    2                  3
        events = [driver.press_return_re, driver.password_re, self.device.prompt_re, pexpect.TIMEOUT]

        transitions = [
            (driver.press_return_re, [0, 1], 1, partial(a_send, "\r\n"), 10),
            (driver.password_re, [0], 1, partial(a_send_password, self._acquire_password()),
             _C['first_prompt_timeout']),
            (driver.password_re, [1], -1, a_authentication_error, 0),
            (self.device.prompt_re, [0, 1], -1, None, 0),
            (pexpect.TIMEOUT, [1], -1,
             ConnectionError("Error getting device prompt") if self.device.is_target else partial(a_send, "\r\n"), 0)
        ]

        logger.debug("EXPECTED_PROMPT={}".format(pattern_to_str(self.device.prompt_re)))
        fsm = FSM("SSH-AUTH", self.device, events, transitions, init_pattern=self.last_pattern, timeout=30)
        return fsm.run()

    def disconnect(self, driver):
        """Disconnect using the protocol specific method."""
        self.device.ctrl.sendline('\x03')
        self.device.ctrl.sendline('\x04')

    # FIXME: This needs to be fixed and tested
    @action
    def fallback_to_sshv1(self, ctx):
        """Fallback to SSHv1."""
        command = self.get_command(version=1)
        ctx.spawn_session(command)
        return True
