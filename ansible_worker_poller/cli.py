#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Usage:
    ansible_worker_poller [options] <url>

Options:
    -h, --help       Show this page
    --debug          Show debug logging
    --verbose        Show verbose logging
    --wait_time=<t>  Wait time between polling server [default: 60].
"""
from gevent import monkey
monkey.patch_all(thread=False)

from docopt import docopt
import logging
import sys
from .client import PollerChannel
from .worker import AnsibleWorker
import gevent

logger = logging.getLogger('cli')


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    parsed_args = docopt(__doc__, args)
    if parsed_args['--debug']:
        logging.basicConfig(level=logging.DEBUG)
    elif parsed_args['--verbose']:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

    worker = AnsibleWorker()
    wc = PollerChannel(parsed_args['<url>'], parsed_args['--wait_time'], worker.queue)
    worker.controller.outboxes['output'] = wc
    gevent.joinall([wc.thread, worker.thread])
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
