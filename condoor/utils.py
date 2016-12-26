"""Provides a set of functions nad clases for different purpose."""

import logging
import socket
import codecs
import time
import re
import os
import yaml


def delegate(attribute_name, method_names):
    """Pass the call to the attribute called attribute_name for every method listed in method_names."""
    # hack for python 2.7 as nonlocal is not available
    info = {
        'attribute': attribute_name,
        'methods': method_names
    }

    def decorator(cls):
        """Decorate class."""
        attribute = info['attribute']
        if attribute.startswith("__"):
            attribute = "_" + cls.__name__ + attribute
        for name in info['methods']:
            setattr(cls, name, eval("lambda self, *a, **kw: "
                                    "self.{0}.{1}(*a, **kw)".format(attribute, name)))
        return cls
    return decorator


def to_list(item):
    """Convert to list.

    If the given item is iterable, this function returns the given item.
    If the item is not iterable, this function returns a list with only the
    item in it.

    @type  item: object
    @param item: Any object.
    @rtype:  list
    @return: A list with the item in it.
    """
    if hasattr(item, '__iter__'):
        return item
    return [item]


def is_reachable(host, port=23):
    """Check reachability for specified hostname/port.

    It tries to open TCP socket.
    It supports IPv6.
    :param host: hostname or ip address string
    :rtype: str
    :param port: tcp port number
    :rtype: number
    :return: True if host is reachable else false
    """
    try:
        addresses = socket.getaddrinfo(
            host, port, socket.AF_UNSPEC, socket.SOCK_STREAM
        )
    except socket.gaierror:
        return False

    for family, _, _, _, sockaddr in addresses:
        sock = socket.socket(family, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect(sockaddr)
        except IOError:
            continue

        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
        # Wait 2 sec for socket to shutdown
        time.sleep(2)
        break
    else:
        return False
    return True


def pattern_to_str(pattern):
    """Convert regex pattern to string.

    If pattern is string it returns itself,
    if pattern is SRE_Pattern then return pattern attribute
    :param pattern: pattern object or string
    :return: str: pattern sttring
    """
    if isinstance(pattern, str):
        return pattern
    else:
        return pattern.pattern if pattern else None


def levenshtein_distance(str_a, str_b):
    """Calculate the Levenshtein distance between string a and b.

    :param str_a: String - input string a
    :param str_b: String - input string b
    :return: Number - Levenshtein Distance between string a and b
    """
    len_a, len_b = len(str_a), len(str_b)
    if len_a > len_b:
        str_a, str_b = str_b, str_a
        len_a, len_b = len_b, len_a
    current = range(len_a + 1)
    for i in range(1, len_b + 1):
        previous, current = current, [i] + [0] * len_a
        for j in range(1, len_a + 1):
            add, delete = previous[j] + 1, current[j - 1] + 1
            change = previous[j - 1]
            if str_a[j - 1] != str_b[i - 1]:
                change += + 1
            current[j] = min(add, delete, change)
    return current[len_a]


def parse_inventory(inventory_output=None):
    """Parse the inventory text and return udi dict."""
    udi = {
        "name": "",
        "description": "",
        "pid": "",
        "vid": "",
        "sn": ""
    }
    if inventory_output is None:
        return udi

    # find the record with chassis text in name or descr
    capture_next = False
    chassis_udi_text = None
    for line in inventory_output.split('\n'):
        lc_line = line.lower()
        if 'chassis' in lc_line and 'name' in lc_line and 'descr':
            capture_next = True
            chassis_udi_text = line
            continue
        if capture_next:
            inventory_output = chassis_udi_text + "\n" + line
            break

    match = re.search(r"(?i)NAME: (?P<name>.*?),? (?i)DESCR", inventory_output, re.MULTILINE)
    if match:
        udi['name'] = match.group('name').strip('" ,')

    match = re.search(r"(?i)DESCR: (?P<description>.*)", inventory_output, re.MULTILINE)
    if match:
        udi['description'] = match.group('description').strip('" ')

    match = re.search(r"(?i)PID: (?P<pid>.*?),? ", inventory_output, re.MULTILINE)
    if match:
        udi['pid'] = match.group('pid')

    match = re.search(r"(?i)VID: (?P<vid>.*?),? ", inventory_output, re.MULTILINE)
    if match:
        udi['vid'] = match.group('vid')

    match = re.search(r"(?i)SN: (?P<sn>.*)", inventory_output, re.MULTILINE)
    if match:
        udi['sn'] = match.group('sn')
    return udi


class FilteredFile(object):
    """Delegate class for handling filtered file object."""

    __slots__ = ['_file', '_pattern']

    def __init__(self, filename, mode="r", encoding=None, pattern=None):
        """Initialize FilteredFile object."""
        object.__setattr__(self, '_pattern', pattern)
        if encoding is None:
            object.__setattr__(self, '_file', open(filename, mode=mode))
        else:
            object.__setattr__(self, '_file', codecs.open(filename, mode=mode, encoding=encoding))

    def __getattr__(self, name):
        """Override standard getattr and delegate to file object."""
        return getattr(self._file, name)

    def __setattr__(self, name, value):
        """Override standard setattr and delegate to file object."""
        setattr(self._file, name, value)

    def write(self, text):
        """Override the standard write method to filter the content."""
        if self._pattern:
            # pattern already compiled no need to check
            result = re.search(self._pattern, text)
            if result:
                for group in result.groups():
                    if group:
                        text = text.replace(group, "***")
        self._file.write(text)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Custom context manager exit method."""
        self._file.close()

    def __enter__(self):
        """Custom context manager exit method."""
        return self


class FilteredFileHandler(logging.FileHandler):
    """Class defining custom FileHandler for filtering sensitive information."""

    def __init__(self, filename, mode='a', encoding="utf-8", delay=0, pattern=None):
        """Initialize the FilteredFileHandler object."""
        self.pattern = pattern
        self.encoding = encoding
        logging.FileHandler.__init__(self, filename, mode=mode, encoding=encoding, delay=delay)

    def _open(self):
        return FilteredFile(self.baseFilename, mode=self.mode, encoding=self.encoding, pattern=self.pattern)


def normalize_urls(urls):
    """Overload urls and make list of lists of urls."""
    _urls = []
    if isinstance(urls, list):
        if urls:
            if isinstance(urls[0], list):
                # multiple connections (list of the lists)
                _urls = urls
            elif isinstance(urls[0], str):
                # single connections (make it list of the lists)
                _urls = [urls]
        else:
            raise RuntimeError("No target host url provided.")
    elif isinstance(urls, str):
        _urls = [[urls]]
    return _urls


def make_handler(log_dir, log_level):
    """Make logging handler."""
    if log_level > 0:
        if log_level == logging.DEBUG:
            formatter = logging.Formatter('%(asctime)-15s [%(levelname)8s] %(name)s:'
                                          '%(funcName)s(%(lineno)d): %(message)s')
        else:
            formatter = logging.Formatter('%(asctime)-15s [%(levelname)8s]: %(message)s')
        if log_dir:
            # Create the log directory.
            if not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir)
                except IOError:
                    log_dir = "./"
            log_filename = os.path.join(log_dir, 'condoor.log')
            # FIXME: take pattern from pattern manager
            handler = FilteredFileHandler(log_filename, pattern=re.compile("s?ftp://.*:(.*)@"))
            # handler = logging.FileHandler(log_filename)

        else:
            handler = logging.StreamHandler()

        handler.setFormatter(formatter)
    else:
        handler = logging.NullHandler()

    return handler


def yaml_file_to_dict(script_name, path=None):
    """Read yaml file and return the dict.

    It assumes the module file exists with the defaults.
    If the CONDOOR_{SCRIPT_NAME} env is set then the user file from the env is loaded and merged with the default

    There can be user file located in ~/.condoor directory with the {script_name}.yaml filename. If exists
    it is merget with default config.
    """
    def load_yaml(file_path):
        """Load YAML file from full file path and return dict."""
        with open(file_path, 'r') as yamlfile:
            try:
                dictionary = yaml.load(yamlfile)
            except yaml.YAMLError:
                return {}
        return dictionary

    def merge(user, default):
        """Merge two dicts."""
        if isinstance(user, dict) and isinstance(default, dict):
            for k, v in default.iteritems():
                if k not in user:
                    user[k] = v
                else:
                    user[k] = merge(user[k], v)
            return user
        else:
            return default

    if path is None:
        path = os.path.abspath('.')

    config_file_path = os.path.join(path, script_name + '.yaml')
    if not os.path.exists(config_file_path):
        raise RuntimeError('Config file does not exist: {}'.format(config_file_path))

    default_dict = load_yaml(config_file_path)

    user_config_file_path = os.path.join(os.path.expanduser('~'), '.condoor', script_name + '.yaml')
    user_config_file_path = os.getenv('CONDOOR_' + script_name.upper(), user_config_file_path)

    if os.path.exists(user_config_file_path):
        user_dict = load_yaml(user_config_file_path)
        default_dict = merge(user_dict, default_dict)

    return default_dict
