from tests.system.common import CondoorTestCase, StopTelnetSrv, StartTelnetSrv
from tests.dmock.dmock import SunHandler
from tests.utils import remove_cache_file

import condoor


class TestSunConnection(CondoorTestCase):
    @StartTelnetSrv(SunHandler, 10023)
    def setUp(self):
        CondoorTestCase.setUp(self)

    @StopTelnetSrv()
    def tearDown(self):
        pass

    def test_sun_connection(self):

        remove_cache_file()

        urls = ["telnet://admin:admin@127.0.0.1:10023", "telnet://admin:admin@host1"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionTimeoutError):
            conn.connect(self.logfile_condoor)

        conn.disconnect()

        #with self.assertRaises(condoor.ConnectionTimeoutError):
        #    conn.reconnect(30)

    def test_sun_connection_wrong_passowrd(self):
        urls = ["telnet://admin:wrong@127.0.0.1:10023", "telnet://admin:admin@host1"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            conn.connect(self.logfile_condoor)

        conn.disconnect()
