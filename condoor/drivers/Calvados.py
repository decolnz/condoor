"""This is a Calvados driver implementation."""

import re
import logging
from condoor.drivers.generic import Driver as Generic
from condoor import pattern_manager

logger = logging.getLogger(__name__)


class Driver(Generic):
    """This is a Driver class implementation for Calvados."""

    platform = 'Calvados'
    inventory_cmd = 'show inventory chassis'
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'exr', 'windriver']
    prepare_terminal_session = ['terminal len 0', 'terminal width 0']
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
        """Initialize Calvados driver object."""
        super(Driver, self).__init__(device)

    def get_version_text(self):
        """Return the version information."""
        version_text = self.device.send('show version', timeout=60)
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

    def after_connect(self):
        """Execute after connect."""
        # TODO: check if this works.
        show_users = self.device.send("show users", timeout=120)
        result = re.search(pattern_manager.pattern(self.platform, 'connected_locally'), show_users)
        if result:
            logger.debug('Locally connected to Calvados. Exiting.')
            self.device.send('exit')
            return True
        return False
