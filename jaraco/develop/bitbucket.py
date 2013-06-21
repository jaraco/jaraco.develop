from __future__ import print_function

import sys
import functools
import argparse
import getpass
import collections
import pprint

try:
	import urllib.parse as urllib_parse
except ImportError:
	import urlparse as urllib_parse

import requests
import keyring
from jaraco.util.string import local_format as lf

api_url = 'https://api.bitbucket.org/1.0/'
make_url = functools.partial(urllib_parse.urljoin, api_url)

def handle_error(resp):
	if not resp.ok:
		print(lf("Error occurred: {resp}"), file=sys.stderr)
		print(resp.text)
	resp.raise_for_status()

def create_repository(name, auth, private=False):
	resp = requests.post(make_url('repositories/'),
		data=dict(name=name, is_private=private, scm='hg',
			language='python'), auth=auth,
		headers=dict(Accept='text/json'),
	)
	handle_error(resp)
	return resp.json()

def add_version(project, version, auth):
	"""
	project should be something like user/project
	"""
	url = make_url(lf('repositories/{project}/versions'))
	resp = requests.post(
		url,
		params=dict(name=version),
		auth=auth,
		headers=dict(Accept='text/json'),
	)
	handle_error(resp)
	return resp.json()

Credential = collections.namedtuple('Credential', 'username password')

def get_mercurial_creds(username=None):
	"""
	Return named tuple of username,password in much the same way that
	Mercurial would (from the keyring).
	"""
	# todo: consider getting this from .hgrc
	username = username or getpass.getuser()
	root = 'https://bitbucket.org'
	keyring_username = '@@'.join((username, root))
	system = 'Mercurial'
	password = keyring.get_password(system, keyring_username)
	if not password:
		password = getpass.getpass()
	return Credential(username, password)

def basic_auth(userpass):
	return Credential(userpass.split(':'))

def create_repository_cmd():
	parser = argparse.ArgumentParser()
	parser.add_argument('repo_name')
	parser.add_argument(
		'-a', '--auth', type=basic_auth, default=get_mercurial_creds(),
	)
	parser.add_argument('-p', '--private', default=False,
		action="store_true")
	args = parser.parse_args()
	res = create_repository(args.repo_name, args.auth,
		private = args.private)
	pprint.pprint(res)

def update_wiki(project, title, path, content):
	url = make_url('repositories/{project}/wiki/{title}'.format(**vars()))
	data = dict(path=path, data=content)
	resp = requests.put(url, data=data, auth=get_mercurial_creds(),
		headers=dict(Accept='text/json'))
	handle_error(resp)

if __name__ == '__main__':
	create_repository_cmd()
