import os
import logging
import requests


class adafruitIO():
    username = ""
    apikey = ""
    cache = []

    def __init__(self):
        self.username = os.getenv('ADAFRUIT_USERNAME', 'rickymoorhouse')
        self.apikey = os.getenv('ADAFRUIT_APIKEY', None)
        self.logger = logging.getLogger(__name__)

    def store(self, name, value):
        if self.apikey:
            req = requests.post(
                "https://io.adafruit.com/api/v2/{username}/feeds/{feed_key}/data".format(
                    username=self.username,
                    feed_key=name
                ),
                data={"value": value},
                headers={"X-AIO-Key":self.apikey }
            )
            self.logger.debug("store returned {}".format(req.status_code))


