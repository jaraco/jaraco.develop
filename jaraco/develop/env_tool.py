#!python

"""
This script should set up a gryphon environment on a plain vanilla
Ubuntu box (8.04 or 10.04) or a BDC template box
(https://dev.yougov.com/wiki/BDC/Configuration/TheTemplate)
loosely using the technique described in the deploy docs.
https://dev.yougov.com/wiki/Gryphon/DeploymentDocumentation
"""

import sys
import subprocess
import os
import re
import urllib2
import signal
import functools
import posixpath
import optparse
import platform
from textwrap import dedent

class LinuxPlatform(object):
	@staticmethod
	def get_codename():
		return LinuxPlatform.get_cmd_val('-c')

	@staticmethod
	def get_release():
		return LinuxPlatform.get_cmd_val('-r')

	@staticmethod
	def get_cmd_val(param):
		cmd = ['lsb_release', param]
		proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
		stdout, stderr = proc.communicate()
		return stdout.split()[-1]

def get_platform_dist():
	"""
	Workaround for https://bugs.launchpad.net/python/+bug/196526
	"""
	dist = platform.dist()
	if platform.dist()[:2] == ('debian', 'lenny/sid'):
		dist = ('Ubuntu', LinuxPlatform.get_release(), LinuxPlatform.get_codename())
	return dist

def G(path):
	"Get the project from the G repository path"
	G_repo = 'ssh://dev/G'
	return posixpath.join(G_repo, path)

class GEnvironment(object):
	"""
	A base class for describing and manipulating an execution
	environment for G projects.
	"""
	cheeseshop = 'http://cheeseshop'
	mongodb_source = 'http://downloads.mongodb.org/linux/mongodb-linux-x86_64-1.4.3.tgz'
	prerequisites = []
	setuptools_href = 'http://pypi.python.org/packages/%(short_python_ver)s/s/setuptools/setuptools-0.6c11-py%(short_python_ver)s.egg'
	# the directory where the daemontools services are defined
	daemontools_svc = '/etc/service'
	
	@staticmethod
	def get_arg_parser():
		parser = optparse.OptionParser()
		boolean_option = functools.partial(parser.add_option, action="store_true", default=False)
		parser.add_option('-r', '--env-root',
			help="The location where this environment will be created",
			default='~/gryphon-test',)
		boolean_option('-e', '--use-existing',
			help="Modify an existing environment")
		parser.add_option('-i', '--install', action='append',
			help="eggmonster, mongodb, peard, gryphon-source, test-support (multiple allowed)",
			default=[],)
		boolean_option('--ignore-prerequisites')
		boolean_option('--run-tests')
		return parser

	def __init__(self, options):
		self.env_root = os.path.expanduser(options.env_root)
		self.options = options

	@staticmethod
	def get_platform_class():
		for env_cls in (HardyGEnvironment, LucidGEnvironment, RedhatGEnvironment):
			if env_cls.matches_system():
				return env_cls

	def get_dirs(self):
		return dict(
			env_root = self.env_root,
			sources = os.path.join(self.env_root, 'src'),
		)

	@classmethod
	def matches_system(cls):
		dist = getattr(cls, 'dist', ())
		return get_platform_dist() == dist

	@staticmethod
	def handle_command_line():
		cls = GEnvironment.get_platform_class()
		parser = cls.get_arg_parser()
		options, args = parser.parse_args()
		env = cls(options, *args)
		env.check_python_version()
		env.check_prerequisites()
		env.check_cheeseshop()
		if not options.use_existing:
			env.check_target_does_not_exist()
			os.makedirs(env.env_root)
			env.patch_Popen()
			env.install_setuptools()
			env.install_virtualenv()
			env.create_virtualenv()
			env.set_default_encoding()
		else:
			env.patch_Popen()
		# install cython (LXML doesn't compile without it)
		env.easy_install('cython==0.12.1')
		# lxml isn't installing properly from the cheeseshop
		env.easy_install('lxml==2.2.2', find_links=[])
		if options.run_tests and 'test-support' not in options.install:
			options.install.append('test-support')
		for aspect in options.install:
			aspect = aspect.replace('-', '_')
			method = getattr(env, 'install_' + aspect)
			method()

	def install_gryphon_source(self):
		self.install_mercurial()
		self.install_gryphon()

	def install_pear(self):
		self.easy_install('pear>=2.1,<=2.2dev')
		# pear requires eventful, but apparently doesn't declare such.
		# pyevent 0.4 (in development) doesn't appear to work on ubuntu 8.04, so use the old verison
		spec = 'event' if sys.version_info >= (2,6) else 'event==0.3.2_pmx'
		self.easy_install(spec)
		self.easy_install('eventful')

	def install_test_support(self):
		# testing requires a few more packages
		list(map(self.easy_install, ['paver', 'py>=1.3.1', 'dingus>=0.3dev']))

	def install_mercurial(self):
		"Get mercurial so we can checkout sources"
		self.easy_install('mercurial>=1.6')

	def set_default_encoding(self):
		"set utf-8 as the default encoding for this environment"
		site_customize = os.path.join(self.env_root, 'lib', self.python_name, 'sitecustomize.py')
		open(site_customize, 'a').write("import sys\nsys.setdefaultencoding('utf-8')\n")



	def create_virtualenv(self):
		"now that we have virtualenv, we can create the virtual environment"
		cmd = [os.path.join(self.env_root, 'bin', 'virtualenv'), '--no-site-packages', self.env_root]
		res = self.Popen(cmd).wait()
		if not res == 0:
			env_root = self.env_root
			print "Error creating virtual environment in %(env_root)s" % vars()
			raise SystemExit(6)
			
		# from here out, virtualenv handles the Python path, so we can unset
		#  the environment variable
		del os.environ['PYTHONPATH']


	def install_virtualenv(self):
		"install virtualenv into the new python environment"
		cmd = [os.path.join(self.env_root, 'bin', 'easy_install'), '--prefix', self.env_root, 'virtualenv']
		res = self.Popen(cmd).wait()
		if not res == 0:
			print "Error installing virtualenv"
			raise SystemExit(5)

	def install_setuptools(self):
		"""
		get setuptools (0.6c9 or later is required by pymongo)
		"""
		# Here we install setuptools and virtualenv into the python_prefix dir

		short_python_ver = self.python_ver
		url = self.setuptools_href % vars()

		# create the libs dir and add it to the environment
		python_libs = os.path.join(self.env_root, 'lib', self.python_name, 'site-packages')
		os.makedirs(python_libs)
		os.environ['PYTHONPATH'] = python_libs

		# download setuptools
		setuptools_installer_filename,_,_ = os.path.basename(url).partition('#')
		# we can't pass the data directly to sh because it will ignore the
		#  --prefix option, so save it to a file instead.
		setuptools_installer_path = os.path.join(self.env_root, setuptools_installer_filename)
		data = urllib2.urlopen(url).read()
		open(setuptools_installer_path, 'wb').write(data)
		# on Unix, the setuptools egg is a shell archive, and is installed by
		#  executing the archive under sh. Install it with the --prefix option
		#  so it's installed independent of the system libs.
		cmd = ['sh', setuptools_installer_path, '--prefix', self.env_root]
		res = self.Popen(cmd).wait()
		# we don't need the setuptools installer anymore, so delete it
		os.remove(setuptools_installer_path)
		if not res == 0:
			print "Error installing setuptools"
			raise SystemExit(4)

		
	def patch_Popen(self):
		"""
		Create a log file and patch Popen to redirect stdout to that
		file by default.
		"""
		deploy_log_filename = os.path.join(self.env_root, 'deploy.log')
		print "Logging to", deploy_log_filename
		deploy_log = open(deploy_log_filename, 'w')
		@functools.wraps(subprocess.Popen)
		def redirected_Popen(*args, **kwargs):
			kwargs.setdefault('stdout', deploy_log)
			return subprocess.Popen(*args, **kwargs)

		self.Popen = redirected_Popen


	def check_target_does_not_exist(self):
		if os.path.exists(self.env_root):
			env_root = self.env_root
			print "ROOT directory %(env_root)s already exists. Remove it or set a different target." % vars()
			raise SystemExit(3)


	def check_python_version(self):
		if not self.correct_python_version():
			print 'Python 2.5 or later is required'
			raise SystemExit(1)

	def correct_python_version(self):
		return sys.version_info >= (2,5)

	@property
	def python_name(self):
		"Create a string like 'python2.5' from the version_info"
		return 'python' + self.python_ver

	@property
	def python_ver(self):
		"Create a string like '2.5' from the version_info"
		return '.'.join(map(str, sys.version_info[:2]))

	def get_prereqs(self):
		return self.system_prerequisites

	def has_prerequisites(self):
		# make sure the prerequites are installed
		return all(self.package_installed(p) for p in self.get_prereqs())

	def check_cheeseshop(self):
		try: urllib2.urlopen(self.cheeseshop)
		except StandardError:
			print 'error: cannot reach %s' % self.cheeseshop
			raise SystemExit(3)

	def easy_install(self, requirement, find_links=None):
		"""
		Easy_install something into the environment. I suspect this is
		similar to what ezpmx does, except that it will install packages
		from PyPI as well.
		"""
		if find_links is None:
			find_links = [self.cheeseshop]
		cmd = [
			os.path.join(self.env_root, 'bin', 'easy_install'),
			requirement,
			]
		for link in find_links:
			cmd[-1:-1] = ['-f', link]
		
		res = self.Popen(cmd).wait()
		if not res == 0:
			print "Error installing %(requirement)s" % vars()
			raise SystemExit(7)

	def install_mongodb(self):
		# install mongodb
		import tarfile
		from StringIO import StringIO
		mongo_tgz_data = StringIO(urllib2.urlopen(self.mongodb_source).read())
		mongo_tar = tarfile.TarFile.open(fileobj=mongo_tgz_data, mode='r:gz')
		mongo_dest,_,_ = mongo_tar.getnames()[0].partition('/')
		mongo_tar.extractall(self.env_root)
		mongo_dest_path = os.path.join(self.env_root, mongo_dest)
		# make a link as $ENV/mongodb for convenience
		mongo_link = os.path.join(self.env_root, 'mongodb')
		if os.path.exists(mongo_link):
			os.unlink(mongo_link)
		os.symlink(mongo_dest_path, mongo_link)
		# create a directory for mongodb to store its data.
		mongodb_data = os.path.join(self.env_root, 'var', 'lib', 'mongodb')
		os.path.isdir(mongodb_data) or os.makedirs(mongodb_data)
		# create a directory for mongodb to log its status.
		self.create_log_dir()

	def create_log_dir(self):
		target = os.path.join(self.env_root, 'var', 'log')
		os.path.isdir(target) or os.makedirs(target)

	@property
	def sources(self):
		return os.path.join(self.env_root, 'src')

	def checkout_source(self, path, args=[], as_version=None):
		"""
		Check out a project from the supplied path.
		If args are supplied, they're passed directly to mercurial
		If as_version is supplied, the setup.py will be modified to
		specify the given version.
		"""
		dest_name = os.path.basename(path)
		dest_path = os.path.join(self.sources, dest_name)
		mercurial = os.path.join(self.env_root, 'bin', 'hg')
		
		cmd = [mercurial, 'clone', path, dest_path,] + args
		
		res = self.Popen(cmd).wait()
		if not res == 0:
			print "Failed to check out %(path)s" % vars()
			raise SystemExit(8)

		# add find_links to setup.cfg so it will use the cheeseshop
		setup_cfg_file = os.path.join(dest_path, 'setup.cfg')
		cheeseshop = self.cheeseshop
		content = '\n[easy_install]\nfind_links=%(cheeseshop)s\n' % vars()
		open(setup_cfg_file, 'a').write(content)

		if as_version:
			setup_py_file = os.path.join(dest_path, 'setup.py')
			setup_py = open(setup_py_file).read()
			setup_py = re.sub('version=.*,', 'version=%r,' % as_version, setup_py)
			open(setup_py_file, 'w').write(setup_py)

	def setup(self, project, *actions):
		"""
		run setup.py on the checked out source with the supplied actions
		such as "develop" or "install" (defaults to install)
		"""
		if not actions: actions = ['install']
		cwd = os.path.join(self.sources, project)
		cmd = [os.path.join(self.env_root, 'bin', 'python'), 'setup.py']
		cmd.extend(actions)
		res = self.Popen(cmd, cwd=cwd).wait()
		if not res == 0:
			print "Error running", subprocess.list2cmdline(cmd), 'in', cwd
			raise SystemExit(10)

	def install_gryphon(self):
		"""
		install the latest Gryphon from the repo
		"""
		# Gryphon setup.py requires pmxtools be installed first
		self.easy_install('pmxtools>=0.15.33')
		self.checkout_source(G('gryphon'))
		self.setup('gryphon', 'develop')

	def run_tests(self):
		print "\n***** Running tests *****"
		os.chdir(os.path.join(self.sources, 'gryphon'))
		cmd = [os.path.join(self.env_root, 'bin', 'paver'), 'test']
		test_out_file = open(os.path.join(self.env_root, 'test results.out'), 'w')
		res = self.Popen(cmd, stdout=test_out_file).wait()
		print "Tests completed with exit code", res

	def install_eggmonster(self):
		self.easy_install('eggmonster')
		# eggmonster will log here
		log_dir = os.path.join(self.env_root, 'var', 'log', 'eggmonster')
		os.makedirs(log_dir)
		# service definitions here and in ./log
		em_svc = os.path.join(self.env_root, 'etc', 'eggmonster', 'service')
		em_log_svc = os.path.join(em_svc, 'log')
		os.makedirs(em_log_svc)
		monster_launchd = os.path.join(self.env_root, 'bin', 'monster_launchd')
		env_bin = os.path.join(self.env_root, 'bin')
		open(os.path.join(em_svc, 'run'), 'w').write(dedent("""
			#!/bin/sh
			export PATH=%(env_bin)s:$PATH
			export PYTHONUNBUFFERED=yes
			export EGGMONSTER_MASTER=http://eggmasterdirect.polimetrix.com:8000
			export EGGMONSTER_CHEESESHOP=http://cheeseshop.polimetrix.com
			exec 2>&1
			exec %(monster_launchd)s -u root
			""").lstrip() % vars())
		open(os.path.join(em_log_svc, 'run'), 'w').write(dedent("""
			#!/bin/sh
			exec multilog t n25 s10000000 %(log_dir)s
			""").lstrip() % vars())
		monster_link = os.path.join(self.daemontools_svc, 'monster-client')
		os.symlink(em_svc, monster_link)


class Ubuntu(object):
	system_prerequisites = [
		'build-essential',
		'python-dev',
		'libevent-dev',
		'libxml2-dev',
		'libxslt1-dev',
		'libfreetype6-dev',
		'zlib1g-dev',
		'libreadline-dev',
		]

	@staticmethod
	def package_installed(pkg_name):
		"""
		Return True only if pkg_name is installed
		
		(Assumes debian and uses dpkg)
		"""
		# for some reason, if Python is run with -i, dpkg compresses the
		#  output into 80 columns (or so), such that the package names
		#  aren't returned in full, so prevent this with an environment
		#  variable.
		env = dict(os.environ)
		env.update(COLUMNS='1024')
		proc = subprocess.Popen("dpkg -l".split(), env=env, stdout=subprocess.PIPE)
		stdout, stderr = proc.communicate()
		lines = stdout.split('\n')
		items = [line.split() for line in lines if len(line.split()) > 1]
		# package names are the second item in the list
		package_names = zip(*items)[1]
		# if pkg_name is a callable, just call it on package_names
		if hasattr(pkg_name, '__call__'):
			return pkg_name(package_names)
		return pkg_name in package_names

	def check_prerequisites(self):
		if not self.has_prerequisites():
			prereqs = self.get_prereqs()
			missing = [str(p) for p in prereqs if not self.package_installed(p)]
			print "You are missing %d prerequisites:" % len(missing)
			print 'use sudo apt-get install -y ' + ' '.join(missing)
			if not self.options.ignore_prerequisites:
				raise SystemExit(2)

class RedhatGEnvironment(GEnvironment):
	dist = ('redhat', '4.5', 'Final')		
	def check_prerequisites(self):
		pass

class HardyGEnvironment(Ubuntu, GEnvironment):
	dist = ('Ubuntu', '8.04', 'hardy')
	system_prerequisites = list(Ubuntu.system_prerequisites)
	system_prerequisites.remove('libreadline-dev')
	system_prerequisites.append('libreadline5-dev')

class LucidGEnvironment(Ubuntu, GEnvironment):
	dist = ('Ubuntu', '10.04', 'lucid')
	def get_prereqs(self):
		prereqs = super(LucidGEnvironment, self).get_prereqs()
		if self.options.install_eggmonster:
			prereqs += ['daemontools-run']
		return prereqs

if __name__ == '__main__': GEnvironment.handle_command_line()
