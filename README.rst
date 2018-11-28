=====================
Ansible Worker Poller
=====================


.. image:: https://img.shields.io/pypi/v/ansible_worker_poller.svg
        :target: https://pypi.python.org/pypi/ansible_worker_poller

.. image:: https://img.shields.io/travis/benthomasson/ansible_worker_poller.svg
        :target: https://travis-ci.org/benthomasson/ansible_worker_poller

.. image:: https://readthedocs.org/projects/ansible-worker-poller/badge/?version=latest
        :target: https://ansible-worker-poller.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status


Ansible Runner with REST API polling


* Free software: Apache Software License 2.0
* Documentation: https://ansible-worker-poller.readthedocs.io.


Features
--------

* Ansible runner side of the Insights Ansible Runner POC. More information here: https://github.com/benthomasson/insights_ansible_runner_poc
* Polls a task queue for a ansible playbook to run


Usage
-----

	Usage:
		ansible_worker_poller [options] <url> <worker_id>

	Options:
		-h, --help          Show this page
		--debug             Show debug logging
		--verbose           Show verbose logging
		--wait_time=<t>     Wait time between polling server [default: 60].


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
