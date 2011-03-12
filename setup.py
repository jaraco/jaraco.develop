# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.develop

Copyright © 2010 Jason R. Coombs
"""

try:
	from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
	from distutils.command.build_py import build_py

from setuptools import find_packages

name = 'jaraco.develop'

setup_params = dict(
	name = name,
	use_hg_version=True,
	description = 'Routines to assist development',
	long_description = open('README').read(),
	author = 'Jason R. Coombs',
	author_email = 'jaraco@jaraco.com',
	url = 'http://bitbucket.org/jaraco/'+name,
	packages = find_packages(),
	namespace_packages = ['jaraco',],
	scripts = ['scripts/test-python-symlink-patch.py'],
	license = 'MIT',
	classifiers = [
		"Development Status :: 4 - Beta",
		"Intended Audience :: Developers",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 3",
	],
	entry_points = {
		'console_scripts': [
			'apply-python-bug-patch=jaraco.develop:'
				'apply_python_bug_patch_cmd',
			'start-selenium=jaraco.develop.selenium:'
				'start_selenium_server',
			'release-package = jaraco.develop.package:release',
			'py-exc-env = jaraco.develop.environments:'
				'PythonEnvironment.handle_command_line',
			'make-namespace-package = jaraco.develop.namespace:'
				'create_namespace_package_cmd',
			'create-bitbucket-repository = jaraco.develop.bitbucket:'
				'create_repository_cmd',
			],
	},
	install_requires=[
		'jaraco.util',
		#'html5lib',
	],
	extras_require = {
	},
	dependency_links = [
	],
	tests_require=[
	],
	cmdclass=dict(build_py=build_py),
	setup_requires=[
		'hgtools',
	],
)

if __name__ == '__main__':
	from setuptools import setup
	setup(**setup_params)
