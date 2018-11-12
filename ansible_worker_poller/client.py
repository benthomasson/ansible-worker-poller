import requests
import json
import gevent
import traceback
from pprint import pprint
from .messages import serialize, Deploy, Cancel


class PollerChannel(object):

    def __init__(self, address, wait_time, outbox):
        self.address = address
        self.start_socket_thread()
        self.outbox = outbox
        self.poll_wait_time = wait_time

    def start_socket_thread(self):
        print(self.address)
        self.thread = gevent.spawn(self.run_forever)

    def run_forever(self):
        while True:
            gevent.sleep(self.poll_wait_time)

    def put(self, message):
        try:
            self.socket.send(json.dumps(serialize(message)))
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            self.thread.kill()
            self.start_socket_thread()

    def on_open(self):
        print('PollerChannel on_open')
        pass

    def on_message(self, message):
        print('PollerChannel on_message')
        message = json.loads(message)
        pprint(message)
        if message[0] == "deploy":
            self.outbox.put(Deploy(message[1]))
        elif message[0] == "cancel":
            self.outbox.put(Cancel())

    def on_close(self):
        print('PollerChannel on_close')
        self.thread.kill()

    def on_error(self, error):
        print('PollerChannel on_error', error)
        try:
            self.on_close()
        finally:
            self.start_socket_thread()
