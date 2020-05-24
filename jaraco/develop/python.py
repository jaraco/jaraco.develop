"""
Support for developing CPython core
"""

import os
import subprocess
from optparse import OptionParser
from argparse import ArgumentParser

from jaraco.develop.trackers import PythonBugTracker
from .vstudio import VisualStudio


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


def find_in_path(filename, search_path):
    if isinstance(search_path, str):
        search_path = search_path.split(os.path.pathsep)
    candidates = [os.path.join(root, filename) for root in search_path]
    matches = filter(os.path.exists, candidates)
    return next(matches)


def build_python():
    parser = ArgumentParser()
    parser.add_argument(
        '-t', '--target', dest='targets', default=[], action='append',
    )
    options = parser.parse_args()
    vs = VisualStudio.find()
    env = vs.get_vcvars_env()
    msbuild = find_in_path('msbuild.exe', env['Path'])
    cmd = [msbuild, 'pcbuild.sln', '/p:Configuration=Release', '/p:Platform=x64']
    if options.targets:
        cmd[2:2] = ['/target:' + ';'.join(options.targets)]
    subprocess.check_call(cmd, env=env)
