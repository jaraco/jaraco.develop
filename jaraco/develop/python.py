#!python
#-*- coding: utf-8 -*-

import os

from optparse import OptionParser
from jaraco.develop.trackers import PythonBugTracker

def apply_python_bug_patch(bug_id, target):
	patch = PythonBugTracker(bug_id).get_latest_patch()
	patch.apply(target)

def apply_python_bug_patch_cmd():
	options, args = OptionParser().parse_args()
	bug_id, target = args
	bug_id = int(bug_id)
	return apply_python_bug_patch(bug_id, target)

def Results(filename):
	filename = os.path.expanduser('~/{filename}.txt'.format(**vars()))
	return open(filename, 'wb')
