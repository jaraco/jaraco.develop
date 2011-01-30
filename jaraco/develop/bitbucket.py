import restclient
import urlparse
import functools

url = functools.partial(urlparse.urljoin, 'https://api.bitbucket.org/1.0/')

def create_repository(name, auth):
	print restclient.POST(url('repositories/'), params=dict(name=name),
		async=False, headers=dict(Authorization=auth))

def create_repository_cmd():
	import sys
	from getpass import getuser, getpass
	auth = ':'.join((getuser(), getpass())).encode('base64')
	create_repository(sys.argv[1], auth)

if __name__ == '__main__':
	create_repository_cmd()
