"""This provides the base Protocol class implementation."""

import logging

logger = logging.getLogger(__name__)


class Protocol(object):
    """Base Protocol class implementation."""

    def __init__(self, device):
        """Initialize the protocol object."""
        self.device = device
        self.port = self.device.node_info.port
        self.password = self.device.node_info.password
        self.username = self.device.node_info.username

        self.last_pattern = None
        self.matched_string = None

    def connect(self, driver):
        """Connect using specific protocol."""
        raise NotImplementedError("Connection method not implemented")

    def authenticate(self, driver):
        """Authenticate using specific protocol."""
        raise NotImplementedError("Authentication method not implemented")

    def disconnect(self, driver):
        """Disconnect using specific protocol."""
        raise NotImplementedError("Disconnect method not implemented")

    @property
    def hostname(self):
        """Return hostname from url."""
        return self.device.node_info.hostname

    def _acquire_password(self):
        # TODO: Remove
        password = self.password
        # if not password:
        #     if self.account_manager:
        #         self._dbg(20,
        #                   "{}: {}: Acquiring password for {} from system KeyRing".format(
        #                       self.protocol, self.hostname, self.username))
        #         password = self.account_manager.get_password(self.hostname, self.username, interact=True)
        #         if not password:
        #             self._dbg(30, "{}: {}: Password for {} does not exists in KeyRing".format(
        #                 self.protocol, self.hostname, self.username))
        return password
