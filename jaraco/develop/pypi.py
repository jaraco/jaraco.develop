import getpass
import xmlrpc.client


url = 'https://pypi.python.org/pypi'


def get_projects():
    username = getpass.getuser()
    client = xmlrpc.client.ServerProxy(url)
    return client.user_packages(username)
