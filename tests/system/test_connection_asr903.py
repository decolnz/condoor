from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import ASR903Handler
from tests.utils import remove_cache_file

import condoor


class TestASR903Connection(CondoorTestCase):
    @StartTelnetSrv(ASR903Handler, 10026)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_ASR903_1_discovery(self):
        """ASR903: Test the connection and discovery"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10026/?enable_password=admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "PAN-5205-ASR903", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-903", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XE", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "03.18.00.S", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 903 Series Router Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-903", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1717P569", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "PAN-5205-ASR903#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR903_2_discovery(self):
        """ASR903: Test whether the cached information is used"""
        urls = ["telnet://admin:admin@127.0.0.1:10026/?enable_password=admin"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "PAN-5205-ASR903", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR900", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-903", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "XE", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "03.18.00.S", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Chassis", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR 903 Series Router Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-903", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1717P569", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "PAN-5205-ASR903#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR903_3_connection_wrong_password(self):
        """ASR903: Test wrong password"""
        urls = ["telnet://:password@127.0.0.1:10026/?enable_password=admin"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

    def test_ASR903_4_connection_wrong_enable_password(self):
        """ASR903: Test wrong enable password"""
        urls = ["telnet://:password@127.0.0.1:10026/?enable_password=admin"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)


if __name__ == '__main__':
    from unittest import main
    main()
