"""Provides the Controller class which is a wrapper to the pyexpect.spawn class."""

import re
import logging
import pexpect
from time import time

from condoor.utils import delegate, levenshtein_distance
from condoor.exceptions import ConnectionError, ConnectionTimeoutError

logger = logging.getLogger(__name__)


# Delegate following methods to _session class
@delegate("_session", ("expect", "expect_exact", "expect_list", "compile_pattern_list", "sendline",
                       "isalive", "sendcontrol", "send", "read_nonblocking", "setecho", "delaybeforesend"))
class Controller(object):
    """Controller class which wraps the pyexpect.spawn class."""

    def __init__(self, connection):
        """Initialize the Controller object for specific connection."""
        # delegated pexpect session
        self._session = None
        self._connection = connection

        self._logfile_fd = connection.session_fd
        self.connected = False
        self.authenticated = False
        self.last_hop = 0

    @property
    def hostname(self):
        """Return the hostname."""
        return self._connection.hostname

    def spawn_session(self, command):
        """Spawn the session using proper command."""
        if self._session and self.isalive():  # pylint: disable=no-member
            logger.debug("Executing command: '{}'".format(command))
            try:
                self.send(command)  # pylint: disable=no-member
                self.expect_exact(command, timeout=20)  # pylint: disable=no-member
                self.sendline()  # pylint: disable=no-member

            except (pexpect.EOF, OSError):
                raise ConnectionError("Connection error", self.hostname)
            except pexpect.TIMEOUT:
                raise ConnectionTimeoutError("Timeout", self.hostname)

        else:
            logger.debug("Spawning command: '{}'".format(command))
            try:
                self._session = pexpect.spawn(
                    command,
                    maxread=65536,
                    searchwindowsize=4000,
                    env={"TERM": "VT100"},  # to avoid color control characters
                    echo=False  # KEEP YOUR DIRTY HANDS OFF FROM ECHO!
                )
                self._session.delaybeforesend = 0.3
                rows, cols = self._session.getwinsize()
                if cols < 160:
                    self._session.setwinsize(1024, 160)
                    nrows, ncols = self._session.getwinsize()
                    logger.debug("Terminal window size changed from "
                                 "{}x{} to {}x{}".format(rows, cols, nrows, ncols))
                else:
                    logger.debug("Terminal window size: {}x{}".format(rows, cols))

            except pexpect.EOF:
                raise ConnectionError("Connection error", self.hostname)
            except pexpect.TIMEOUT:
                raise ConnectionTimeoutError("Timeout", self.hostname)

            self._session.logfile_read = self._logfile_fd
            self.connected = True

    def send_command(self, cmd):
        """Send command."""
        self.send(cmd)  # pylint: disable=no-member
        self.expect_exact([cmd, pexpect.TIMEOUT], timeout=15)  # pylint: disable=no-member
        self.sendline()  # pylint: disable=no-member

    def disconnect(self):
        """Disconnect the controller."""
        if self._session and self._session.isalive():
            logger.debug("Disconnecting the sessions")
            # self.sendline('\x03')  # pylint: disable=no-member
            # self.sendline('\x04')  # pylint: disable=no-member
            #
            # self.sendcontrol(']')  # pylint: disable=no-member
            # self.sendline('quit')  # pylint: disable=no-member
            self._session.close(force=True)
            self._session.wait()
        logger.debug("Disconnected")
        self.connected = False

    def try_read_prompt(self, timeout_multiplier):
        """Read the prompt.

        Based on try_read_prompt from pxssh.py
        https://github.com/pexpect/pexpect/blob/master/pexpect/pxssh.py
        """
        # maximum time allowed to read the first response
        first_char_timeout = timeout_multiplier * 2

        # maximum time allowed between subsequent characters
        inter_char_timeout = timeout_multiplier * 0.4

        # maximum time for reading the entire prompt
        total_timeout = timeout_multiplier * 4

        prompt = ""
        begin = time()
        expired = 0.0
        timeout = first_char_timeout

        while expired < total_timeout:
            try:
                char = self.read_nonblocking(size=1, timeout=timeout)  # pylint: disable=no-member
                # \r=0x0d CR \n=0x0a LF
                if char not in ['\n', '\r']:  # omit the cr/lf sent to get the prompt
                    timeout = inter_char_timeout
                expired = time() - begin
                prompt += char
            except pexpect.TIMEOUT:
                break
            except pexpect.EOF:
                raise ConnectionError('Session disconnected')

        prompt = prompt.strip()
        return prompt

    def detect_prompt(self, sync_multiplier=4):
        """Detect the prompt.

        This attempts to find the prompt. Basically, press enter and record
        the response; press enter again and record the response; if the two
        responses are similar then assume we are at the original prompt.
        This can be a slow function. Worst case with the default sync_multiplier
        can take 16 seconds. Low latency connections are more likely to fail
        with a low sync_multiplier. Best case sync time gets worse with a
        high sync multiplier (500 ms with default).

        """
        self.sendline()  # pylint: disable=no-member
        self.try_read_prompt(sync_multiplier)

        attempt = 0
        max_attempts = 10
        while attempt < max_attempts:
            attempt += 1
            logger.debug("Detecting prompt. Attempt ({}/{})".format(attempt, max_attempts))

            self.sendline()  # pylint: disable=no-member
            first = self.try_read_prompt(sync_multiplier)

            self.sendline()  # pylint: disable=no-member
            second = self.try_read_prompt(sync_multiplier)

            lhd = levenshtein_distance(first, second)
            len_first = len(first)
            logger.debug("LD={},MP={}".format(lhd, sync_multiplier))
            sync_multiplier *= 1.2
            if len_first == 0:
                continue

            if float(lhd) / len_first < 0.3:
                prompt = second.splitlines(True)[-1]
                logger.debug("Detected prompt: '{}'".format(prompt))
                compiled_prompt = re.compile("(\r\n|\n\r){}".format(re.escape(prompt)))
                self.sendline()  # pylint: disable=no-member
                self.expect(compiled_prompt)  # pylint: disable=no-member
                return prompt

        return None

    @property
    def is_connected(self):
        """Return the session state regardless of device connection state."""
        return self.connected and self._session and self._session.isalive()

    @property
    def before(self):
        """Return text up to the expected string pattern."""
        return self._session.before if self._session else None

    @property
    def after(self):
        """Return text that was matched by the expected pattern."""
        return self._session.after if self._session else None
