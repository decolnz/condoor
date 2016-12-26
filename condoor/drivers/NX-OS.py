"""This is NX-OS driver class implementation."""

import logging

from condoor.drivers.generic import Driver as Generic
from condoor import pattern_manager

logger = logging.getLogger(__name__)


class Driver(Generic):
    """This is a Driver class implementation for NX-OS."""

    platform = 'NX-OS'
    inventory_cmd = 'show inventory chassis'
    users_cmd = 'show users'
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'rommon']
    prepare_terminal_session = ['terminal len 0', 'terminal width 511']
    # N9K-C9508
    families = {
        "Nexus9": "N9K",
        "N9K-C9": "N9K",
    }

    def __init__(self, device):
        """Initialize the NX-OS driver object."""
        super(Driver, self).__init__(device)

    def get_version_text(self):
        """Return the version information from NX-OS device."""
        version_text = self.device.send("show version", timeout=120)
        return version_text

    def update_driver(self, prompt):
        """Return driver name based on prompt analysis."""
        logger.debug(prompt)
        platform = pattern_manager.platform(prompt)
        if platform == 'IOS':
            platform = 'NX-OS'

        if platform:
            logger.debug('{} -> {}'.format(self.platform, platform))
            return platform
        else:
            logger.debug('No update: {}'.format(self.platform))
            return self.platform

    def reload(self, save_config=True):
        """Reload the device.

        !!!WARNING! there is unsaved configuration!!!
        This command will reboot the system. (y/n)?  [n]
        """
        if save_config:
            self.device.send("copy running-config startup-config")
        self.device("reload", wait_for_string="This command will reboot the system")
        self.device.ctrl.sendline("y")
