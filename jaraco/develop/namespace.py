from __future__ import print_function

import re
import textwrap
import argparse

import pkg_resources
from path import path

try:
	from jaraco.util.string import local_format as lf
except ImportError:
	def local_format(string):
		import inspect
		return string.format(**inspect.currentframe().f_back.f_locals)
	lf = local_format

def DALS(string):
	"Dedent and left strip"
	return textwrap.dedent(string).lstrip()

_setup_template = (
	pkg_resources.resource_string(__name__, 'setup template.py')
	.decode('utf-8')
)

def tabs_to_spaces(tabs):
	return ' '*4*len(tabs.group(0))

def create_namespace_package(root, indent_with_spaces=False):
	project_name = root.basename()
	namespace, sep, package = project_name.rpartition('.')
	if not root.isdir(): root.mkdir()
	template = DALS(_setup_template)
	if not namespace:
		# remove the namespace_packages declaration
		template = re.sub(r'^\tnamespace_packages.*\n', '', template,
			flags=re.MULTILINE)
		assert not 'namespace_packages' in template
	if indent_with_spaces:
		template = re.sub(r'^\t+', tabs_to_spaces, template,
			flags=re.MULTILINE)
	(root/'setup.py').open('wb').write(lf(template).encode('utf-8'))
	with (root/'README.txt').open('w') as readme:
		print(project_name, file=readme)
		print('='*len(project_name), file=readme)
	(root/'CHANGES.txt').touch()

	with (root/'.hgignore').open('w') as hgignore:
		hgignore.write('build\ndist\n')

	if namespace:
		namespace_root = root/namespace
		namespace_root.mkdir()
		ns_decl = '__import__("pkg_resources").declare_namespace(__name__)\n'
		(namespace_root/'__init__.py').open('wb').write(ns_decl.encode('utf-8'))
		root = namespace_root

	(root/package).mkdir()
	(root/package/'__init__.py').touch()
	return root/package

def create_namespace_package_cmd():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--indent-with-spaces', default=False,
		action='store_true',)
	parser.add_argument('target', help="path to new project",
		type=path)
	args = parser.parse_args()
	create_namespace_package(args.target, args.indent_with_spaces)

def create_namespace_sandbox(root='.'):
	"""
	Create a namespace package with two packages:
		myns.projA
			- contains myns/projA/modA.py
		myns.projB
			- contains a test which references myns.projA.modA
	"""
	root = path(root)
	pkg = create_namespace_package(root / 'myns.projA')
	(pkg/'modA.py').open('w').write(DALS(
		"""
		def funcA():
			print "funcA called"
		"""))
	pkg = create_namespace_package(root / 'myns.projB')
	testdir = root/'myns.projB'/'test'
	testdir.mkdir()
	(testdir/'__init__.py').touch()
	(testdir/'test_basic.py').open('w').write(DALS(
		"""
		from myns.projA.modA import funcA
		def test_simple():
			funcA()
		"""))

if __name__ == '__main__':
	create_namespace_sandbox()
