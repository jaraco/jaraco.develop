#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import io
import sys

import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
	long_description = readme.read()

needs_wheel = {'release', 'bdist_wheel', 'dists'}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

name = 'jaraco.develop'
description = ''

setup_params = dict(
	name=name,
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description=description or name,
	long_description=long_description,
	url="https://github.com/jaraco/" + name,
	packages=setuptools.find_packages(),
	include_package_data=True,
	namespace_packages=name.split('.')[:-1],
	install_requires=[
		'keyring',
		'path.py>=6.2',
		'jaraco.text',
		'more_itertools',
		'jaraco.logging',
		'jaraco.ui',
		'PyGithub>=1.25.2',
		'six',
		'jaraco.itertools',
		'jaraco.functools',
		'requests',
	],
	extras_require={
		':sys_platform=="win32"': [
			'jaraco.windows>=2.7',
		],
	},
	setup_requires=[
		'setuptools_scm>=1.15.0',
	] + wheel,
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
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
			'create-github-repo = jaraco.develop.github:'
				'create_repo_cmd',
			'build-python = jaraco.develop.python:build_python',
			'vs-upgrade = jaraco.develop.vstudio:upgrade_file',
			'set-tabs-mode = jaraco.develop.indent:set_tabs_mode_cmd',
			'patch-hgrc = jaraco.develop.mercurial:patch_hgrc',
			'hide-hg-dirs = jaraco.develop.mercurial:hide_hg_dirs',
		],
	},
)
if __name__ == '__main__':
	setuptools.setup(**setup_params)
