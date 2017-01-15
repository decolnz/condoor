"""This is IOS XRv driver implementation."""

import logging
from condoor.drivers.XR import Driver as XR

logger = logging.getLogger(__name__)


class Driver(XR):
    """This is a Driver class implementation for IOS XRv."""

    platform = 'XRv'
    inventory_cmd = 'admin show inventory chassis'
    users_cmd = 'show users'
    target_prompt_components = ['prompt_dynamic', 'prompt_default', 'rommon', 'xml']
    prepare_terminal_session = ['terminal exec prompt no-timestamp', 'terminal len 0', 'terminal width 0']
    reload_cmd = 'admin reload location all'
    families = {
        "XRv": "IOS-XRv",
    }
