"""Provides the condoor configuration."""

import os
from utils import yaml_file_to_dict


class YConfig(dict):
    """Yamal configuration file interface."""

    def __init__(self):
        """Initialize the pattern manager object."""
        script_name = os.path.splitext(__file__)[0]
        path = os.path.abspath('./')
        super(YConfig, self).__init__(yaml_file_to_dict(script_name, path))


CONF = YConfig()
