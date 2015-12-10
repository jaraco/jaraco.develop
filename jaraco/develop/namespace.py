from __future__ import print_function

import re
import textwrap
import argparse
import inspect
import datetime

import path
import pkg_resources
from jaraco.functools import compose


class Path(path.Path):
	def write_text(self, *args, **kwargs):
		kwargs.setdefault('linesep', '\n')
		kwargs.setdefault('encoding', 'utf-8')
		super(Path, self).write_text(*args, **kwargs)


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
	version = pkg_resources.require('jaraco.develop')[0].version
	namespace, sep, package = project_name.rpartition('.')
	if not root.isdir(): root.mkdir()
	whitespace = to_spaces if indent_with_spaces else lambda x: x
	namespace_adj = remove_namespace_packages if not namespace else lambda x: x
	transform = compose(whitespace, namespace_adj)
	setup_py = load_template('setup template.py', transform=transform)
	(root/'setup.py').write_text(setup_py)

	docs = root / 'docs'
	docs.mkdir_p()
	sphinx_i = load_template('sphinx index template.rst', transform)
	(docs/'index.rst').write_text(sphinx_i)
	sphinx_c = load_template('sphinx conf template.py', transform)
	(docs/'conf.py').write_text(sphinx_c)
	history = load_template('history.rst', transform)
	(docs/'history.rst').write_text(history)

	separator = '=' * len(project_name)
	(root/'README.rst').write_text(DALS("""
		{project_name}
		{separator}
		""").format(**locals()))

	(root/'CHANGES.rst').touch()

	(root/'setup.cfg').write_text(DALS("""
		[aliases]
		release = sdist bdist_wheel build_sphinx upload upload_docs
		test = pytest

		[wheel]
		universal = 1
		"""))

	(root/'pytest.ini').write_text(DALS("""
		[pytest]
		norecursedirs=*.egg .eggs dist build
		addopts=--doctest-modules
		doctest_optionflags=ALLOW_UNICODE ELLIPSIS
		"""))

	(root/'.travis.yml').write_text(DALS("""
		sudo: false
		language: python
		python:
		 - 2.7
		 - 3.5
		script:
		 - pip install -U pytest
		 - python setup.py test
		"""))

	(root/'.hgignore').write_text("build\ndist\n")

	if namespace:
		namespace_root = root/namespace
		namespace_root.mkdir_p()
		ns_decl = '__import__("pkg_resources").declare_namespace(__name__)\n'
		(namespace_root/'__init__.py').write_text(ns_decl)
		root = namespace_root

	(root/package).mkdir_p()
	(root/package/'__init__.py').touch()
	return root/package

def create_namespace_package_cmd():
	parser = argparse.ArgumentParser()
	parser.add_argument('-s', '--indent-with-spaces', default=False,
		action='store_true',)
	parser.add_argument('target', help="path to new project",
		type=Path)
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
	root = Path(root)
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
