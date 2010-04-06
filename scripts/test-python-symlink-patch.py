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
import re
import subprocess
import itertools
import traceback
import urllib2
import urllib
import urlparse
from optparse import OptionParser
from BeautifulSoup import BeautifulSoup

from jaraco.develop.vstudio import get_vcvars_env

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
		print("Test directory already exists. Aborting", file=sys.stderr)
		raise SystemExit(1)
	os.makedirs(test_dir)

def checkout_source():
	global pcbuild_dir
	url = 'http://svn.python.org/projects/python/branches/py3k'
	print("Checking out Python from {url}".format(**vars()))
	target = os.path.join(test_dir, 'python-py3k')
	cmd = ['svn', 'co', '-q', url, target]
	result = subprocess.Popen(cmd).wait()
	if result != 0:
		print("Checkout failed", file=sys.stderr)
		raise SystemExit(result)
	pcbuild_dir = os.path.join(target, 'pcbuild')

class RoundupTracker(object):
	"""
	An object representing a RoundUp issue (referenced by URL).
	"""
	def __init__(self, url):
		self.url = url

	def get_patch_refs(self):
		return (
			urlparse.urljoin(self.url, link.parent['href'])
			for link in self.find_patch_links()
			)

	@staticmethod
	def patch_number(link):
		number = re.compile(r'\d+(\.\d+)?')
		return float(number.search(link.string).group(0))

	def find_patch_links(self):
		soup = BeautifulSoup(urllib2.urlopen(self.url).read())
		files = soup.find(attrs='files')
		links = files.findAll(text=re.compile(r'.*\.patch'))
		links.sort(key=self.patch_number, reverse=True)
		return links

	def get_patches(self):
		return itertools.imap(Patch.urlopen, self.get_patch_refs())

	def get_latest_patch(self):
		return next(self.get_patches())

class PythonBugTracker(RoundupTracker):
	def __init__(self, id):
		url = 'http://bugs.python.org/issue' + str(id)
		super(PythonBugTracker, self).__init__(url)

class Patch(str):
	"""
	A unified diff object that can be applied to a file or folder.
	Depends on GNU patch.exe being in the path.
	"""
	def __new__(cls, *args, **kwargs):
		return str.__new__(cls, *args)

	def __init__(self, *args, **kwargs):
		self.__dict__.update(kwargs)

	@classmethod
	def urlopen(cls, url):
		filename = urllib.unquote(os.path.basename(url))
		return cls(urllib2.urlopen(url).read(), filename=filename)

	def apply(self, target):
		filename = self.filename
		print("Applying {filename} on {target}".format(**vars()))
		cmd = ['patch', '-p0', '-t', '-d', target]
		proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
		stdout, stderr = proc.communicate(self)
		if proc.returncode != 0:
			print("Error applying patch", file=sys.stderr)
			raise RuntimeError("Error applying patch")

def apply_patch():
	patch = PythonBugTracker(bug_id).get_latest_patch()
	target = os.path.join(test_dir, 'python-py3k')
	patch.apply(target)

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

def do_build(word_size):
	print("building {word_size}-bit python".format(**vars()))
	env_args = {32: [], 64: ['x64']}[word_size]
	env = get_vcvars_env(*env_args)
	cmd_args = {32: [], 64: ['-p', 'x64']}[word_size]
	cmd = construct_build_command(cmd_args)
	proc = subprocess.Popen(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output, stderr = proc.communicate()
	print("result of {word_size}-bit build is {proc.returncode}".format(**vars()))
	return proc.returncode, output

def run_test(*params):
	print("Running regression tests")
	cmd = [
		'rt.bat',
		'-q',
		] + list(params)
	orig_dir = os.getcwd()
	os.chdir(pcbuild_dir)
	proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	output, stderr = proc.communicate()
	if not proc.returncode == 0:
		print("Warning: rt.bat returned {proc.returncode}".format(**vars()))
	os.chdir(orig_dir)
	return proc.returncode, output

def save_results(results, filename):
	filename = os.path.join(os.environ['USERPROFILE'], filename+'.txt')
	code, output = results
	f = open(filename, 'wb')
	f.write(str(code)+'\n')
	f.write(output)

def cleanup():
	cmd = ['cmd', '/c', 'rmdir', '/s', '/q', test_dir]
	res = subprocess.Popen(cmd).wait()
	if not res == 0:
		print("Error cleaning up", file=sys.stderr)
		raise SystemExit(1)

def do_builds():
	init()
	create_test_dir()
	checkout_source()
	apply_patch()
	code, output = do_build(32)
	#code, output = do_build(64)

# orchestrate the test
def orchestrate_test():
	init()
	create_test_dir()
	try:
		checkout_source()
		if not options.no_patch: apply_patch()
		save_results(do_build(32), '32-bit build results')
		save_results(run_test(), '32-bit test results')
		if not options.skip_64_bit:
			save_results(do_build(64), '64-bit build results')
			save_results(run_test('-x64'), '64-bit test results')
	except KeyboardInterrupt:
		print("Cancelled by user")
	finally:
		print("Cleaning up...")
		cleanup()

def handle_command_line():
	get_options()
	if options.clean:
		init(); cleanup()
		return
	if options.just_build:
		do_builds()
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
	parser.add_option('--no-patch', default=False, action="store_true")
	parser.add_option('--skip-64-bit', default=False, action="store_true")
	options, args = parser.parse_args()

if __name__ == '__main__':
	handle_command_line()
