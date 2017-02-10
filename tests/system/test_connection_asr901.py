from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import ASR901Handler
from tests.utils import remove_cache_file

import condoor


class TestASR901Connection(CondoorTestCase):
    @StartTelnetSrv(ASR901Handler, 10025)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_ASR901_1_discovery(self):
        """ASR901: Test the connection and discovery"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10025/?enable_password=admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "CSG-1202-ASR901", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "A901", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "IOS", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "15.3(2)S1", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "A901-6CZ-FT-A Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "A901-6CZ-FT-A Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "A901-6CZ-FT-A", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "CAT1650U01P", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "CSG-1202-ASR901#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR901_2_discovery(self):
        """ASR901: Test whether the cached information is used"""
        urls = ["telnet://admin:admin@127.0.0.1:10025/?enable_password=admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "CSG-1202-ASR901", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "A901", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "IOS", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "15.3(2)S1", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "A901-6CZ-FT-A Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "A901-6CZ-FT-A Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "A901-6CZ-FT-A", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "CAT1650U01P", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "CSG-1202-ASR901#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR901_3_connection_wrong_password(self):
        """ASR901: Test wrong password"""
        urls = ["telnet://:password@127.0.0.1:10025/?enable_password=admin"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()

    def test_ASR901_4_connection_wrong_enable_password(self):
        """ASR901: Test wrong enable password"""
        urls = ["telnet://admin:admin@127.0.0.1:10025/?enable_password=wrongpass"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()


if __name__ == '__main__':
    from unittest import main
    main()
