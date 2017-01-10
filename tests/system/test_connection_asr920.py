from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import ASR920Handler
from tests.utils import remove_cache_file

import condoor


class TestASR920Connection(CondoorTestCase):
    @StartTelnetSrv(ASR920Handler, 10025)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_ASR920_1_discovery(self):
        """ASR920: Test the connection and discovery"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10025/admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "CSG-5502-ASR920", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-920", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XE", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "03.16.00.S", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "Cisco ASR920 Series - 12GE and 2-10GE - AC model",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-920-12CZ-A", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "CAT1928U2YX", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "CSG-5502-ASR920#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR920_2_discovery(self):
        """ASR920: Test whether the cached information is used"""
        urls = ["telnet://admin:admin@127.0.0.1:10025/admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "CSG-5502-ASR920", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-920", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XE", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "03.16.00.S", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "Cisco ASR920 Series - 12GE and 2-10GE - AC model",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-920-12CZ-A", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "CAT1928U2YX", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "CSG-5502-ASR920#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR920_3_connection_wrong_password(self):
        """ASR920: Test wrong password"""
        urls = ["telnet://:password@127.0.0.1:10025/admin"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)
        self.conn.disconnect()

    def test_ASR920_4_connection_wrong_enable_password(self):
        """ASR920: Test wrong enable password"""
        urls = ["telnet://:password@127.0.0.1:10025/admin"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()


            # def test_ASR9K_4_connection_refused(self):
    #     urls = ["telnet://admin:admin@127.0.0.1:10024"]
    #     self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
    #     with self.assertRaises(condoor.ConnectionError):
    #         self.conn.connect(self.logfile_condoor)


if __name__ == '__main__':
    from unittest import main
    main()
