import subprocess
import os
import sys

def find_firefox_win32():
	import _winreg
	from jaraco.windows.registry import key_subkeys
	key = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, 'Software\Wow6432Node\Mozilla\Mozilla Firefox')
	ver_key = next(key_subkeys(key))
	ver_key = _winreg.OpenKey(key, ver_key)
	main = _winreg.OpenKey(ver_key, 'Main')
	install_loc, typ = _winreg.QueryValueEx(main, 'Install Directory')
	return install_loc

def find_firefox_linux2():
	raise NotImplementedError()

def add_firefox_to_path():
	env = dict(os.environ)
	firefox_finder = globals().get('find_firefox_'+sys.platform)
	try:
		loc = firefox_finder()
		env['PATH'] = str(os.path.pathsep.join((env['PATH'], loc)))
	except StandardError:
		pass
	return env

def start_selenium_server(
	java = r'c:\program files\java\jdk\bin\java.exe',
	selenium = r'c:\program files\java\selenium-server\selenium-server.jar'):
	env = add_firefox_to_path()
	try:
		subprocess.check_call([java, '-jar', selenium], env=env)
	except KeyboardInterrupt:
		pass
