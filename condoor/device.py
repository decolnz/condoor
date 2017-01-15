"""Provides Device class representing the physical device for both target and jumphost."""

import sys
import logging
import pexpect

from condoor.exceptions import ConnectionError, CommandSyntaxError, CommandTimeoutError
from condoor.utils import parse_inventory
from condoor.fsm import FSM

logger = logging.getLogger(__name__)


class Device(object):
    """Device class representing physical device for both target and jumphost."""

    def __init__(self, chain, node_info, driver_name='jumphost', is_target=False):
        """Initialize Device object."""
        self.chain = chain
        self.hostname = "{}:{}".format(node_info.hostname, node_info.port)  # used by driver

        self.node_info = node_info
        self.ctrl = None

        # information whether the device is connected to the console
        self.is_console = False

        # True is last device in the chain
        self.is_target = is_target

        # prompt
        self.prompt = None
        self.prompt_re = None

        # properties with getter to collect in case None
        # version_text
        self._version_text = None

        # inventory_text
        self._inventory_text = None

        # hostname_text
        self._hostname_text = None

        # show users text
        self._users_text = None

        # set if device is connect
        self.connected = False

        self.mode = None

        self.protocol = None
        self.driver = self.make_driver(driver_name)

        self.os_version = None
        self.os_type = None
        self.family = None
        self.platform = None
        self.udi = None
        self.is_console = None

        self.last_command_result = None

        self.last_error_msg = None

    @property
    def device_info(self):
        """Return device info dict."""
        return {
            'family': self.family,
            'platform': self.platform,
            'os_type': self.os_type,
            'os_version': self.os_version,
            'udi': self.udi,
            # TODO(klstanie): add property to make driver automatically
            'driver_name': self.driver.platform,
            'mode': self.mode,
            'is_console': self.is_console,
            'is_target': self.is_target,
            'prompt': self.driver.base_prompt(self.prompt),
            'hostname': self.hostname,
        }

    @device_info.setter
    def device_info(self, info):
        for key, value in info.items():
            logger.debug("Update: [{}] {}<-{}".format(self, key, value))
            setattr(self, key, value)

    def __repr__(self):
        """Return string representing node info."""
        return str(self.node_info)

    def clear_info(self):
        """Clear the device info."""
        self._version_text = None
        self._inventory_text = None
        self._users_text = None
        self.os_version = None
        self.os_type = None
        self.family = None
        self.platform = None
        self.udi = None
        # self.is_console = None
        self.prompt = None
        self.prompt_re = None

    def connect(self, ctrl):
        """Connect to the device."""
        if self.prompt:
            self.prompt_re = self.driver.make_dynamic_prompt(self.prompt)
        else:
            self.prompt_re = self.driver.prompt_re

        self.ctrl = ctrl
        if self.protocol.connect(self.driver):
            if self.protocol.authenticate(self.driver):
                self.ctrl.try_read_prompt(1)
                if not self.prompt:
                    self.prompt = self.ctrl.detect_prompt()

                if self.is_target:
                    self.update_config_mode()
                    if self.mode is not None and self.mode != 'global':
                        self.last_error_msg = "Device is not in global mode. Disconnected."
                        self.chain.disconnect()
                        return False

                self.prompt_re = self.driver.make_dynamic_prompt(self.prompt)
                self.connected = True

                if self.is_target is False:
                    if self.os_version is None:
                        self.update_os_version()

                    self.update_hostname()
                else:
                    self._connected_to_target()
                return True

        else:
            self.connected = False
            return False

    def _connected_to_target(self):
        self.update_driver(self.prompt)
        self.after_connect()

        try:
            self.prepare_terminal_session()
        except CommandSyntaxError:
            pass

        if self.os_type is None:
            self.update_os_type()

        self.driver_name = self.os_type

        if self.os_version is None:
            self.update_os_version()

        # delegate to device
        self.prompt_re = self.driver.make_dynamic_prompt(self.prompt)

        # self.prepare_terminal_session()

        if self.udi is None:
            self.update_udi()

        if self.family is None:
            self.update_family()

        if self.platform is None:
            self.update_platform()

        if self.is_console is None:
            self.update_console()

        self.enable(self._get_enable_password())

    def _get_enable_password(self):
        return self.node_info.enable_password if self.node_info.enable_password else self.node_info.password

    def disconnect(self):
        """Disconnect the device."""
        if self.connected:
            if self.protocol:
                self.protocol.disconnect(self.driver)
                self.protocol = None
            if self.ctrl:
                self.ctrl = None

    def send(self, cmd="", timeout=60, wait_for_string=None):
        """Send the command to the device and return the output.

        Args:
            cmd (str): Command string for execution. Defaults to empty string.
            timeout (int): Timeout in seconds. Defaults to 60s
            wait_for_string (str): This is optional string that driver
                waits for after command execution. If none the detected
                prompt will be used.

        Returns:
            A string containing the command output.

        Raises:
            ConnectionError: General connection error during command execution
            CommandSyntaxError: Command syntax error or unknown command.
            CommandTimeoutError: Timeout during command execution
        """
        if self.connected:
            output = ''
            logger.debug("Sending command: '{}'".format(cmd))

            try:
                output = self.execute_command(cmd, timeout, wait_for_string)
            except ConnectionError:
                logger.error("Connection lost. Disconnecting.")
                # self.disconnect()
                raise

            logger.info("Command executed successfully: '{}'".format(cmd))
            return output

        else:
            raise ConnectionError("Device not connected", host=self.hostname)

    def execute_command(self, cmd, timeout, wait_for_string):
        """Execute command."""
        try:
            self.last_command_result = None
            self.ctrl.send_command(cmd)
            if wait_for_string is None:
                wait_for_string = self.prompt_re

            if not self.driver.wait_for_string(wait_for_string, timeout):
                logger.error("Unexpected session disconnect during '{}' "
                             "command execution".format(cmd))
                raise ConnectionError("Unexpected session disconnect", host=self.hostname)

            if self.last_command_result:
                output = self.last_command_result.replace('\r', '')
            else:
                output = self.ctrl.before.replace('\r', '')

            second_line_index = output.find('\n') + 1
            output = output[second_line_index:]
            return output

        except CommandSyntaxError as e:  # pylint: disable=invalid-name
            logger.error("{}: '{}'".format(e.message, cmd))
            e.command = cmd
            raise e

        except (CommandTimeoutError, pexpect.TIMEOUT):
            logger.error("Command timeout: '{}'".format(cmd))
            raise CommandTimeoutError(message="Command timeout", host=self.hostname, command=cmd)

        except ConnectionError as e:  # pylint: disable=invalid-name
            logger.error("{}: '{}'".format(e.message, cmd))
            raise

        except pexpect.EOF:
            logger.error("Unexpected session disconnect")
            raise ConnectionError("Unexpected session disconnect", host=self.hostname)

        except Exception as e:  # pylint: disable=invalid-name
            logger.critical("Exception", exc_info=True)
            raise ConnectionError(message="Unexpected error", host=self.hostname)

    @property
    def driver_name(self):
        """Return driver name or None."""
        return None if self.driver is None else self.driver.platform

    @driver_name.setter
    def driver_name(self, driver_name):
        if self.driver is None or driver_name != self.driver.platform:
            self.driver = self.make_driver(driver_name)
            logger.debug("{}".format(self.driver.platform))
            self.make_dynamic_prompt(self.prompt)

    def make_driver(self, driver_name='generic'):
        """Factory function to make driver."""
        module_str = 'condoor.drivers.%s' % driver_name
        try:
            __import__(module_str)
            module = sys.modules[module_str]
            driver_class = getattr(module, 'Driver')
        except ImportError as e:  # pylint: disable=invalid-name
            logger.critical("Import error", exc_info=e)
            return self.make_driver()
            # raise GeneralError("Platform {} not supported".format(driver_name))

        logger.debug("Make Device: {} with Driver: {}".format(self, driver_class.platform))
        return driver_class(self)

    def get_previous_prompts(self):
        """Return list of prompts from all devices except target."""
        return self.chain.get_previous_prompts(self)

    @property
    def version_text(self):
        """Return version text and collect if not available."""
        if self._version_text is None:
            logger.debug("Collecting version information")
            self._version_text = self.driver.get_version_text()
            if self._version_text:
                logger.debug("Version info collected")
            else:
                logger.warn("Version info not collected")

        return self._version_text

    @property
    def hostname_text(self):
        """Return hostname text and collect if not available."""
        if self._hostname_text is None:
            logger.debug("Collecting hostname information")
            self._hostname_text = self.driver.get_hostname_text()
            if self._hostname_text:
                logger.debug("Hostname info collected")
            else:
                logger.warn("Hostname info not collected")
        return self._hostname_text

    @property
    def inventory_text(self):
        """Return inventory information and collect if not available."""
        if self._inventory_text is None:
            logger.debug("Collecting inventory information")
            self._inventory_text = self.driver.get_inventory_text()
            if self._inventory_text:
                logger.debug("Inventory info collected")
            else:
                logger.warn("Inventory info not collected")
        return self._inventory_text

    @property
    def users_text(self):
        """Return connected users information and collect if not available."""
        if self._users_text is None:
            logger.debug("Getting connected users text")
            self._users_text = self.driver.get_users_text()
            if self._users_text:
                logger.debug("Users text collected")
            else:
                logger.warn("Users text not collected")
        return self._users_text

    def get_protocol_name(self):
        """Provide protocol name based on node_info."""
        protocol_name = self.node_info.protocol
        if self.is_console:
            protocol_name += '_console'
        return protocol_name

    def make_dynamic_prompt(self, prompt):
        """Extend prompt with flexible mode handling regexp."""
        if prompt:
            self.prompt_re = self.driver.make_dynamic_prompt(prompt)

    def update_udi(self):
        """Update udi."""
        logger.debug("Parsing inventory")
        # TODO: Maybe validate if udi is complete
        self.udi = parse_inventory(self.inventory_text)

    def update_config_mode(self, prompt=None):
        """Update config mode."""
        # TODO: Fix the conflict with config mode attribute at connection
        if prompt:
            self.mode = self.driver.update_config_mode(prompt)
        else:
            self.mode = self.driver.update_config_mode(self.prompt)

    def update_hostname(self):
        """Update hostname."""
        self.hostname = self.driver.update_hostname(self.prompt)

    def update_driver(self, prompt):
        """Update driver based on new prompt."""
        logger.debug("{}: New prompt '{}'".format(self.driver.platform, prompt))
        self.prompt = prompt
        self.driver_name = self.driver.update_driver(prompt)

    def prepare_terminal_session(self):
        """Send commands to prepare terminal session configuration."""
        for cmd in self.driver.prepare_terminal_session:
            self.send(cmd)

    def update_os_type(self):
        """Update os_type attribute."""
        os_type = self.driver.get_os_type(self.version_text)
        if os_type:
            logger.debug("SW Type: {}".format(os_type))
            self.os_type = os_type

    def update_os_version(self):
        """Update os_version attribute."""
        os_version = self.driver.get_os_version(self.version_text)
        if os_version:
            logger.debug("SW Version: {}".format(os_version))
            self.os_version = os_version

    def update_family(self):
        """Update family attribute."""
        family = self.driver.get_hw_family(self.version_text)
        if family:
            logger.debug("HW Family: {}".format(family))
            self.family = family

    def update_platform(self):
        """Update platform attribute."""
        platform = self.driver.get_hw_platform(self.udi)
        if platform:
            logger.debug("HW Platform: {}".format(platform))
            self.platform = platform

    def update_console(self):
        """Update is_console whether connected via console."""
        is_console = self.driver.is_console(self.users_text)
        if is_console is not None:
            self.is_console = is_console

    def after_connect(self):
        """Execute right after connect."""
        return self.driver.after_connect()

    def enable(self, enable_password):
        """Set privilege mode."""
        self.driver.enable(enable_password)

    def reload(self, reload_timeout, save_config, no_reload_cmd):
        """Reload device."""
        if not no_reload_cmd:
            self.ctrl.send_command(self.driver.reload_cmd)
        self.driver.reload(reload_timeout, save_config)

    def run_fsm(self, name, command, events, transitions, timeout, max_transitions=20):
        """Wrap the FSM code."""
        self.ctrl.send_command(command)
        return FSM(name, self, events, transitions, timeout=timeout, max_transitions=max_transitions).run()
