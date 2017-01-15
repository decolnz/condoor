"""This is IOS XR 64 bit driver implementation."""

from functools import partial
import re
import logging
import pexpect

from condoor.exceptions import CommandSyntaxError, CommandTimeoutError, ConnectionError
from condoor.actions import a_connection_closed, a_expected_prompt, a_stays_connected, a_unexpected_prompt, a_send, \
    a_store_cmd_result, a_message_callback, a_send_line, a_reconnect, a_send_boot
from condoor.utils import pattern_to_str
from condoor.fsm import FSM
from condoor.drivers.generic import Driver as Generic
from condoor import pattern_manager, EOF
from condoor.config import CONF

logger = logging.getLogger(__name__)

_C = CONF['driver']['eXR']


class Driver(Generic):
    """This is a Driver class implementation for IOS XR 64 bit."""

    platform = 'eXR'
    inventory_cmd = 'admin show inventory chassis'
    users_cmd = 'show users'
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'rommon', 'xml']
    prepare_terminal_session = ['terminal exec prompt no-timestamp', 'terminal len 0', 'terminal width 0']
    reload_cmd = 'admin hw-module location all reload'
    families = {
        "ASR9K": "ASR9K",
        "ASR-9": "ASR9K",
        "ASR9": "ASR9K",
        "NCS-6": "NCS6K",
        "NCS-4": "NCS4K",
        "NCS-50": "NCS5K",
        "NCS-55": "NCS5500",
        "NCS1": "NCS1K",
        "NCS-1": "NCS1K",
    }

    def __init__(self, device):
        """Initialize the XR 64 bit Driver object."""
        super(Driver, self).__init__(device)
        self.calvados_re = pattern_manager.pattern(self.platform, 'calvados')
        self.calvados_connect_re = pattern_manager.pattern(self.platform, 'calvados_connect')
        self.calvados_term_length = pattern_manager.pattern(self.platform, 'calvados_term_length')

    def get_version_text(self):
        """Return version information text."""
        version_text = self.device.send("show version", timeout=120)
        return version_text

    def update_driver(self, prompt):
        """Return driver name based on prompt analysis."""
        logger.debug(prompt)
        platform = pattern_manager.platform(prompt)
        # to avoid the XR platform detection as eXR and XR prompts are the same
        if platform == 'XR':
            platform = 'eXR'

        if platform:
            logger.debug('{} -> {}'.format(self.platform, platform))
            return platform
        else:
            logger.debug('No update: {}'.format(self.platform))
            return self.platform

    def wait_for_string(self, expected_string, timeout=60):
        """Wait for string FSM for XR 64 bit."""
        # Big thanks to calvados developers for make this FSM such complex ;-)
        #                    0                         1                        2                        3
        events = [self.syntax_error_re, self.connection_closed_re, expected_string, self.press_return_re,
                  #        4           5                 6                7               8
                  self.more_re, pexpect.TIMEOUT, pexpect.EOF, self.calvados_re, self.calvados_connect_re,
                  #     9
                  self.calvados_term_length]

        # add detected prompts chain
        events += self.device.get_previous_prompts()  # without target prompt

        logger.debug("Expecting: {}".format(pattern_to_str(expected_string)))
        logger.debug("Calvados prompt: {}".format(pattern_to_str(self.calvados_re)))

        transitions = [
            (self.syntax_error_re, [0], -1, CommandSyntaxError("Command unknown", self.device.hostname), 0),
            (self.connection_closed_re, [0], 1, a_connection_closed, 10),
            (pexpect.TIMEOUT, [0, 2], -1, CommandTimeoutError("Timeout waiting for prompt", self.device.hostname), 0),
            (pexpect.EOF, [0, 1], -1, ConnectionError("Unexpected device disconnect", self.device.hostname), 0),
            (self.more_re, [0], 0, partial(a_send, " "), 10),
            (expected_string, [0, 1], -1, a_expected_prompt, 0),
            (self.calvados_re, [0], -1, a_expected_prompt, 0),
            (self.press_return_re, [0], -1, a_stays_connected, 0),
            (self.calvados_connect_re, [0], 2, None, 0),
            # admin command to switch to calvados
            (self.calvados_re, [2], 3, None, _C['calvados_term_wait_time']),
            # getting the prompt only
            (pexpect.TIMEOUT, [3], 0, partial(a_send, "\r"), 0),
            # term len
            (self.calvados_term_length, [3], 4, None, 0),
            # ignore for command start
            (self.calvados_re, [4], 5, None, 0),
            # ignore for command start
            (self.calvados_re, [5], 0, a_store_cmd_result, 0),
        ]

        for prompt in self.device.get_previous_prompts():
            transitions.append((prompt, [0, 1], 0, a_unexpected_prompt, 0))

        fsm = FSM("WAIT-4-STRING", self.device, events, transitions, timeout=timeout)
        return fsm.run()

    def reload(self, reload_timeout, save_config):
        """Reload the device."""
        RELOAD_PROMPT = re.compile(re.escape("Reload hardware module ? [no,yes]"))
        START_TO_BACKUP = re.compile("Status report.*START TO BACKUP")
        BACKUP_HAS_COMPLETED_SUCCESSFULLY = re.compile("Status report.*BACKUP HAS COMPLETED SUCCESSFULLY")
        DONE = re.compile(re.escape("[Done]"))
        CONSOLE = re.compile("ios con[0|1]/(?:RS?P)?[0-1]/CPU0 is now available")
        CONFIGURATION_COMPLETED = re.compile("SYSTEM CONFIGURATION COMPLETED")
        CONFIGURATION_IN_PROCESS = re.compile("SYSTEM CONFIGURATION IN PROCESS")
        BOOTING = re.compile("Booting IOS-XR 64 bit Boot previously installed image")

        # events = [RELOAD_NA, DONE, PROCEED, CONFIGURATION_IN_PROCESS, self.rommon_re, self.press_return_re,
        #           #   6               7                       8                     9      10        11
        #           CONSOLE, CONFIGURATION_COMPLETED, RECONFIGURE_USERNAME_PROMPT, TIMEOUT, EOF, self.reload_cmd,
        #           #    12                    13                     14
        #           ROOT_USERNAME_PROMPT, ROOT_PASSWORD_PROMPT, CANDIDATE_BOOT_IMAGE]

        events = [self.reload_cmd, RELOAD_PROMPT, START_TO_BACKUP, BACKUP_HAS_COMPLETED_SUCCESSFULLY, DONE, BOOTING,
                  CONSOLE, self.press_return_re, CONFIGURATION_COMPLETED, CONFIGURATION_IN_PROCESS, EOF]

        transitions = [
            # do I really need to clean the cmd
            (RELOAD_PROMPT, [0], 1, partial(a_send_line, "yes"), 30),
            (START_TO_BACKUP, [1], 2, a_message_callback, 60),
            (BACKUP_HAS_COMPLETED_SUCCESSFULLY, [2], 3, a_message_callback, 10),
            (DONE, [3], 4, None, 600),
            (self.rommon_re, [0, 4], 5, partial(a_send_boot, "boot"), 600),
            (BOOTING, [0, 4], 5, a_message_callback, 600),
            (CONSOLE, [0, 5], 6, None, 600),
            (self.press_return_re, [6], 7, partial(a_send, "\r"), 300),
            (CONFIGURATION_IN_PROCESS, [7], 8, None, 180),
            (CONFIGURATION_COMPLETED, [8], -1, a_reconnect, 0),
            (EOF, [0, 1, 2, 3, 4, 5], -1, ConnectionError("Device disconnected"), 0),

            # (RELOAD_NA, [1], -1, a_reload_na, 0),
            # (DONE, [1], 2, None, 120),
            # (PROCEED, [2], 3, partial(a_send, "\r"), reload_timeout),
            # (self.rommon_re, [0, 3], 4, partial(a_send_boot, "boot"), 600),
            # (CANDIDATE_BOOT_IMAGE, [0, 3], 4, a_message_callback, 600),
            # (CONSOLE, [0, 1, 3, 4], 5, None, 600),
            # (self.press_return_re, [5], 6, partial(a_send, "\r"), 300),
            # # configure root username and password the same as used for device connection.
            # (RECONFIGURE_USERNAME_PROMPT, [6, 7], 8, None, 10),
            # (ROOT_USERNAME_PROMPT, [8], 9, partial(a_send_username, self.device.node_info.username), 1),
            # (ROOT_PASSWORD_PROMPT, [9], 9, partial(a_send_password, self.device.node_info.password), 1),
            # (CONFIGURATION_IN_PROCESS, [6, 9], 7, None, 180),
            # (CONFIGURATION_COMPLETED, [7], -1, a_reconnect, 0),
            # (TIMEOUT, [0, 1, 2], -1, ConnectionAuthenticationError("Unable to reload"), 0),
            # (EOF, [0, 1, 2, 3, 4, 5], -1, ConnectionError("Device disconnected"), 0),
            # (TIMEOUT, [6], 7, partial(a_send, "\r"), 180),
            # (TIMEOUT, [7], -1, ConnectionAuthenticationError("Unable to reconnect after reloading"), 0),
        ]

        fsm = FSM("RELOAD", self.device, events, transitions, timeout=600)
        return fsm.run()
