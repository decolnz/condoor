"""Provides the PatternManager class."""

import os
import re
from utils import yaml_file_to_dict


class PatternManager(object):
    """Provides API to patterns defined externally."""

    def __init__(self, pattern_dict):
        """Initialize PatternManager object."""
        self._dict = pattern_dict
        self._dict_compiled, self._dict_text, self._dict_dscr = self._prepare_patterns(pattern_dict)

    def _prepare_patterns(self, pattern_dict):
        """Return two dictionaries: compiled and text prompts."""
        dict_compiled = {}
        dict_text = {}
        dict_dscr = {}
        for platform, patterns in pattern_dict.items():
            dict_text[platform] = {}
            dict_compiled[platform] = {}
            dict_dscr[platform] = {}

            for key, pattern in patterns.items():
                try:
                    text_pattern = None
                    compiled_pattern = None
                    description_pattern = None

                    if isinstance(pattern, str):
                        text_pattern = pattern
                        compiled_pattern = re.compile(text_pattern, re.MULTILINE)
                        description_pattern = key

                    elif isinstance(pattern, dict):
                        text_pattern = pattern['pattern']
                        compiled_pattern = re.compile(text_pattern, re.MULTILINE)
                        description_pattern = pattern['description']

                    elif isinstance(pattern, list):
                        text_pattern = self._concatenate_patterns(key, pattern)
                        compiled_pattern = re.compile(text_pattern, re.MULTILINE)
                        description_pattern = key

                    dict_text[platform][key] = text_pattern
                    dict_compiled[platform][key] = compiled_pattern
                    dict_dscr[platform][key] = description_pattern

                except re.error as e:
                    raise RuntimeError("Pattern compile error: {} ({}:{})".format(e.message, platform, key))

        return dict_compiled, dict_text, dict_dscr

    def _platform_patterns(self, platform='generic', compiled=False):
        """Return all the patterns for specific platform."""
        patterns = self._dict_compiled.get(platform, None) if compiled else self._dict_text.get(platform, None)
        if patterns is None:
            raise KeyError("Unknown platform: {}".format(platform))
        return patterns

    def _concatenate_patterns(self, key, patterns):
        pattern_set = set()
        for platform in patterns:
            try:
                pattern = self._dict.get(platform, None)[key]
                if isinstance(pattern, dict):
                    pattern = pattern.get('pattern', None)

                pattern_set |= set(pattern.split('|'))
            except (KeyError, TypeError):
                continue
        return "|".join(pattern_set)

    def pattern(self, platform, key, compiled=True):
        """Return the pattern defined by the key string specific to the platform.

        :param platform:
        :param key:
        :param compiled:
        :return: Pattern string or RE object.
        """
        patterns = self._platform_patterns(platform, compiled=compiled)
        pattern = patterns.get(key, self._platform_patterns(compiled=compiled).get(key, None))

        if pattern is None:
            raise KeyError("Patterns database corrupted. Platform: {}, Key: {}".format(platform, key))

        if compiled:
            return re.compile(pattern)
        else:
            return pattern

    def description(self, platform, key):
        """Return the patter description."""
        patterns = self._dict_dscr.get(platform, None)
        description = patterns.get(key, None)
        return description

    def platform(self, with_prompt):
        """Return the platform name based on the prompt matching."""
        platforms = self._dict['generic']['prompt_detection']
        for platform in platforms:
            pattern = self.pattern(platform, 'prompt')
            result = re.search(pattern, with_prompt)
            if result:
                return platform
        return None


class YPatternManager(PatternManager):
    """Yaml version of pattern manager."""

    def __init__(self):
        """Initialize the pattern manager object."""
        script_name = os.path.splitext(__file__)[0]
        path = os.path.abspath('./')
        super(YPatternManager, self).__init__(pattern_dict=yaml_file_to_dict(script_name, path))

# ypm = YPatternManager()
# from pprint import pprint
# pprint(ypm._dict_compiled)
# pprint(ypm._dict_text)
# pprint(ypm.pattern('eXR', 'prompt'))
# pprint(ypm.pattern('eXR', 'prompt', compiled=False))
#
# pprint(ypm.pattern('eXR', 'press_return'))
# pprint(ypm.pattern('eXR', 'press_return', compiled=False))
#
# pattern = ypm.pattern('eXR', 'press_return')
# print(re.search(pattern, "Press RETURN to get started."))
#
# description = ypm.description('eXR', 'syntax_error')
# print(description)

# p = ypm.get_pattern('generic', "syntax_error")
# pprint(p.pattern)

# print(ypm.get_platform_based_on_prompt('[sysadmin-vm:0_RSP0:~]$'))
# print(ypm.get_platform_based_on_prompt('sysadmin-vm:0_RSP0#'))

# print(ypm.get_pattern("generic", "syntax_error", compiled=False))
# print(ypm.get_pattern("generic", "syntax_error").pattern)

# print(ypm._get_all_patterns('rommon').pattern)

# print(ypm._get_all_patterns('rommon', compiled=False))

# print(ypm._get_all_patterns('dupa'))

# print(ypm.get_pattern("XR", "connection_closed", compiled=False))
# print(ypm.get_pattern("XR", "standby_console", compiled=False))
