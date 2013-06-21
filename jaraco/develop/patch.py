#!python
#-*- coding: utf-8 -*-

from __future__ import print_function

import subprocess
import sys
import os

try:
	import urllib.request as urllib_request
	import urllib.parse as urllib_parse
except ImportError:
	import urllib2 as urllib_request
	import urlparse as urllib_parse

class Patch(str):
	"""
	A unified diff object that can be applied to a file or folder.
	Depends on GNU patch.exe being in the path.
	"""
	def __new__(cls, *args, **kwargs):
		return str.__new__(cls, *args)

	def __init__(self, *args, **kwargs):
		self.__dict__.update(kwargs)

	@classmethod
	def urlopen(cls, url):
		filename = urllib_parse.unquote(os.path.basename(url))
		return cls(urllib_request.urlopen(url).read(), filename=filename)

	def apply(self, target):
		print("Applying {filename} on {target}".format(
			filename=self.filename, target=target))
		cmd = ['patch', '-p0', '-t', '-d', target]
		proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
		stdout, stderr = proc.communicate(self)
		if proc.returncode != 0:
			print("Error applying patch", file=sys.stderr)
			raise RuntimeError("Error applying patch")
