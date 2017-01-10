import functools
import os
import sys
from threading import Thread
from tests.dmock.dmock import TelnetServer
from unittest import TestCase


class StartTelnetSrv(object):
    def __init__(self, handler, port):
        self.handler = handler
        self.port = port

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(obj, *args, **kwargs):
            obj.server = TelnetServer(("127.0.0.1", self.port), self.handler)
            obj.server_thread = Thread(target=obj.server.serve_forever)
            obj.server_thread.daemon = True
            obj.server_thread.start()
            fn(obj, *args, **kwargs)
        return decorated


class StopTelnetSrv(object):
    def __init__(self):
        pass

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(obj, *args, **kwargs):
            try:
                obj.server.server_close()
            except:
                pass
        return decorated


class CondoorTestCase(TestCase):
    def setUp(self):
        debug = os.getenv("TEST_DEBUG", None)
        if debug:
            self.log_session = True
            self.logfile_condoor = sys.stderr
            self.log_level = 10

        else:
            self.log_session = False
            self.logfile_condoor = None  # sys.stderr
            self.log_level = 0

