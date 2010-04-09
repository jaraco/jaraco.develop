#!python
#-*- coding: utf-8 -*-

from __future__ import print_function, absolute_import

import os
import sys
import subprocess
from optparse import OptionParser

from .vstudio import get_vcvars_env
from jaraco.develop import apply_python_bug_patch

class TestStage(object):
	"""
	A staging directory where code will be checked out and tests run.
	"""
	def __init__(self):
		self.location = os.path.expanduser('~/build/python')
		self.location = os.path.normpath(self.location)

	def create(self, reuse=False):
		"""
		create a directory for the test
		"""
		build_existed_prior = os.path.exists(os.path.expanduser('~/build'))
		loc_exists = os.path.exists(self.location)
		if loc_exists and not reuse:
			msg = "Test directory already exists."
			print(msg + " Aborting", file=sys.stderr)
			raise RuntimeError(msg)
		if not loc_exists:
			os.makedirs(self.location)

	def checkout_source(self, url, project_name=None):
		self.project_name = project_name or os.path.basename(url)
		print("Checking out source from {url}".format(**vars()))
		target = os.path.join(self.location, self.project_name)
		cmd = ['svn', 'co', '-q', url, target]
		if False:
			cmd.extend(['--depth', 'immediates', ]) # for debugging
		result = subprocess.Popen(cmd).wait()
		if result != 0:
			print("Checkout failed", file=sys.stderr)
			raise RuntimeError("Checkout failed")

	@property
	def project_location(self):
		return os.path.join(self.location, self.project_name)

	def cleanup(self):
		cmd = ['cmd', '/c', 'rmdir', '/s', '/q', self.location]
		res = subprocess.Popen(cmd).wait()
		if not res == 0:
			msg = "Error cleaning up"
			print(msg, file=sys.stderr)
			raise RuntimeError(msg)

class PythonTestStage(TestStage):
	@property
	def pcbuild_dir(self):
		return os.path.join(self.project_location, 'PCBuild')

	def apply_patch(self, bug_id):
		apply_python_bug_patch(bug_id, self.project_location)

	def get_externals(self, word_size):
		script_name = {
			32: 'external.bat',
			64: 'external-amd64.bat',
			}[word_size]
		script_path = os.path.join('Tools', 'buildbot', script_name)
		proc = subprocess.Popen(script_path, stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			cwd=self.project_location, # external scripts are particular about the cwd
			)
		output, stderr = proc.communicate()
		print("result of {script_name} is {proc.returncode}".format(**vars()))
		return proc.returncode, output

	def do_build(self, word_size, save_results, get_externals=False):
		get_externals and self.get_externals(word_size)
		print("building {word_size}-bit python".format(**vars()))
		env_args = {32: [], 64: ['x64']}[word_size]
		env = get_vcvars_env(*env_args)
		cmd_args = {32: [], 64: ['-p', 'x64']}[word_size]
		cmd = self.construct_build_command(self.project_location, cmd_args)
		proc = subprocess.Popen(cmd, env=env, stdout=save_results, stderr=subprocess.STDOUT)
		proc.communicate()
		print("result of {word_size}-bit build is {proc.returncode}".format(**vars()))
		save_results.write('\nresult: {proc.returncode}'.format(**vars()))

	@staticmethod
	def construct_build_command(base, args=[]):
		"""
		Construct a command to build Python, modeled after build.bat
		"""
		parser = OptionParser()
		parser.add_option('-c', '--conf', default='Release')
		parser.add_option('-p', '--platf', default='Win32')
		parser.add_option('-r', '--rebuild', action='store_true', default=False)
		parser.add_option('-d', '--debug', dest='conf', action='store_const', const='Debug')
		options, args = parser.parse_args(args)

		cmd = [
			'cmd', '/c',
			'vcbuild',
			'/useenv',
			os.path.join(base, 'PCBuild', 'pcbuild.sln'),
			'|'.join([options.conf, options.platf])
		]
		if options.rebuild:
			cmd[-1:-1] = ['/rebuild']
		return cmd

	def run_test(self, save_results, *params):
		print("Running regression tests")
		cmd = [
			os.path.join(self.pcbuild_dir, 'rt.bat'),
			'-q',
			] + list(params)
		proc = subprocess.Popen(cmd, stdout=save_results,
			stderr=subprocess.STDOUT, cwd=self.pcbuild_dir)
		proc.wait()
		if not proc.returncode == 0:
			print("Warning: rt.bat returned {proc.returncode}".format(**vars()))
		save_results.write('\nresult: {proc.returncode}'.format(**vars()))

