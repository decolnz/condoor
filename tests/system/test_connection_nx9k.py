from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import NX9KHandler
from tests.utils import remove_cache_file

import condoor


class TestNX9KConnection(CondoorTestCase):
    @StartTelnetSrv(NX9KHandler, 10024)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_NX9K_1_discovery(self):

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10024"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "switch", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "N9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "N9K-C9508", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "NX-OS", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "7.0(3)IED5(1)", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "Nexus9000 C9508 (8 Slot) Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "N9K-C9508", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FGE18210BQR", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "switch#", "Wrong Prompt: {}".format(conn.prompt))
        self.assertEqual(conn.is_console, True, "Console connection not detected")
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_NX9K_2_connection_wrong_user(self):
        urls = ["telnet://root:admin@127.0.0.1:10024"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()

    def test_NX9K_3_connection_refused(self):
        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        with self.assertRaises(condoor.ConnectionError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()


if __name__ == '__main__':
    from unittest import main
    main()
