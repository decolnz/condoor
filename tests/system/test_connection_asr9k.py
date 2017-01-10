from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import ASR9KHandler
from tests.utils import remove_cache_file

import condoor


class TestASR9KConnection(CondoorTestCase):
    @StartTelnetSrv(ASR9KHandler, 10023)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_ASR9K_1_discovery(self):
        """ASR9k: Test the connection and discovery"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        # TODO: Test if device_info is correct
        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-9904", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "5.3.3", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "chassis ASR-9904-AC", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 9904 2 Line Card Slot Chassis with V2 AC PEM",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-9904-AC", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1830GT5W", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))
        self.assertEqual(conn.is_console, False, "Console: {}".format(conn.is_console))

        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR9K_2_discovery(self):
        """ASR9k: Test whether the cached information is used"""
        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-9904", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "5.3.3", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "chassis ASR-9904-AC", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 9904 2 Line Card Slot Chassis with V2 AC PEM",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-9904-AC", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1830GT5W", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))
        self.assertEqual(conn.is_console, False, "Console: {}".format(conn.is_console))

        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR9K_3_connection_wrong_user(self):
        """ASR9k: Test wrong username"""
        urls = ["telnet://root:admin@127.0.0.1:10023"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

    def test_ASR9K_4_connection_refused(self):
        """ASR9k: Test when the connection is refused"""
        urls = ["telnet://admin:admin@127.0.0.1:10024"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        with self.assertRaises(condoor.ConnectionError):
            self.conn.connect(self.logfile_condoor)

    def test_ASR9K_5_discovery_force(self):
        """ASR9k: Test the connect with force"""
        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor, force_discovery=True)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-9904", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "5.3.3", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "chassis ASR-9904-AC", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 9904 2 Line Card Slot Chassis with V2 AC PEM",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-9904-AC", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1830GT5W", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))
        self.assertEqual(conn.is_console, False, "Console: {}".format(conn.is_console))

        conn.disconnect()


    def test_ASR9K_6_connect_reconnect(self):
        """ASR9k: Test the connect with force"""
        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-9904", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "5.3.3", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "chassis ASR-9904-AC", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 9904 2 Line Card Slot Chassis with V2 AC PEM",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-9904-AC", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1830GT5W", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))
        self.assertEqual(conn.is_console, False, "Console: {}".format(conn.is_console))

        conn.disconnect()

        conn.reconnect(self.logfile_condoor)
        conn.send("show user")
        conn.disconnect()


        conn.reconnect(self.logfile_condoor)
        conn.send("show user")

        conn.connect(self.logfile_condoor)
        conn.send("show user")


if __name__ == '__main__':
    from unittest import main
    main()
