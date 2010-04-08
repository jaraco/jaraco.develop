#!python

"""
This script fully automates the checkout, patch, compile, test cycle
for the Windows symlink support patch.

Prerequisites:
	Visual Studio 2008
	Subversion command-line client
	GNU patch

If you run it without any command line parameters, it will create
~/build/python, check out the py3k branch to python-py3k, apply the
latest patch from the bugtracker, and then for each of the 32-bit and
64-bit architectures, build python and run the regression tests for it.

When it is done, it leaves four files in the user's home directory:

32-bit build results.txt
32-bit test results.txt
64-bit build results.txt
64-bit test results.txt

It then cleans up the rest.
"""

from __future__ import print_function
import os
import sys
import subprocess
import traceback
from optparse import OptionParser

from jaraco.develop.vstudio import get_vcvars_env
from jaraco.develop import apply_python_bug_patch

bug_id = 1578269
source_url = 'http://svn.python.org/projects/python/branches/py3k'

class TestStage():
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

	def apply_patch(self):
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

class Results(file):
	def __init__(self, filename):
		filename = os.path.expanduser('~/{filename}.txt'.format(**vars()))
		super(Results, self).__init__(filename, 'wb')

class TestConductor:
	# orchestrate the test
	def go(self, options):
		if options.skip: return
		stage = PythonTestStage()
		if options.clean:
			stage.cleanup(); return
		stage.create(options.reuse)
		try:
			stage.checkout_source(source_url)
			options.no_patch or stage.apply_patch()
			stage.do_build(32, Results('32-bit build results'), options.get_externals)
			options.just_build or stage.run_test(Results('32-bit test results'))
			if not options.skip_64_bit:
				stage.do_build(64, Results('64-bit build results'), options.get_externals)
				options.just_build or stage.run_test(Results('64-bit test results'), '-x64')
		except KeyboardInterrupt:
			print("Cancelled by user")
		finally:
			options.just_build or print("Cleaning up...") and stage.cleanup()

	def handle_command_line(self):
		self.go(self.get_options())

	def get_options(self):
		parser = OptionParser()
		parser.add_option('-s', '--skip', default=False,
			action="store_true",
			help="Don't do anything - useful for interactive mode",
			)
		parser.add_option('-b', '--just-build', default=False,
			action="store_true",
			help="Download, patch, and build, but don't test or clean up",
			)
		parser.add_option('-c', '--clean', default=False,
			action="store_true",
			help="Just run cleanup; all other options ignored",
			)
		parser.add_option('--no-patch', default=False, action="store_true",
			help="Skip patching the code",
			)
		parser.add_option('--skip-64-bit', default=False,
			action="store_true",
			help="Skip the 64-bit builds (do 32-bit only)"
			)
		parser.add_option('--get-externals', default=False,
			action="store_true",
			help="Get the external dependencies",
			)
		parser.add_option('--reuse', default=False, action="store_true",
			help="Re-use an existing checkout (if it exists)",
			)
		options, args = parser.parse_args()
		return options

if __name__ == '__main__':
	TestConductor().handle_command_line()
