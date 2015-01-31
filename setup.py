# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.develop

Copyright © 2010-2013 Jason R. Coombs
"""

import platform

import setuptools

name = 'jaraco.develop'

plat_requirements = []
if platform.system() == 'Windows':
	plat_requirements.extend(
		['jaraco.windows >= 2.7b1']
	)

with open('README') as readme:
	long_description = readme.read()

setup_params = dict(
	name=name,
	use_hg_version=True,
	description='Routines to assist development',
	long_description=long_description,
	author='Jason R. Coombs',
	author_email='jaraco@jaraco.com',
	url='http://bitbucket.org/jaraco/' + name,
	packages=setuptools.find_packages(),
	namespace_packages=['jaraco'],
	include_package_data=True,
	license='MIT',
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"Programming Language :: Python",
		"Programming Language :: Python :: 2",
		"Programming Language :: Python :: 3",
	],
	entry_points={
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
			'patch-hgrc = jaraco.develop.mercurial:patch_hgrc',
			'hide-hg-dirs = jaraco.develop.mercurial:hide_hg_dirs',
		],
	},
	install_requires=[
		'jaraco.util>=8.0',
		'keyring',
		'path.py',
		#'html5lib',
	] + plat_requirements,
	extras_require={
	},
	dependency_links=[
	],
	tests_require=[
	],
	setup_requires=[
		'hgtools',
	],
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)
