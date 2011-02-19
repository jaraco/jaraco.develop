from __future__ import print_function

import urllib2
import tarfile
import zipfile
import posixpath
import platform
import os
from textwrap import dedent
import subprocess
from cStringIO import StringIO
import pkg_resources
import shutil
from distutils import msvccompiler

pkg_resources.require('cython')
assert msvccompiler.get_build_version() >= 9.0

def shortest(strings):
	return next(iter(sorted(strings, key=len)))

class LibraryManager():
	@staticmethod
	def zip_topdir(zf):
		dir = shortest(zf.namelist())
		return all(name.startswith(dir) for name in zf.namelist()) and dir

	def get_lib(self, lib):
		url = posixpath.join(self.root, lib)
		print('getting', url)
		u = urllib2.urlopen(url)
		f = StringIO(u.read())
		zf = zipfile.ZipFile(f)
		zf_topdir = self.zip_topdir(zf)
		if zf_topdir:
			dest = '.'
			lib_loc = zf_topdir
		else:
			url_name, ext = os.path.splitext(os.path.basename(url))
			dest = url_name
			lib_loc = url_name
		zf.extractall(dest)
		assert len(os.listdir(lib_loc)) > 1
		assert 'include' in os.listdir(lib_loc)
		custom_handler = 'handle_'+lib_loc.split('-')[0]
		getattr(self, custom_handler, lambda x: None)(lib_loc)
		return lib_loc

	def get_libs(self):
		self.locs = map(self.get_lib, self.sources)

	def get_dirs(self, name):
		dirs = list(posixpath.join('..', loc, name) for loc in self.locs)
		missing = [dir for dir in dirs if not os.path.isdir(dir)]
		assert not missing, "Dirs not found: " + ','.join(missing)
		return dirs


class LibraryManager32(LibraryManager):
	root = 'ftp://ftp.zlatkovic.com/pub/libxml'
	sources = dedent("""
		iconv-1.9.2.win32.zip
		libxml2-2.7.6.win32.zip
		libxslt-1.1.26.win32.zip
		zlib-1.2.3.win32.zip
		""").strip().split()

class LibraryManager64(LibraryManager):
	root = 'http://pecl2.php.net/downloads/php-windows-builds/php-libs/VC9/x64'
	sources = dedent("""
		libiconv-1.12-vc9-x64.zip
		libxml2-2.7.3-vc9-x64.zip
		libxslt-1.1.23-vc9-x64.zip
		zlib-1.2.3-vc9-x64.zip
		""").strip().split()

	def rename_libs(self, lib_root, replacement):
		for orig_file in os.listdir(lib_root):
			new_file = orig_file.replace(*replacement)
			orig_file = os.path.join(lib_root, orig_file)
			new_file = os.path.join(lib_root, new_file)
			if orig_file == new_file: continue
			shutil.copy(orig_file, new_file)

	def handle_libiconv(self, loc):
		"""
		the lib names are off; try renaming
		"""
		lib_root = os.path.join(loc, 'lib')
		self.rename_libs(lib_root, ('libiconv', 'iconv'))

	def handle_zlib(self, loc):
		lib_root = os.path.join(loc, 'lib')
		self.rename_libs(lib_root, ('zlib_a', 'zlib'))

platform_bits = platform.architecture()[0][:2]

def get_source():
	url = 'http://codespeak.net/lxml/lxml-2.3.tgz'
	stream = urllib2.urlopen(url)
	# mode='r|gz' doesn't work as advertised, queue up the whole file in memory
	stream = StringIO(stream.read())
	stream.seek(0)
	tf = tarfile.TarFile.open(fileobj=stream, mode='r:gz')
	m = tf.getmembers()[0]
	assert m.path == m.name
	tf.extractall()
	return m.name

def alter_source(source_dir):
	setup = os.path.join('setup.py')
	f = open(setup, 'r+')
	data = f.read()
	SID = 'STATIC_INCLUDE_DIRS = %r' % lib_manager.get_dirs('include')
	SLD = 'STATIC_LIBRARY_DIRS = %r' % lib_manager.get_dirs('lib')
	data = data.replace('STATIC_INCLUDE_DIRS = []', SID)
	data = data.replace('STATIC_LIBRARY_DIRS = []', SLD)
	f.seek(0)
	f.write(data)

def handle_command_line():
	global lib_manager
	lib_manager = globals()['LibraryManager' + platform_bits]()
	lib_manager.get_libs()
	src = get_source()
	os.chdir(src)
	alter_source(src)
	cmd = 'python setup.py bdist --static'.split()
	subprocess.check_call(cmd)

if __name__ == '__main__':
	handle_command_line()
