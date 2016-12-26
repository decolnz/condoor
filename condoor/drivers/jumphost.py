"""This is jumphost driver class implementation."""

import re
import logging

from condoor.drivers.generic import Driver as Generic
from condoor import pattern_manager, CommandError

logger = logging.getLogger(__name__)


class Driver(Generic):
    """This is a Driver class implementation for Unix Jumphost."""

    platform = 'jumphost'
    inventory_cmd = None
    target_prompt_components = ['prompt_dynamic']
    prepare_terminal_session = []

    def __init__(self, device):
        """Initialize the Unix Jumphost driver object."""
        super(Driver, self).__init__(device)

    def get_version_text(self):
        """Return the version information from Unix host."""
        version_text = self.device.send('uname -sr', timeout=10)
        return version_text

    def update_hostname(self, prompt):
        """Return the hostname."""
        return self.device.hostname

    def get_hostname_text(self):
        """Return hostname information from the Unix host."""
        # FIXME: fix it, too complex logic
        try:
            hostname_text = self.device.send('hostname', timeout=10)
            if hostname_text:
                self.device.hostname = hostname_text.splitlines()[0]
                return hostname_text
        except CommandError:
            return None

    def make_dynamic_prompt(self, prompt):
        """Extend prompt with flexible mode handling regexp."""
        patterns = [pattern_manager.pattern(
            self.platform, pattern_name, compiled=False) for pattern_name in self.target_prompt_components]

        patterns_re = "|".join(patterns).format(prompt=re.escape(prompt))

        try:
            prompt_re = re.compile(patterns_re)
        except re.error as e:  # pylint: disable=invalid-name
            raise RuntimeError("Pattern compile error: {} ({}:{})".format(e.message, self.platform, patterns_re))

        logger.debug("Dynamic prompt: '{}'".format(prompt_re.pattern))
        return prompt_re
