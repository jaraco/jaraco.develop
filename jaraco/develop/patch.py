#!python
#-*- coding: utf-8 -*-

from __future__ import print_function

import subprocess
import urllib
import urllib2
import sys
import os

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
		filename = urllib.unquote(os.path.basename(url))
		return cls(urllib2.urlopen(url).read(), filename=filename)

	def apply(self, target):
		filename = self.filename
		print("Applying {filename} on {target}".format(**vars()))
		cmd = ['patch', '-p0', '-t', '-d', target]
		proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
		stdout, stderr = proc.communicate(self)
		if proc.returncode != 0:
			print("Error applying patch", file=sys.stderr)
			raise RuntimeError("Error applying patch")

