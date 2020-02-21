import socket
import time
import os
import logging
class graphite():
    server = 'localhost'
    prefix = ""
    port = 2003
    cache = []

    def __init__(self, server='localhost', port=2003, prefix=''):
        self.server = os.getenv('GRAPHITE_HOST', 'localhost')
        self.port = int(os.getenv('GRAPHITE_PORT', '2003'))
        self.prefix = prefix
        self.logger = logging.getLogger(__name__)

    def stage(self, name, value):
        t = int(time.time())
        message = '{}.{} {} {}'.format(self.prefix, name, value, t)
        self.cache.append(message)
        self.logger.debug("storing {}".format(message))

    def store(self):
        try:
            sock = socket.socket()
            sock.connect((self.server, self.port))
            self.logger.info("Sending {} records to graphite [{}:{}]".format(len(self.cache), self.server, self.port))
            self.logger.debug("\n".join(self.cache))
            sock.sendall(("\n".join(self.cache)+"\n").encode())
            sock.close()
            # Clear out cache
            self.cache[:] = []
        except socket.error as se:
            self.logger.exception(se)

    def __del__(self):
        logging.info("Storing remaining data ({} records)".format(len(self.cache)))
        self.store()
