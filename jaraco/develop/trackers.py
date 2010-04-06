#!python
#-*- coding: utf-8 -*-

from __future__ import absolute_import

from BeautifulSoup import BeautifulSoup
import re
import itertools
import urlparse
import urllib2

from .patch import Patch

class RoundupTracker(object):
	"""
	An object representing a RoundUp issue (referenced by URL).
	"""
	def __init__(self, url):
		self.url = url

	def get_patch_refs(self):
		return (
			urlparse.urljoin(self.url, link.parent['href'])
			for link in self.find_patch_links()
			)

	@staticmethod
	def patch_number(link):
		number = re.compile(r'\d+(\.\d+)?')
		return float(number.search(link.string).group(0))

	def find_patch_links(self):
		soup = BeautifulSoup(urllib2.urlopen(self.url).read())
		files = soup.find(attrs='files')
		links = files.findAll(text=re.compile(r'.*\.patch'))
		links.sort(key=self.patch_number, reverse=True)
		return links

	def get_patches(self):
		return itertools.imap(Patch.urlopen, self.get_patch_refs())

	def get_latest_patch(self):
		return next(self.get_patches())

class PythonBugTracker(RoundupTracker):
	def __init__(self, id):
		url = 'http://bugs.python.org/issue' + str(id)
		super(PythonBugTracker, self).__init__(url)
