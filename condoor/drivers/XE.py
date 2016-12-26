"""This is IOS XE driver implementation."""

import logging

from condoor.drivers.IOS import Driver as IOSDriver
from condoor import pattern_manager

logger = logging.getLogger(__name__)


# based on IOS driver
class Driver(IOSDriver):
    """This is a Driver class implementation for IOS XR."""

    platform = 'XE'
    families = {
        "ASR-9": "ASR900",
    }

    def __init__(self, device):
        """Initialize the IOS XE driver object."""
        super(Driver, self).__init__(device)

    def update_driver(self, prompt):
        """Return driver name based on prompt analysis."""
        logger.debug(prompt)
        platform = pattern_manager.platform(prompt)
        # to avoid the XE platform detection as IOS and XE and IOS prompts are the same
        if platform == 'IOS':
            platform = 'XE'

        if platform:
            logger.debug('{} -> {}'.format(self.platform, platform))
            return platform
        else:
            logger.debug('No update: {}'.format(self.platform))
            return self.platform
