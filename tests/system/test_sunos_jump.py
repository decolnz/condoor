
import os
from unittest import TestCase

from tests.dmock.dmock import TelnetServer, SunHandler
from threading import Thread

import condoor


class TestSunConnection(TestCase):
    def setUp(self):
        self.server = TelnetServer(("127.0.0.1", 10023), SunHandler)
        self.server_thread = Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()

        debug = os.getenv("TEST_DEBUG", None)
        if debug:
            self.log_session = True
            import sys
            self.logfile_condoor = sys.stderr
            self.log_level = 10

        else:
            self.log_session = False
            self.logfile_condoor = None  # sys.stderr
            self.log_level = 0

        try:
            os.remove('/tmp/condoor.shelve')
        except OSError:
            pass

    def tearDown(self):
        self.server.RUNSHELL = False
        self.server.shutdown()
        self.server.server_close()
        self.server_thread.join()

    def test_sun_connection(self):
        urls = ["telnet://admin:admin@127.0.0.1:10023", "telnet://admin:admin@host1"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionTimeoutError):
            conn.connect(self.logfile_condoor)
        print(conn.description_record)
        conn.reconnect(30)

    def test_sun_connection_wrong_passowrd(self):
        urls = ["telnet://admin:wrong@127.0.0.1:10023", "telnet://admin:admin@host1"]
        conn = condoor.Connection("host", urls, log_session=self.log_session, log_level=self.log_level)

        with self.assertRaises(condoor.ConnectionAuthenticationError):
            conn.connect(self.logfile_condoor)
