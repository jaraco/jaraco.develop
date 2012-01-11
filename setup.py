# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.develop

Copyright © 2010-2011 Jason R. Coombs
"""

import setuptools

name = 'jaraco.develop'

setup_params = dict(
	name = name,
	use_hg_version=True,
	description = 'Routines to assist development',
	long_description = open('README').read(),
	author = 'Jason R. Coombs',
	author_email = 'jaraco@jaraco.com',
	url = 'http://bitbucket.org/jaraco/'+name,
	packages = setuptools.find_packages(),
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
			'apply-python-bug-patch=jaraco.develop.python:'
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
			'build-python = jaraco.develop.python:build_python',
			'vs-upgrade = jaraco.develop.vstudio:upgrade_file',
			'set-tabs-mode = jaraco.develop.indent:set_tabs_mode_cmd',
		],
	},
	install_requires=[
		'jaraco.util>=4.0',
		#'html5lib',
	],
	extras_require = {
	},
	dependency_links = [
	],
	tests_require=[
	],
	use_2to3=True,
	setup_requires=[
		'hgtools',
	],
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)
