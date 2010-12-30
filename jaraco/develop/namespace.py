from textwrap import dedent
import optparse

# requires path.py (easy_install path.py)
from path import path

try:
	from jaraco.util.string import local_format as lf
except ImportError:
	def local_format(string):
		import inspect
		return string.format(**inspect.currentframe().f_back.f_locals)
	lf = local_format

# dedent and left strip
def DALS(string):
	return dedent(string).lstrip()

_setup_template = """
from setuptools import setup, find_packages
setup_params = dict(
	name='{project_name}',
	version='1.0',
	packages=find_packages(),
	namespace_packages=['{namespace}'],
	zip_safe=False,
)
if __name__ == '__main__':
	setup(**setup_params)
"""

def create_namespace_package(root):
	project_name = root.basename()
	namespace, package = project_name.split('.')
	root.mkdir()
	(root/'setup.py').open('w').write(lf(_setup_template))
	namespace_root = root/namespace
	namespace_root.mkdir()
	ns_decl = '__import__("pkg_resources").declare_namespace(__name__)\n'
	(namespace_root/'__init__.py').open('w').write(ns_decl)
	(namespace_root/package).mkdir()
	(namespace_root/package/'__init__.py').touch()
	return namespace_root/package

def create_namespace_package_cmd():
	parser = optparse.OptionParser()
	options, args = parser.parse_args()
	if not args:
		parser.error('namespace name required')
	root = args.pop(0)
	if args:
		parser.error('unexpected positional arguments')
	create_namespace_package(path(root))

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
