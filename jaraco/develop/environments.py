"""
Classes for managing virtual execution environments (including such
things as a Python virtual environment).
"""

import sys
import subprocess
import os
import re
import functools
import optparse
import platform
import urllib.request


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


class Environment(object):
    """
    A base class for describing and manipulating an execution
    environment.
    """

    install_options = []  # type: ignore

    @classmethod
    def get_arg_parser(cls):
        parser = optparse.OptionParser()
        boolean_option = functools.partial(
            parser.add_option, action="store_true", default=False
        )
        parser.add_option(
            '-r',
            '--env-root',
            help="The location where this environment will be created",
            default='~/env',
        )
        boolean_option('-e', '--use-existing', help="Modify an existing environment")
        if cls.install_options:
            parser.add_option(
                '-i',
                '--install',
                action='append',
                help=', '.join(cls.install_options) + ' (multiple allowed)',
                default=[],
            )
        return parser

    def __init__(self, options):
        self.env_root = os.path.expanduser(options.env_root)
        self.options = options

    def get_dirs(self):
        return dict(env_root=self.env_root, sources=os.path.join(self.env_root, 'src'),)

    @classmethod
    def matches_system(cls):
        dist = getattr(cls, 'dist', ())
        return get_platform_dist() == dist

    def patch_Popen(self):
        """
        Create a log file and patch Popen to redirect stdout to that
        file by default.
        """
        deploy_log_filename = os.path.join(self.env_root, 'deploy.log')
        print("Logging to", deploy_log_filename)
        deploy_log = open(deploy_log_filename, 'w')

        @functools.wraps(subprocess.Popen)
        def redirected_Popen(*args, **kwargs):
            kwargs.setdefault('stdout', deploy_log)
            return subprocess.Popen(*args, **kwargs)

        self.Popen = redirected_Popen

    def check_target_does_not_exist(self):
        if os.path.exists(self.env_root):
            print(
                "ROOT directory {self.env_root} already exists. Remove it"
                " or set a different target.".format(**vars())
            )
            raise SystemExit(3)

    ##
    system_prerequisites = []  # type: ignore

    def check_prerequisites(self):
        if self.has_prerequisites():
            return
        prereqs = self.get_prereqs()
        missing = [str(p) for p in prereqs if not self.package_installed(p)]
        print("You are missing %d prerequisites:" % len(missing))
        print('use sudo apt-get install -y ' + ' '.join(missing))
        if not self.options.ignore_prerequisites:
            raise SystemExit(2)

    def get_prereqs(self):
        return self.system_prerequisites

    def has_prerequisites(self):
        # make sure the prerequites are installed
        return all(self.package_installed(p) for p in self.get_prereqs())

    def install_mongodb(self):
        # install mongodb
        import tarfile
        from StringIO import StringIO

        url = self.mongodb_source
        mongo_tgz_data = StringIO(urllib.request.urlopen(url).read())
        mongo_tar = tarfile.TarFile.open(fileobj=mongo_tgz_data, mode='r:gz')
        mongo_dest, _, _ = mongo_tar.getnames()[0].partition('/')
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


class VirtualEnvSupport:
    setuptools_href = (
        'http://pypi.python.org/packages/%(short_python_ver)s/'
        's/setuptools/setuptools-0.6c11-py%(short_python_ver)s.egg'
    )

    def create_virtualenv(self):
        "now that we have virtualenv, we can create the virtual environment"
        cmd = [
            os.path.join(self.env_root, 'bin', 'virtualenv'),
            '--no-site-packages',
            self.env_root,
        ]
        res = self.Popen(cmd).wait()
        if not res == 0:
            print(
                "Error creating virtual environment in {self.env_root}".format(**vars())
            )
            raise SystemExit(6)

        # from here out, virtualenv handles the Python path, so we can unset
        #  the environment variable
        del os.environ['PYTHONPATH']

    def install_virtualenv(self):
        "install virtualenv into the new python environment"
        cmd = [
            os.path.join(self.env_root, 'bin', 'easy_install'),
            '--prefix',
            self.env_root,
            'virtualenv',
        ]
        res = self.Popen(cmd).wait()
        if not res == 0:
            print("Error installing virtualenv")
            raise SystemExit(5)

    def install_setuptools(self):
        """
        get setuptools
        """
        # Here we install setuptools and virtualenv into the python_prefix dir

        url = self.setuptools_href % dict(short_python_ver=self.python_ver)

        # create the libs dir and add it to the environment
        python_libs = os.path.join(
            self.env_root, 'lib', self.python_name, 'site-packages'
        )
        os.makedirs(python_libs)
        os.environ['PYTHONPATH'] = python_libs

        # download setuptools
        setuptools_installer_filename, _, _ = os.path.basename(url).partition('#')
        # we can't pass the data directly to sh because it will ignore the
        #  --prefix option, so save it to a file instead.
        setuptools_installer_path = os.path.join(
            self.env_root, setuptools_installer_filename
        )
        data = urllib.request.urlopen(url).read()
        open(setuptools_installer_path, 'wb').write(data)
        # on Unix, the setuptools egg is a shell archive, and is installed by
        #  executing the archive under sh. Install it with the --prefix option
        #  so it's installed independent of the system libs.
        cmd = ['sh', setuptools_installer_path, '--prefix', self.env_root]
        res = self.Popen(cmd).wait()
        # we don't need the setuptools installer anymore, so delete it
        os.remove(setuptools_installer_path)
        if not res == 0:
            print("Error installing setuptools")
            raise SystemExit(4)

    def check_cheeseshop(self):
        try:
            urllib.request.urlopen(self.cheeseshop)
        except Exception:
            print('error: cannot reach %s' % self.cheeseshop)
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
            print("Error installing %(requirement)s" % vars())
            raise SystemExit(7)


class PythonEnvironment(VirtualEnvSupport, Environment):
    @staticmethod
    def handle_command_line():
        cls = PythonEnvironment
        parser = cls.get_arg_parser()
        options, args = parser.parse_args()
        env = cls(options, *args)
        env.check_prerequisites()
        env.setup_environment()

    def setup_environment(self):
        if not self.options.use_existing:
            self.check_target_does_not_exist()
            os.makedirs(self.env_root)
            self.patch_Popen()
            self.install_setuptools()
            self.install_virtualenv()
            self.create_virtualenv()
            self.set_default_encoding()
        else:
            self.patch_Popen()

    def install_mercurial(self):
        "Get mercurial so we can checkout sources"
        self.easy_install('mercurial>=1.6')

    def set_default_encoding(self):
        "set utf-8 as the default encoding for this environment"
        site_customize = os.path.join(
            self.env_root, 'lib', self.python_name, 'sitecustomize.py'
        )
        open(site_customize, 'a').write("import sys\nsys.setdefaultencoding('utf-8')\n")

    @property
    def python_name(self):
        "Create a string like 'python2.5' from the version_info"
        return 'python' + self.python_ver

    @property
    def python_ver(self):
        "Create a string like '2.5' from the version_info"
        return '.'.join(map(str, sys.version_info[:2]))


class MercurialSupport:
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

        cmd = [mercurial, 'clone', path, dest_path] + args

        res = self.Popen(cmd).wait()
        if not res == 0:
            print("Failed to check out %(path)s" % vars())
            raise SystemExit(8)

        # add find_links to setup.cfg so it will use the cheeseshop
        setup_cfg_file = os.path.join(dest_path, 'setup.cfg')
        content = '\n[easy_install]\nfind_links={self.cheeseshop}\n'.format(**vars())
        open(setup_cfg_file, 'a').write(content)

        if as_version:
            setup_py_file = os.path.join(dest_path, 'setup.py')
            setup_py = open(setup_py_file).read()
            setup_py = re.sub('version=.*,', 'version=%r,' % as_version, setup_py)
            open(setup_py_file, 'w').write(setup_py)


if __name__ == '__main__':
    PythonEnvironment.handle_command_line()
