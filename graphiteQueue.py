import time
import os
import logging
import requests


class graphite():
    server = 'localhost'
    prefix = ""
    cache = []

    def __init__(self, server='localhost', port=2003, prefix=''):
        self.server = os.getenv('GRAPHITE_HOST', 'localhost')
        self.url = 'https://{}/graphite/metrics'.format(self.server)
        self.headers = {
            "Authorization": "Bearer {}:{}".format(
                os.getenv('GRAFANA_USER'),
                os.getenv('GRAFANA_APIKEY'))
        }
        self.prefix = prefix
        self.logger = logging.getLogger(__name__)

    def stage(self, name, value, timestamp=None):
        if timestamp is None:
            timestamp = int(time.time())
        message = '{}.{} {} {}'.format(self.prefix, name, value, timestamp)
        self.cache.append(
            {
                'name': "{}.{}".format(self.prefix, name),
                'metric': "{}.{}".format(self.prefix, name),
                'value': float(value),
                'time': int(timestamp),
                'interval': 30,
                'mtype': 'count',
                'tags': [],
            }
        )
        self.logger.debug("storing {}".format(message))

    def debug(self):
        self.logger.debug(print(self.cache))

    def store(self):
        try:
            if self.server != "localhost":
                # sort by ts
                self.cache.sort(key=lambda obj: obj['time'])
                result = requests.post(self.url, json=self.cache, headers=self.headers)
                if result.status_code != 200:
                    raise Exception(result.text)
                self.logger.info('%s: %s' % (result.status_code, result.text))            
                sent = len(self.cache)
                # Clear out cache
                self.cache[:] = []
                self.cache[:] = []
                return sent
            else:
                return 0
        except Exception as se:
            self.logger.info("Failed to send %d",len(self.cache))
            self.logger.exception(se)
            return -1

    def __del__(self):
        logging.info("Storing remaining data ({} records)".format(len(self.cache)))
        self.store()


