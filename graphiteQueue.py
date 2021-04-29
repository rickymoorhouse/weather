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

    def stage(self, name, value, timestamp=None):
        if None == timestamp:
            timestamp = int(time.time())
        message = '{}.{} {} {}'.format(self.prefix, name, value, timestamp)
        self.cache.append(message)
        self.logger.debug("storing {}".format(message))

    def debug(self):
        print(self.cache)

    def store(self):
        try:
            sock = socket.socket()
            sock.connect((self.server, self.port))
            self.logger.info("Sending {} records to graphite [{}:{}]".format(len(self.cache), self.server, self.port))
            self.logger.debug("\n".join(self.cache))
            sock.sendall(("\n".join(self.cache)+"\n").encode())
            sock.close()
            sent = len(self.cache)
            # Clear out cache
            self.cache[:] = []
            return sent
        except socket.error as se:
            self.logger.exception(se)

    def __del__(self):
        logging.info("Storing remaining data ({} records)".format(len(self.cache)))
        self.store()
