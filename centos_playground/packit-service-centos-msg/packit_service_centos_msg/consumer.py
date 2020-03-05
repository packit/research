# MIT License
#
# Copyright (c) 2018-2019 Red Hat, Inc.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import json
import os
import ssl
from logging import getLogger
from os import getenv
from pprint import pprint

from celery import Celery
import paho.mqtt.client as mqtt

logger = getLogger(__name__)

class Consumerino(mqtt.Client):
    """
    Consume events from centos messaging
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._celery_app = None

    @property
    def celery_app(self):
        if self._celery_app is None:
            redis_host = getenv("REDIS_SERVICE_HOST", "localhost")
            redis_port = getenv("REDIS_SERVICE_PORT", "6379")
            redis_db = getenv("REDIS_SERVICE_DB", "0")
            redis_url = "redis://{host}:{port}/{db}".format(
                host=redis_host, port=redis_port, db=redis_db
            )

            self._celery_app = Celery(backend=redis_url, broker=redis_url)
        return self._celery_app

    def on_message(self, client, userdata, msg):
        # print(msg.topic + " " + str(msg.payload))
        pprint(msg.topic)
        pprint(json.loads(msg.payload))

    def on_connect(self, client, userdata, flags, rc):
        print("Connected with result code " + str(rc))
        logger.info(f"Connected wit result code: ${str(rc)}")

        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe("git.stg.centos.org/#")

    def consume_from_centos_messaging(self, ca_certs, certfile):

        self.tls_set(ca_certs=ca_certs, certfile=certfile,
                     keyfile=certfile, cert_reqs=ssl.CERT_REQUIRED,
                     tls_version=ssl.PROTOCOL_TLS)
        self.connect(host="mqtt.stg.centos.org", port=8883)
        self.loop_forever()

