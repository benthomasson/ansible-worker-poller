
from collections import namedtuple


def serialize(message):
    return [message.__class__.__name__, dict(message._asdict())]


Deploy = namedtuple('Deploy', ['id', 'data'])
Cancel = namedtuple('Cancel', ['id'])
Complete = namedtuple('Complete', ['id'])
Error = namedtuple('Error', ['id'])
RunnerStdout = namedtuple('RunnerStdout', ['id', 'data'])
RunnerMessage = namedtuple('RunnerMessage', ['id', 'data'])
RunnerCancelled = namedtuple('RunnerCancelled', ['id'])
