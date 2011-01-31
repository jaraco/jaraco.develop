from __future__ import print_function
import sys
import restclient
import urlparse
import functools
import argparse

def create_repository(name, auth, url):
	make_url = functools.partial(urlparse.urljoin, url)
	resp, content = restclient.POST(make_url('repositories/'),
		params=dict(name=name), resp=True,
		async=False, headers=dict(Authorization=auth),
		)
	import pdb;
	pdb.set_trace()

def create_repository_cmd():
	from getpass import getuser, getpass
	parser = argparse.ArgumentParser()
	parser.add_argument('repo_name')
	parser.add_argument('-a', '--auth')
	parser.add_argument('-u', '--url', default='https://api.bitbucket.org/1.0/')
	args = parser.parse_args()
	if not args.auth:
		args.auth = ':'.join((getuser(), getpass()))
	args.auth = args.auth.encode('base64')
	create_repository(args.repo_name, args.auth, args.url)

if __name__ == '__main__':
	create_repository_cmd()
