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

def init():
	global test_dir
	test_dir = os.path.expanduser('~/build/python')
	test_dir = os.path.normpath(test_dir)
	assert not '/' in test_dir

def create_test_dir():
	"""
	create a directory for the test
	"""
	build_existed_prior = os.path.exists(os.path.expanduser('~/build'))
	if os.path.exists(test_dir):
		if options.reuse: return
		print("Test directory already exists. Aborting", file=sys.stderr)
		raise SystemExit(1)
	os.makedirs(test_dir)

def checkout_source():
	global pcbuild_dir
	url = 'http://svn.python.org/projects/python/branches/py3k'
	print("Checking out Python from {url}".format(**vars()))
	target = os.path.join(test_dir, 'python-py3k')
	cmd = ['svn', 'co', '-q', url, target]
	if False:
		cmd.extend(['--depth', 'immediates', ]) # for debugging
	result = subprocess.Popen(cmd).wait()
	if result != 0:
		print("Checkout failed", file=sys.stderr)
		raise SystemExit(result)
	pcbuild_dir = os.path.join(target, 'pcbuild')

def apply_patch():
	target = os.path.join(test_dir, 'python-py3k')
	apply_python_bug_patch(bug_id, target)

def construct_build_command(args=[]):
	"""
	Inspired by build.bat
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
		os.path.join(pcbuild_dir, 'pcbuild.sln'),
		'|'.join([options.conf, options.platf])
	]
	if options.rebuild:
		cmd[-1:-1] = ['/rebuild']
	return cmd

def get_externals(word_size):
	script_name = {
		32: 'external.bat',
		64: 'external-amd64.bat',
		}[word_size]
	# the externals scripts are particular about the cwd
	cwd = os.path.join(pcbuild_dir, '..')
	script_path = os.path.join('Tools', 'buildbot', script_name)
	cmd = [script_path]
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT, cwd=cwd)
	for line in proc.stdout:
		sys.stdout.write(line)
	output, stderr = proc.communicate()
	print("result of {script_name} is {proc.returncode}".format(**vars()))
	return proc.returncode, output

def do_build(word_size, save_results):
	options.get_externals and get_externals(word_size)
	print("building {word_size}-bit python".format(**vars()))
	env_args = {32: [], 64: ['x64']}[word_size]
	env = get_vcvars_env(*env_args)
	cmd_args = {32: [], 64: ['-p', 'x64']}[word_size]
	cmd = construct_build_command(cmd_args)
	proc = subprocess.Popen(cmd, env=env, stdout=save_results, stderr=subprocess.STDOUT)
	proc.communicate()
	print("result of {word_size}-bit build is {proc.returncode}".format(**vars()))
	save_results.write('\nresult: {proc.returncode}'.format(**vars()))

def run_test(save_results, *params):
	print("Running regression tests")
	cmd = [
		'rt.bat',
		'-q',
		] + list(params)
	orig_dir = os.getcwd()
	os.chdir(pcbuild_dir)
	proc = subprocess.Popen(cmd, stdout=save_results, stderr=subprocess.STDOUT)
	proc.communicate()
	if not proc.returncode == 0:
		print("Warning: rt.bat returned {proc.returncode}".format(**vars()))
	os.chdir(orig_dir)
	save_results.write('\nresult: {proc.returncode}'.format(**vars()))

class Results(file):
	def __init__(self, filename):
		filename = os.path.expanduser('~/{filename}.txt'.format(**vars()))
		super(Results, self).__init__(filename, 'wb')

def cleanup():
	cmd = ['cmd', '/c', 'rmdir', '/s', '/q', test_dir]
	res = subprocess.Popen(cmd).wait()
	if not res == 0:
		print("Error cleaning up", file=sys.stderr)
		raise SystemExit(1)

# orchestrate the test
def orchestrate_test():
	init()
	create_test_dir()
	try:
		checkout_source()
		options.no_patch or apply_patch()
		do_build(32, save_results=Results('32-bit build results'))
		options.just_build or run_test(Results('32-bit test results'))
		if not options.skip_64_bit:
			do_build(64, save_results=Results('64-bit build results'))
			options.just_build or run_test(Results('64-bit test results'), '-x64')
	except KeyboardInterrupt:
		print("Cancelled by user")
	finally:
		options.just_build or print("Cleaning up...") and cleanup()

def handle_command_line():
	get_options()
	if options.clean:
		init(); cleanup()
		return
	if not options.skip:
		orchestrate_test()

def get_options():
	global options
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

if __name__ == '__main__':
	handle_command_line()
