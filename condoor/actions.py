"""Provides predefined actions for Finite State Machines."""
import logging
from condoor.fsm import action
from condoor.exceptions import ConnectionAuthenticationError, ConnectionError, ConnectionTimeoutError


@action
def a_send_line(text, ctx):
    """Send text line to the controller followed by `os.linesep`."""
    ctx.ctrl.sendline(text)
    return True


@action
def a_send(text, ctx):
    """Send text line to the controller."""
    ctx.ctrl.send(text)
    return True


@action
def a_send_username(username, ctx):
    """Sent the username text."""
    if username:
        ctx.ctrl.sendline(username)
        return True
    else:
        ctx.ctrl.disconnect()
        raise ConnectionAuthenticationError("Username not provided", ctx.ctrl.hostname)


@action
def a_send_password(password, ctx):
    """Send the password text.

    Before sending the password local echo is disabled.
    If password not provided it disconnects from the device and raises ConnectionAuthenticationError exception.
    """
    if password:
        # ctx.ctrl.setecho(False)
        ctx.ctrl.sendline(password)
        # ctx.ctrl.setecho(True)
        return True
    else:
        ctx.ctrl.disconnect()
        raise ConnectionAuthenticationError("Password not provided", ctx.ctrl.hostname)


@action
def a_authentication_error(ctx):
    """Raise ConnectionAuthenticationError exception and disconnect."""
    ctx.ctrl.disconnect()
    raise ConnectionAuthenticationError("Authentication failed", ctx.ctrl.hostname)


@action
def a_unable_to_connect(ctx):
    """Provide detailed information about the session (before, after) when unable to connect.

    The state machine finishes without exception
    """
    message = "{}{}".format(ctx.ctrl.before, ctx.ctrl.after)
    ctx.msg = message.strip().splitlines()[-1]
    ctx.device.last_error_msg = ctx.msg
    # ctx.msg = "{}{}".format(ctx.ctrl.before, ctx.ctrl.after)
    return False


@action
def a_standby_console(ctx):
    """Raise ConnectionError exception when connected to standby console."""
    ctx.device.is_console = True
    raise ConnectionError("Standby console", ctx.ctrl.hostname)


@action
def a_disconnect(ctx):
    """Disconnect from the device when device is reloading."""
    ctx.msg = "Device is reloading"
    ctx.ctrl.disconnect()
    return True


@action
def a_reload_na(ctx):
    """Provide the message when the reload is not possible."""
    ctx.msg = "Reload to the ROM monitor disallowed from a telnet line. " \
              "Set the configuration register boot bits to be non-zero."
    ctx.failed = True
    return False


@action
def a_connection_closed(ctx):
    """Provide message when connection is closed by remote host."""
    ctx.msg = "Device disconnected"
    ctx.device.connected = False
    # do not stop FSM to detect the jumphost prompt
    return True


@action
def a_stays_connected(ctx):
    """Stay connected."""
    ctx.ctrl.connected = True
    ctx.device.connected = False
    return True


@action
def a_unexpected_prompt(ctx):
    """Provide message when received humphost prompt."""
    prompt = ctx.ctrl.after
    ctx.msg = "Received the jump host prompt: '{}'".format(prompt)
    ctx.device.connected = False
    ctx.finished = True
    raise ConnectionError("Unable to connect to the device.", ctx.ctrl.hostname)


@action
def a_connection_timeout(ctx):
    """Check the prompt and update the drivers."""
    prompt = ctx.ctrl.after
    ctx.msg = "Received the jump host prompt: '{}'".format(prompt)
    print(ctx.msg)
    ctx.device.connected = False
    ctx.finished = True
    raise ConnectionTimeoutError("Unable to connect to the device.", ctx.ctrl.hostname)


@action
def a_expected_prompt(ctx):
    """Update driver, config mode and hostname when received an expected prompt."""
    prompt = ctx.ctrl.after
    ctx.device.update_driver(prompt)
    ctx.device.update_config_mode()
    ctx.device.update_hostname()
    ctx.finished = True
    return True


@action
def a_save_last_pattern(obj, ctx):
    """Save last pattern in the context."""
    obj.last_pattern = ctx.pattern
    return True


@action
def a_send_boot(rommon_boot_command, ctx):
    """Send boot command."""
    ctx.ctrl.sendline(rommon_boot_command)
    return True


@action
def a_reconnect(ctx):
    """Reconnect."""
    ctx.device.connect(ctx.ctrl)
    return True


@action
def a_return_and_reconnect(ctx):
    """Send new line and reconnect."""
    ctx.ctrl.send("\r")
    ctx.ctrl.connect(ctx.device)
    return True


@action
def a_store_cmd_result(ctx):
    """Store the command result for complex state machines.

    It is useful when exact command output is embedded in another commands, i.e. admin show inventory in eXR.
    """
    result = ctx.ctrl.before
    # check if multi line
    index = result.find('\n')
    if index > 0:
        # remove first line
        result = result[index + 1:]
    ctx.device.last_command_result = result.replace('\r', '')
    return True


@action
def a_message_callback(ctx):
    """Message the captured pattern."""
    message = ctx.ctrl.after.strip().splitlines()[-1]
    ctx.device.chain.connection.emit_message(message, log_level=logging.INFO)
    return True
