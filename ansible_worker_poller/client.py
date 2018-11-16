import requests
import yaml
import gevent
from .messages import Deploy
from . import messages
from itertools import count
import re

ansi_escape = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')


class PollerChannel(object):

    def __init__(self, address, worker_id, wait_time, outbox):
        self.address = address
        self.worker_id = worker_id
        self.poll_wait_time = wait_time
        self.outbox = outbox
        self.start_socket_thread()
        self.run_data = dict()
        self.log_counter = count(0, 1)

    def get_api_url(self, name, **kwargs):
        if kwargs:
            return '{0}/insights_integration/api/{1}/?{2}'.format(self.address, name, "&".join(["=".join([str(y) for y in x]) for x in kwargs.items()]))
        else:
            return '{0}/insights_integration/api/{1}/'.format(self.address, name)

    def start_socket_thread(self):
        self.thread = gevent.spawn(self.run_forever)

    def run_forever(self):
        while True:
            self.poll_worker_queue()
            gevent.sleep(self.poll_wait_time)

    def delete_api_object(self, object_type, pk):
        response = requests.delete(self.get_api_url(object_type) + str(pk))
        if not response.status_code == 204:
            raise Exception("Not deleted")

    def post_api_object(self, object_type, data):
        response = requests.post(self.get_api_url(object_type), data=data)
        return response.json()

    def put_api_object(self, object_type, pk, data):
        response = requests.put("{0}{1}/".format(self.get_api_url(object_type), pk), data=data)
        return response.json()

    def patch_api_object(self, object_type, pk, data):
        response = requests.patch("{0}{1}/".format(self.get_api_url(object_type), pk), data=data)
        return response.json()


    def get_api_object(self, object_type, **kwargs):
        object_list = self.get_api_list(object_type, **kwargs)
        if len(object_list) == 1:
            return object_list[0]
        elif len(object_list) == 0:
            raise Exception("{0} object not found for {1}".format(object_type, repr(kwargs)))
        else:
            raise Exception("More than one {0} object found for {1}".format(object_type, repr(kwargs)))

    def get_api_list(self, object_type, **kwargs):
        response = requests.get(self.get_api_url(object_type, **kwargs))
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            raise Exception(response.text)

    def poll_worker_queue(self):
        items = self.get_api_list('workerqueue', worker_id=self.worker_id)
        for item in items:
            playbook_run = self.get_api_object('playbookrun', playbook_run_id=item['playbook_run'])
            key = self.get_api_object('key', key_id=playbook_run['key'])
            playbook = self.get_api_object('playbook', playbook_id=playbook_run['playbook'])
            hosts = self.get_api_list('host', inventory_id=playbook_run['inventory'])

            host_vars = {x['name']: yaml.load(x['host_vars']) for x in hosts}

            self.run_data[playbook_run['playbook_run_id']] = dict(hosts={x['name']: x['host_id'] for x in hosts},
                                                                  playbook_run=playbook_run['playbook_run_id'])

            inventory_yaml = yaml.dump(dict(all=dict(hosts={x['name']: host_vars[x['name']] for x in hosts})), default_flow_style=False)
            self.outbox.put(Deploy(playbook_run['playbook_run_id'],
                                   dict(text='doit',
                                        inventory=inventory_yaml,
                                        playbook=yaml.load(playbook['contents']),
                                        key=key['value'])))
            self.delete_api_object('workerqueue', item['worker_queue_id'])

    def put(self, message):
        if isinstance(message, messages.RunnerMessage):
            self.onRunnerMessage(message)
        elif isinstance(message, messages.RunnerStdout):
            self.onRunnerStdout(message)

    def onRunnerMessage(self, message):
        handler = getattr(self, "on_" + message.data.get('event', None), None)
        if handler:
            handler(message)

    def onRunnerStdout(self, message):
        data = message.data
        data = ansi_escape.sub('', data)
        self.post_api_object('playbookrunlog', dict(playbook_run=self.run_data[message.id]['playbook_run'],
                                                    order=next(self.log_counter),
                                                    value=data))

    def on_runner_on_ok(self, message):
        taskresult = self.post_api_object('taskresult', dict(status='ok',
                                                             name=message.data['event_data']['task'],
                                                             host=self.run_data[message.id]['hosts'][message.data['event_data']['host']]))
        self.post_api_object('taskresultplaybookrun', dict(task_result=taskresult['task_result_id'],
                                                           playbook_run=self.run_data[message.id]['playbook_run']))

    def on_runner_on_unreachable(self, message):
        taskresult = self.post_api_object('taskresult', dict(status='unreachable',
                                                             name=message.data['event_data']['task'],
                                                             host=self.run_data[message.id]['hosts'][message.data['event_data']['host']]))
        self.post_api_object('taskresultplaybookrun', dict(task_result=taskresult['task_result_id'],
                                                           playbook_run=self.run_data[message.id]['playbook_run']))
    def on_runner_on_failed(self, message):
        taskresult = self.post_api_object('taskresult', dict(status='failed',
                                                             name=message.data['event_data']['task'],
                                                             host=self.run_data[message.id]['hosts'][message.data['event_data']['host']]))
        self.post_api_object('taskresultplaybookrun', dict(task_result=taskresult['task_result_id'],
                                                           playbook_run=self.run_data[message.id]['playbook_run']))


    def on_playbook_on_task_start(self, message):
        pass

    def on_playbook_on_start(self, message):
        self.patch_api_object('playbookrun', self.run_data[message.id]['playbook_run'], dict(status="started"))

    def on_playbook_on_play_start(self, message):
        pass

    def on_playbook_on_stats(self, message):
        self.patch_api_object('playbookrun', self.run_data[message.id]['playbook_run'], dict(status="completed"))
