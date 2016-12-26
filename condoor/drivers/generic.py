"""This is generic driver class implementation."""

from functools import partial
import re
import logging
import pexpect

from condoor.actions import a_send, a_connection_closed, a_stays_connected, a_unexpected_prompt, a_expected_prompt
from condoor.fsm import FSM
from condoor.exceptions import ConnectionError, CommandError, CommandSyntaxError, CommandTimeoutError
from condoor.utils import pattern_to_str

from condoor import pattern_manager

logger = logging.getLogger(__name__)


class Driver(object):
    """This is generic Driver class implementation."""

    platform = 'generic'
    inventory_cmd = None
    users_cmd = None
    target_prompt_components = ['prompt_dynamic']
    prepare_terminal_session = ['terminal len 0']
    families = {}

    def __init__(self, device):
        """Initialize the Driver object."""
        self.device = device

        # FIXME: Do something with this, it's insane
        self.prompt_re = pattern_manager.pattern(self.platform, 'prompt')
        self.syntax_error_re = pattern_manager.pattern(self.platform, 'syntax_error')
        self.connection_closed_re = pattern_manager.pattern(self.platform, 'connection_closed')
        self.press_return_re = pattern_manager.pattern(self.platform, 'press_return')
        self.more_re = pattern_manager.pattern(self.platform, 'more')
        self.rommon_re = pattern_manager.pattern(self.platform, 'rommon')
        self.buffer_overflow_re = pattern_manager.pattern(self.platform, 'buffer_overflow')

        self.username_re = pattern_manager.pattern(self.platform, 'username')
        self.password_re = pattern_manager.pattern(self.platform, 'password')
        self.authentication_error_re = pattern_manager.pattern(self.platform, 'authentication_error')
        self.unable_to_connect_re = pattern_manager.pattern(self.platform, 'unable_to_connect')
        self.timeout_re = pattern_manager.pattern(self.platform, 'timeout')
        self.standby_re = pattern_manager.pattern(self.platform, 'standby')

        self.pid2platform_re = pattern_manager.pattern(self.platform, 'pid2platform')
        self.platform_re = pattern_manager.pattern(self.platform, 'platform', compiled=False)
        self.version_re = pattern_manager.pattern(self.platform, 'version', compiled=False)
        self.vty_re = pattern_manager.pattern(self.platform, 'vty')
        self.console_re = pattern_manager.pattern(self.platform, 'console')

    def __repr__(self):
        """Return the string representation of the driver class."""
        return str(self.platform)

    def get_version_text(self):
        """Return the version information from the device."""
        try:
            version_text = self.device.send("show version brief", timeout=120)
        except CommandError:
            # IOS Hack - need to check if show version brief is supported on IOS/IOS XE
            version_text = self.device.send("show version", timeout=120)
        return version_text

    def get_inventory_text(self):
        """Return the inventory information from the device."""
        inventory_text = None
        if self.inventory_cmd:
            try:
                inventory_text = self.device.send(self.inventory_cmd, timeout=120)
                logger.debug('Inventory collected')
            except CommandError:
                logger.debug('Unable to collect inventory')
        else:
            logger.debug('No inventory command for {}'.format(self.platform))
        return inventory_text

    def get_hostname_text(self):  # pylint: disable=no-self-use
        """Return the hostname information from the device."""
        return None

    def get_users_text(self):
        """Return the users logged in information from the device."""
        users_text = None
        if self.users_cmd:
            try:
                users_text = self.device.send(self.users_cmd, timeout=60)
            except CommandError:
                logger.debug('Unable to collect connected users information')
        else:
            logger.debug('No users command for {}'.format(self.platform))
        return users_text

    def get_os_type(self, version_text):  # pylint: disable=no-self-use
        """Return the OS type information from the device."""
        os_type = None
        if version_text is None:
            return os_type

        match = re.search("(XR|XE|NX-OS)", version_text)
        if match:
            os_type = match.group(1)
        else:
            os_type = 'IOS'

        if os_type == "XR":
            match = re.search("Build Information", version_text)
            if match:
                os_type = "eXR"
            match = re.search("XR Admin Software", version_text)
            if match:
                os_type = "Calvados"
        return os_type

    def get_os_version(self, version_text):
        """Return the OS version information from the device."""
        os_version = None
        if version_text is None:
            return os_version
        match = re.search(self.version_re, version_text, re.MULTILINE)
        if match:
            os_version = match.group(1)

        return os_version

    def get_hw_family(self, version_text):
        """Return the HW family information from the device."""
        family = None
        if version_text is None:
            return family

        match = re.search(self.platform_re, version_text, re.MULTILINE)
        if match:
            logger.debug("Platform string: {}".format(match.group()))
            family = match.group(1)
            for key, value in self.families.items():
                if family.startswith(key):
                    family = value
                    break
        else:
            logger.debug("Platform string not present. Refer to CSCux08958")
        return family

    def get_hw_platform(self, udi):
        """Return th HW platform information from the device."""
        platform = None
        try:
            pid = udi['pid']
            match = re.search(self.pid2platform_re, pid)
            if match:
                platform = match.group(1)
        except KeyError:
            pass
        return platform

    def is_console(self, users_text):
        """Return if device is connected over console."""
        if users_text is None:
            logger.debug("Console information not collected")
            return None

        for line in users_text.split('\n'):
            if '*' in line:
                match = re.search(self.vty_re, line)
                if match:
                    logger.debug("Detected connection to vty")
                    return False
                else:
                    match = re.search(self.console_re, line)
                    if match:
                        logger.debug("Detected connection to console")
                        return True

        logger.debug("Connection port unknown")
        return None

    def update_driver(self, prompt):
        """Update driver based on the prompt."""
        logger.debug(prompt)
        platform = pattern_manager.platform(prompt)
        if platform:
            logger.debug('{} -> {}'.format(self.platform, platform))
            return platform
        else:
            logger.debug('No update: {}'.format(self.platform))
            return self.platform

    def wait_for_string(self, expected_string, timeout=60):
        """Wait for string FSM."""
        #                    0                         1                        2                        3
        events = [self.syntax_error_re, self.connection_closed_re, expected_string, self.press_return_re,
                  #        4           5                 6                7
                  self.more_re, pexpect.TIMEOUT, pexpect.EOF, self.buffer_overflow_re]

        # add detected prompts chain
        events += self.device.get_previous_prompts()  # without target prompt

        logger.debug("Expecting: {}".format(pattern_to_str(expected_string)))

        transitions = [
            (self.syntax_error_re, [0], -1, CommandSyntaxError("Command unknown", self.device.hostname), 0),
            (self.connection_closed_re, [0], 1, a_connection_closed, 10),
            (pexpect.TIMEOUT, [0], -1, CommandTimeoutError("Timeout waiting for prompt", self.device.hostname), 0),
            (pexpect.EOF, [0, 1], -1, ConnectionError("Unexpected device disconnect", self.device.hostname), 0),
            (self.more_re, [0], 0, partial(a_send, " "), 10),
            (expected_string, [0, 1], -1, a_expected_prompt, 0),
            (self.press_return_re, [0], -1, a_stays_connected, 0),
            # TODO: Customize in XR driver
            (self.buffer_overflow_re, [0], -1, CommandSyntaxError("Command too long", self.device.hostname), 0)
        ]

        for prompt in self.device.get_previous_prompts():
            transitions.append((prompt, [0, 1], 0, a_unexpected_prompt, 0))

        fsm = FSM("WAIT-4-STRING", self.device, events, transitions, timeout=timeout)
        return fsm.run()

    # def send_xml(self, command, timeout=60):
    #     """
    #     Handle error i.e.
    #     ERROR: 0x24319600 'XML-TTY' detected the 'informational' condition
    #     'The XML TTY Agent has not yet been started.
    #     Check that the configuration 'xml agent tty' has been committed.'
    #     """
    #     self._debug("Starting XML TTY Agent")
    #     result = self.send("xml")
    #     self._info("XML TTY Agent started")
    #
    #     result = self.send(command, timeout=timeout)
    #     self.ctrl.sendcontrol('c')
    #     return result

    # def netconf(self, command):
    #     """
    #     Handle error i.e.
    #     ERROR: 0x24319600 'XML-TTY' detected the 'informational' condition
    #     'The XML TTY Agent has not yet been started.
    #     Check that the configuration 'xml agent tty' has been committed.'
    #     """
    #     self._debug("Starting XML TTY Agent")
    #     result = self.send("netconf", wait_for_string=']]>]]>')
    #     self._info("XML TTY Agent started")
    #
    #     self.ctrl.send(command)
    #     self.ctrl.send("\r\n")
    #     self.ctrl.expect("]]>]]>")
    #     result = self.ctrl.before
    #     self.ctrl.sendcontrol('c')
    #     self.send()
    #     return result

    def enable(self, enable_password):
        """Change the device mode to privileged.

        If device does not support privileged mode the
        the informational message to the log will be posted.

        Args:
            enable_password (str): The privileged mode password. This is optional parameter. If password is not
                provided but required the password from url will be used. Refer to :class:`condoor.Connection`
        """
        logger.info("Privileged mode not supported on {} platform".format(self.platform))

    def reload(self, reload_timeout=300, save_config=True):
        """Reload the device and waits for device to boot up.

        It posts the informational message to the log if not implemented by device driver.
        """
        logger.info("Reload not implemented on {} platform".format(self.platform))

    def after_connect(self):
        """Execute right after connecting to the device."""
        pass

    def base_prompt(self, prompt):
        """Extract the base prompt pattern."""
        if prompt is None:
            return None
        if not self.device.is_target:
            return prompt
        pattern = pattern_manager.pattern(self.platform, "prompt_dynamic", compiled=False)
        pattern = pattern.format(prompt="(?P<prompt>.*?)")
        result = re.search(pattern, prompt)
        if result:
            base = result.group("prompt") + "#"
            logger.debug("base prompt: {}".format(base))
            return base
        else:
            logger.error("Unable to extract the base prompt")
            return prompt

    def make_dynamic_prompt(self, prompt):
        """Extend prompt with flexible mode handling regexp."""
        patterns = [pattern_manager.pattern(
            self.platform, pattern_name, compiled=False) for pattern_name in self.target_prompt_components]

        patterns_re = "|".join(patterns).format(prompt=re.escape(prompt[:-1]))

        try:
            prompt_re = re.compile(patterns_re)
        except re.error as e:  # pylint: disable=invalid-name
            raise RuntimeError("Pattern compile error: {} ({}:{})".format(e.message, self.platform, patterns_re))

        logger.debug("Platform: {} -> Dynamic prompt: '{}'".format(self.platform, prompt_re.pattern))
        return prompt_re

    def update_config_mode(self, prompt):  # pylint: disable=no-self-use
        """Update config mode based on the prompt analysis."""
        if 'config' in prompt:
            mode = 'config'
        elif 'admin' in prompt:
            mode = 'admin'
        else:
            mode = 'global'

        logger.debug("Mode: {}".format(mode))
        return mode

    def update_hostname(self, prompt):
        """Update the hostname based on the prompt analusis."""
        result = re.search(self.prompt_re, prompt)
        if result:
            hostname = result.group('hostname')
            logger.debug("Hostname detected: {}".format(hostname))
        else:
            hostname = self.device.hostname
            logger.debug("Hostname not set: {}".format(prompt))
        return hostname
