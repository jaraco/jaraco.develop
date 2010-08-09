import subprocess
import os
import sys
import optparse

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

def get_options():
	parser = optparse.OptionParser()
	parser.add_option('-j', '--java-vm', default=r'c:\program files\java\jdk\bin\java.exe')
	parser.add_option('-s', '--selenium-jar', default=r'c:\program files\java\selenium-server\selenium-server.jar')
	parser.add_option('-p', '--firefox-profile')
	options, args = parser.parse_args()
	if args:
		parser.error('%prog does not accept any positional arguments')
	return options

def get_firefox_profile(name):
	profile_path = os.path.join(
		os.environ['APPDATA'],'Mozilla','Firefox','Profiles')
	profiles = os.listdir(profile_path)
	for profile in profiles:
		id, sep, profile_name = profile.partition('.')
		if profile_name == name:
			return os.path.join(profile_path, profile)

def start_selenium_server():
	options = get_options()
	env = add_firefox_to_path()
	
	try:
		cmd = [options.java_vm, '-jar', options.selenium_jar]
		if options.firefox_profile:
			p = get_firefox_profile(options.firefox_profile)
			cmd.extend(['-firefoxProfileTemplate', p])
		subprocess.check_call(cmd, env=env)
	except KeyboardInterrupt:
		pass
