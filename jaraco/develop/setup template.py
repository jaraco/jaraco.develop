#!/usr/bin/env python
# Generated by jaraco.develop {version}
# https://pypi.python.org/pypi/jaraco.develop

import io
import sys

import setuptools

with io.open('README.txt', encoding='utf-8') as readme:
	long_description = readme.read()

needs_pytest = {{'pytest', 'test'}}.intersection(sys.argv)
pytest_runner = ['pytest_runner'] if needs_pytest else []
needs_sphinx = {{'release', 'build_sphinx', 'upload_docs'}}.intersection(sys.argv)
sphinx = ['sphinx'] if needs_sphinx else []
needs_wheel = {{'release', 'bdist_wheel'}}.intersection(sys.argv)
wheel = ['wheel'] if needs_wheel else []

setup_params = dict(
	name='{project_name}',
	use_scm_version=True,
	author="Jason R. Coombs",
	author_email="jaraco@jaraco.com",
	description="{project_name}",
	long_description=long_description,
	url="https://bitbucket.org/jaraco/{project_name}",
	packages=setuptools.find_packages(),
	include_package_data=True,
	namespace_packages=['{namespace}'],
	install_requires=[
	],
	extras_require={{
	}},
	setup_requires=[
		'setuptools_scm>=1.9',
	] + pytest_runner + sphinx + wheel,
	tests_require=[
		'pytest>=2.8',
	],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python :: 2.7",
		"Programming Language :: Python :: 3",
	],
	entry_points={{
	}},
)
if __name__ == '__main__':
	setuptools.setup(**setup_params)
