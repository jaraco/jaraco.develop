from __future__ import print_function

import re
import textwrap
import argparse
import inspect
import io
import datetime

import pkg_resources
from path import path
from jaraco.functools import compose


def DALS(string):
	"Dedent and left strip"
	return textwrap.dedent(string).lstrip()

def load_template(name, transform=None, context=None):
	if transform is None:
		transform = lambda x: x
	result = pkg_resources.resource_string(__name__, name).decode('utf-8')
	if context is None:
		context = inspect.currentframe().f_back.f_locals
	return transform(result).format(**context)

def to_spaces(script):
	"""
	Replace tab indentation with space indentation.
	"""
	return re.sub(r'^\t+', tabs_to_spaces, script, flags=re.MULTILINE)

def tabs_to_spaces(tabs):
	return ' '*4*len(tabs.group(0))

def remove_namespace_packages(script):
	"remove the namespace_packages declaration"
	return re.sub(r'^\tnamespace_packages.*\n', '', script, flags=re.MULTILINE)

def create_namespace_package(root, indent_with_spaces=False):
	project_name = root.basename()
	year = datetime.date.today().year
	namespace, sep, package = project_name.rpartition('.')
	if not root.isdir(): root.mkdir()
	whitespace = to_spaces if indent_with_spaces else lambda x: x
	namespace_adj = remove_namespace_packages if namespace else lambda x: x
	transform = compose(whitespace, namespace_adj)
	setup_py = load_template('setup template.py', transform=transform)
	io.open(root/'setup.py', 'w', encoding='utf-8').write(setup_py)

	docs = root / 'docs'
	docs.mkdir_p()
	sphinx_i = load_template('sphinx index template.rst', transform)
	io.open(docs/'index.rst', 'w', encoding='utf-8').write(sphinx_i)
	sphinx_c = load_template('sphinx conf template.py', transform)
	io.open(docs/'conf.py', 'w', encoding='utf-8').write(sphinx_c)

	with (root/'README.txt').open('w') as readme:
		print(project_name, file=readme)
		print('='*len(project_name), file=readme)
	(root/'CHANGES.txt').touch()
	with (root/'setup.cfg').open('w') as setupcfg:
		setupcfg.writelines([
			'[aliases]\n',
			'release = sdist build_sphinx upload upload_docs\n',
		])
	with (root/'pytest.ini').open('w') as setupcfg:
		setupcfg.writelines([
			'[pytest]\n',
			'norecursedirs=*.egg .eggs dist build\n',
			'addopts=--doctest-modules\n',
		])

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
