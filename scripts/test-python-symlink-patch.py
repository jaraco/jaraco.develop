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
from optparse import OptionParser

from jaraco.develop import Results
from jaraco.develop.stage import PythonTestStage

bug_id = 1578269
source_url = 'http://svn.python.org/projects/python/branches/py3k'

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
			options.no_patch or stage.apply_patch(bug_id)
			stage.do_build(32, Results('32-bit build results'), options.get_externals)
			options.just_build or stage.run_test(Results('32-bit test results'))
			if not options.skip_64_bit:
				stage.do_build(64, Results('64-bit build results'), options.get_externals)
				options.just_build or stage.run_test(Results('64-bit test results'), '-x64')
		except KeyboardInterrupt:
			print("Cancelled by user")
		finally:
			if not options.just_build:
				print("Cleaning up...")
				stage.cleanup()

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
