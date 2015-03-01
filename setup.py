# -*- coding: UTF-8 -*-

"""
Setup script for building jaraco.develop

Copyright © 2010-2015 Jason R. Coombs
"""

import sys
import platform

import setuptools

name = 'jaraco.develop'

needs_pytest = {'pytest', 'test'}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_sphinx = {'release', 'build_sphinx', 'upload_docs'}.intersection(sys.argv)
sphinx = ['sphinx'] if needs_sphinx else []

plat_requirements = []
if platform.system() == 'Windows':
	plat_requirements.extend(
		['jaraco.windows >= 2.7b1']
	)

with open('README.txt') as readme:
	long_description = readme.read()

setup_params = dict(
	name=name,
	use_scm_version=True,
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
		'keyring',
		'path.py',
		#'html5lib',
		'jaraco.text',
		'more_itertools',
		'jaraco.logging',
		'jaraco.ui',
	] + plat_requirements,
	extras_require={
	},
	dependency_links=[
	],
	tests_require=[
		'pytest',
	],
	setup_requires=[
		'setuptools_scm',
	] + pytest_runner,
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)
