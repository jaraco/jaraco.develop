from __future__ import print_function
import sys
import restclient
import urlparse
import functools
import argparse
import json
import pprint

def create_repository(name, auth, url, private=False):
	make_url = functools.partial(urlparse.urljoin, url)
	res = restclient.POST(make_url('repositories/'),
		params=dict(name=name, is_private=private, scm='hg'),
		async=False,
		headers=dict(Authorization=auth), accept=['text/json'],
	)
	res = json.loads(res)
	return res

def create_repository_cmd():
	from getpass import getuser, getpass
	parser = argparse.ArgumentParser()
	parser.add_argument('repo_name')
	parser.add_argument('-a', '--auth')
	parser.add_argument('-u', '--url', default='https://api.bitbucket.org/1.0/')
	parser.add_argument('-p', '--private', default=False,
		action="store_true")
	args = parser.parse_args()
	if not args.auth:
		args.auth = ':'.join((getuser(), getpass()))
	args.auth = 'Basic ' + args.auth.encode('base64')
	res = create_repository(args.repo_name, args.auth, args.url,
		private = args.private)
	pprint.pprint(res)

if __name__ == '__main__':
	create_repository_cmd()
