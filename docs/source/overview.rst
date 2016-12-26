Overview
========

The name is taken from conglomerate of two words: connection and door.
Condoor provides an easy way to connect to Cisco devices over SSH and Telnet. It provides the connection door
to the Cisco devices using standard Telnet and/or SSH protocol.

Condoor supports various software platforms including:

- Cisco IOS,
- Cisco IOS XE,
- Cisco IOS XR,
- Cisco IOS XR 64 bits,
- Cisco IOS XRv,
- Cisco NX-OS.

Condoor automatically adapts to different configuration modes and shells, i.e. XR Classic Admin mode,
XR 64 bits Calvados Admin mode or Windriver Linux when connecting to the Line Cards.

Here is the command line which installs together with Condoor module::

    $ condoor --help
    Usage: condoor [OPTIONS]

    Options:
      --url URL                       The connection url to the host (i.e.
                                      telnet://user:pass@hostname). The --url
                                      option can be repeated to define multiple
                                      jumphost urls. If no --url option provided
                                      the CONDOOR_URLS environment variable is
                                      used.  [required]
      --log-path PATH                 The logging path. If no path specified
                                      condoor logs are sent to stdout and session
                                      logs are sent to stderr.
      --log-level [NONE|DEBUG|INFO|ERROR]
                                      Logging level.  [default: ERROR]
      --log-session                   Log terminal session.
      --force-discovery               Force full device discovery.
      --cmd TEXT                      The command to be send to the device. The
                                      --cmd option can be repeated multiple times.
      --print-info                    Print the discovered information.
      --help                          Show this message and exit.




