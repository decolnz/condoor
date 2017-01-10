from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import ASR9K64Handler
from tests.utils import remove_cache_file

import condoor


class TestASR9K64Connection(CondoorTestCase):
    @StartTelnetSrv(ASR9K64Handler, 10022)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_ASR9K64_1_discovery(self):
        """ASR9k-64: Test whether the cached information is used"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10022"]
        conn = condoor.Connection('host', urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "ASR9K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "ASR-9904", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "eXR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "6.2.1.11I", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Rack 0", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "ASR-9904 AC Chassis",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "ASR-9904-AC", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "FOX1739G95R", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))
        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_ASR9K64_2_connection_wrong_user(self):
        urls = ["telnet://root:admin@127.0.0.1:10022"]
        self.conn = condoor.Connection('host', urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()

    def test_ASR9K64_3_connection_refused(self):
        urls = ["telnet://admin:admin@127.0.0.1:10024"]
        self.conn = condoor.Connection('host', urls, log_session=self.log_session, log_level=self.log_level)
        with self.assertRaises(condoor.ConnectionError):
            self.conn.connect(self.logfile_condoor)

        self.conn.disconnect()


if __name__ == '__main__':
    from unittest import main
    main()
