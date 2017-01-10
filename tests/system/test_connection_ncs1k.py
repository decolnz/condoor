from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import NCS1KHandler
from tests.utils import remove_cache_file

import condoor


class TestNCS1KConnection(CondoorTestCase):
    @StartTelnetSrv(NCS1KHandler, 10023)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_NCS1K_1_discovery(self):
        """NCS1k: Test the connection and discovery"""

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10023"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)
        self.conn = conn
        conn.connect(self.logfile_condoor)

        self.assertEqual(conn.is_discovered, True, "Not discovered properly")
        self.assertEqual(conn.hostname, "ios", "Wrong Hostname: {}".format(conn.hostname))
        self.assertEqual(conn.family, "NCS1K", "Wrong Family: {}".format(conn.family))
        self.assertEqual(conn.platform, "NCS1002", "Wrong Platform: {}".format(conn.platform))
        self.assertEqual(conn.os_type, "eXR", "Wrong OS Type: {}".format(conn.os_type))
        self.assertEqual(conn.os_version, "6.0.1", "Wrong Version: {}".format(conn.os_version))
        self.assertEqual(conn.udi['name'], "Rack 0", "Wrong Name: {}".format(conn.udi['name']))
        self.assertEqual(conn.udi['description'], "Network Convergence System 1000 Controller",
                         "Wrong Description: {}".format(conn.udi['description']))
        self.assertEqual(conn.udi['pid'], "NCS1002", "Wrong PID: {}".format(conn.udi['pid']))
        self.assertEqual(conn.udi['vid'], "V01", "Wrong VID: {}".format(conn.udi['vid']))
        self.assertEqual(conn.udi['sn'], "CHANGE-ME-", "Wrong S/N: {}".format(conn.udi['sn']))
        self.assertEqual(conn.prompt, "RP/0/RP0/CPU0:ios#", "Wrong Prompt: {}".format(conn.prompt))

        with self.assertRaises(condoor.CommandSyntaxError):
            conn.send("wrongcommand")

        conn.disconnect()

    def test_NCS1K_2_connection_refused(self):
        urls = ["telnet://admin:admin@127.0.0.1:10024"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=0)
        with self.assertRaises(condoor.ConnectionError):
            self.conn.discovery(self.logfile_condoor)

        self.conn.disconnect()

    def test_NCS1K_3_connection_wrong_user(self):
        urls = ["telnet://root:admin@127.0.0.1:10023"]
        self.conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=0)
        with self.assertRaises(condoor.ConnectionAuthenticationError):
            self.conn.discovery(self.logfile_condoor)

        self.conn.disconnect()

    # TODO: Add unexpected disconnect test
