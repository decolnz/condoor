"""This is a Wind River Linux driver implementation."""

import logging
from condoor.drivers.generic import Driver as Generic

logger = logging.getLogger(__name__)


class Driver(Generic):
    """This is a Driver class implementation for Wind River Linux."""

    platform = 'Windriver'
    inventory_cmd = None
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'calvados', 'lc']
    prepare_terminal_session = []
    families = {
    }

    def __init__(self, device):
        """Initialize the Wind River Linux driver object."""
        super(Driver, self).__init__(device)

    def get_version_text(self):
        """Return the version information."""
        version_text = self.device.send('cat /etc/issue', timeout=10)
        return version_text

    def get_os_type(self, version_text):
        """Return Windriver os type."""
        return 'Windriver'
