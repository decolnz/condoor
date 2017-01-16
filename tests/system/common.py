import functools
import os
import sys
from threading import Thread
from multiprocessing import Process
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

            def server_run(server):
                try:
                    server.serve_forever()
                except Exception as e:
                    print("server_run")
                    print(e)
                    pass

            obj.server_thread = Process(target=server_run, args=(obj.server, ))
            obj.server_thread.daemon = False
            obj.server_thread.start()
            fn(obj, *args, **kwargs)
        return decorated


class StopTelnetSrv(object):
    def __init__(self):
        pass

    def __call__(self, fn):
        @functools.wraps(fn)
        def decorated(obj, *args, **kwargs):

            # print("Try server shutdown")
            # try:
            #     obj.server.shutdown()
            # except Exception as e:
            #     print("shutdown")
            #     print(e)

            print("Try server close")
            try:
                obj.server.server_close()
            except Exception as e:
                print("server_close")
                print(e)

            # obj.server.socket.close()
            #
            #
            # print("Try thread join")
            # try:
            #     obj.server_thread.join(10)
            # except Exception as e:
            #     print("thread")
            #     print(e)

            obj.server_thread.terminate()
            obj.server_thread.join()



            print("Stop done")

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

