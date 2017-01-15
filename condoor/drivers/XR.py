"""This is IOS XR Classic driver implementation."""

from functools import partial
import re
import logging
from condoor.drivers.generic import Driver as Generic
from condoor import TIMEOUT, EOF, ConnectionAuthenticationError, ConnectionError
from condoor.fsm import FSM
from condoor.actions import a_reload_na, a_send, a_send_boot, a_reconnect, a_send_username, a_send_password,\
    a_message_callback

logger = logging.getLogger(__name__)


class Driver(Generic):
    """This is a Driver class implementation for IOS XR Classic."""

    platform = 'XR'
    inventory_cmd = 'admin show inventory chassis'
    users_cmd = 'show users'
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'rommon', 'xml']
    prepare_terminal_session = ['terminal exec prompt no-timestamp', 'terminal len 0', 'terminal width 0']
    reload_cmd = 'admin reload location all'
    families = {
        "ASR9K": "ASR9K",
        "ASR-9": "ASR9K",
        "CRS": "CRS",
    }

    def __init__(self, device):
        """Initialize the IOS XR Classic driver object."""
        super(Driver, self).__init__(device)

    def reload(self, reload_timeout, save_config):
        """Reload the device."""
        PROCEED = re.compile(re.escape("Proceed with reload? [confirm]"))
        DONE = re.compile(re.escape("[Done]"))
        CONFIGURATION_COMPLETED = re.compile("SYSTEM CONFIGURATION COMPLETED")
        CONFIGURATION_IN_PROCESS = re.compile("SYSTEM CONFIGURATION IN PROCESS")

        # CONSOLE = re.compile("ios con[0|1]/RS?P[0-1]/CPU0 is now available")
        CONSOLE = re.compile("ios con[0|1]/(?:RS?P)?[0-1]/CPU0 is now available")
        RECONFIGURE_USERNAME_PROMPT = "[Nn][Oo] root-system username is configured"
        ROOT_USERNAME_PROMPT = "Enter root-system username\: "
        ROOT_PASSWORD_PROMPT = "Enter secret( again)?\: "

        # BOOT=disk0:asr9k-os-mbi-6.1.1/0x100305/mbiasr9k-rsp3.vm,1; \
        # disk0:asr9k-os-mbi-5.3.4/0x100305/mbiasr9k-rsp3.vm,2;
        # Candidate Boot Image num 0 is disk0:asr9k-os-mbi-6.1.1/0x100305/mbiasr9k-rsp3.vm
        # Candidate Boot Image num 1 is disk0:asr9k-os-mbi-5.3.4/0x100305/mbiasr9k-rsp3.vm
        CANDIDATE_BOOT_IMAGE = "Candidate Boot Image num 0 is .*vm"

        RELOAD_NA = re.compile("Reload to the ROM monitor disallowed from a telnet line")
        #           0          1      2                3                   4                  5
        events = [RELOAD_NA, DONE, PROCEED, CONFIGURATION_IN_PROCESS, self.rommon_re, self.press_return_re,
                  #   6               7                       8                     9      10        11
                  CONSOLE, CONFIGURATION_COMPLETED, RECONFIGURE_USERNAME_PROMPT, TIMEOUT, EOF, self.reload_cmd,
                  #    12                    13                     14
                  ROOT_USERNAME_PROMPT, ROOT_PASSWORD_PROMPT, CANDIDATE_BOOT_IMAGE]

        transitions = [
            (RELOAD_NA, [0], -1, a_reload_na, 0),
            (DONE, [0], 2, None, 120),
            (PROCEED, [2], 3, partial(a_send, "\r"), reload_timeout),
            # this needs to be verified
            (self.rommon_re, [0, 3], 3, partial(a_send_boot, "boot"), 600),
            (CANDIDATE_BOOT_IMAGE, [0, 3], 4, a_message_callback, 600),
            (CONSOLE, [0, 1, 3, 4], 5, None, 600),
            (self.press_return_re, [5], 6, partial(a_send, "\r"), 300),
            # configure root username and password the same as used for device connection.
            (RECONFIGURE_USERNAME_PROMPT, [6, 7], 8, None, 10),
            (ROOT_USERNAME_PROMPT, [8], 9, partial(a_send_username, self.device.node_info.username), 1),
            (ROOT_PASSWORD_PROMPT, [9], 9, partial(a_send_password, self.device.node_info.password), 1),
            (CONFIGURATION_IN_PROCESS, [6, 9], 7, None, 180),
            (CONFIGURATION_COMPLETED, [7], -1, a_reconnect, 0),
            (TIMEOUT, [0, 1, 2], -1, ConnectionAuthenticationError("Unable to reload"), 0),
            (EOF, [0, 1, 2, 3, 4, 5], -1, ConnectionError("Device disconnected"), 0),
            (TIMEOUT, [6], 7, partial(a_send, "\r"), 180),
            (TIMEOUT, [7], -1, ConnectionAuthenticationError("Unable to reconnect after reloading"), 0),
        ]

        fsm = FSM("RELOAD", self.device, events, transitions, timeout=600)
        return fsm.run()
