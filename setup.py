#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import setuptools

name = 'jaraco.develop'
description = ''
nspkg_technique = 'managed'
"""
Does this package use "native" namespace packages or
pkg_resources "managed" namespace packages?
"""

params = dict(
	name=name,
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description=description or name,
	url="https://github.com/jaraco/" + name,
	packages=setuptools.find_packages(),
	include_package_data=True,
	namespace_packages=(
		name.split('.')[:-1] if nspkg_technique == 'managed'
		else []
	),
	python_requires='>=3.4',
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
		'testing': [
			# upstream
			'pytest>=3.5,!=3.7.3',
			'pytest-sugar>=0.9.1',
			'collective.checkdocs',
			'pytest-flake8',

			# local
		],
		'docs': [
			# upstream
			'sphinx',
			'jaraco.packaging>=3.2',
			'rst.linker>=1.9',

			# local
		],
		':sys_platform=="win32"': [
			'jaraco.windows>=2.7',
		],
	},
	setup_requires=[
		'setuptools_scm>=1.15.0',
	],
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
	setuptools.setup(**params)
