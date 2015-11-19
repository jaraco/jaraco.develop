import pprint
import argparse
import getpass

import keyring
from github import Github


def create_repository(name):
	username = getpass.getuser()
	password = keyring.get_password('Github', username)
	g = Github(username, password)
	g.get_user().create_repo(name)


def create_repo_cmd():
	parser = argparse.ArgumentParser()
	parser.add_argument('repo_name')
	args = parser.parse_args()
	res = create_repository(args.repo_name)
	pprint.pprint(res)
