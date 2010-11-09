#!/usr/bin/env python

import os
import sys
import inspect
import pkg_resources

def set_environment_for_PyPI():
	"""
	PyPI requires that the HOME environment be set before running
	upload, so go ahead and set it to something reasonable.
	"""
	if sys.platform in ('win32',):
		# set the HOME environment variable if it's not already set
		drivepath = map(os.environ.get, ('HOMEDRIVE', 'HOMEPATH'))
		calculated_home = os.path.join(*drivepath)
		# todo: consider os.expanduser('~') instead
		os.environ.setdefault('HOME', calculated_home)

def release():
	set_environment_for_PyPI()

	sys.argv[1:] = ['egg_info', '-RDb', '', 'sdist', 'upload']
	__name__ = '__main__'
	execfile('setup.py')

def read_long_description():
	"""
	return the text in docs/index.txt
	"""
	return open(
		os.path.join(
			'docs',
			'index.txt',
		) ).read().strip()

def test_compile_rst(filename):
	try:
		from docutils.core import publish_string
	except ImportError:
		# if we don't have docutils, just fail silently
		return
	docs = open(filename).read()
	res = publish_string(docs)

def local_resource_filename(filename):
	"""
	Use pkg_resources to get a filename for a resource relative to
	the caller's module.
	"""
	callers_frame = inspect.currentframe().f_back
	calling_module_name = callers_frame.f_globals['__name__']
	return pkg_resources.resource_filename(calling_module_name, filename)
