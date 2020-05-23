import re
import getpass
import xmlrpc.client

import keyring
import requests


url = 'https://pypi.python.org/pypi'


def get_projects():
    username = getpass.getuser()
    client = xmlrpc.client.ServerProxy(url)
    return client.user_packages(username)


def request(data):
    username = getpass.getuser()
    password = keyring.get_password(url, username)
    auth = username, password
    return requests.post(url, data=data, auth=auth)


def get_CSRF_token(project):
    data = {
        ':action': 'pkg_edit',
        'name': project,
    }
    resp = request(data)
    resp.raise_for_status()
    res = re.search('"CSRFToken" value="(.*)"', resp.text)
    return res.group(1)


def remove_docs(project):
    data = {
        ':action': 'doc_destroy',
        'name': project,
        'submit': 'Destroy Documentation',
        'CSRFToken': get_CSRF_token(project),
    }
    resp = request(data)
    resp.raise_for_status()


def remove_all_docs():
    for role, project in get_projects():
        print("Removing docs for", project)
        remove_docs(project)
