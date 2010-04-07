#-*- coding: utf-8 -*-

from optparse import OptionParser
from jaraco.develop.trackers import PythonBugTracker

def apply_python_bug_patch(bug_id, target):
	patch = PythonBugTracker(bug_id).get_latest_patch()
	patch.apply(target)

def apply_python_bug_patch_cmd():
	options, args = OptionParser().parse_args()
	bug_id = int(args.pop())
	target = args.pop()
	return apply_python_bug_patch(bug_id, target)