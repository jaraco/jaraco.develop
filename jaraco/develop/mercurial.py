import argparse
import re
import logging
import itertools
import importlib

import path
import jaraco.logging

log = logging.getLogger(__name__)


def get_hgrcs(base, recurse=False):
    hg_dirs = get_hg_dirs(base, recurse)
    return (dir / 'hgrc' for dir in hg_dirs if (dir / 'hgrc').isfile())


def get_hg_dirs(base, recurse=False):
    candidates = (base,)
    if recurse:
        candidates = itertools.chain(candidates, base.walkdirs())
    candidates = (dir for dir in candidates if dir.basename() != '.hg')
    hg_dirs = (dir / '.hg' for dir in candidates if (dir / '.hg').isdir())
    return hg_dirs


def replace(filename, pattern, repl):
    with open(filename, 'r') as file:
        content = file.read()
    new_content = re.sub(pattern, repl, content)
    if new_content == content:
        log.warning("No change in {filename}".format(**vars()))
        return
    with open(filename, 'w') as file:
        file.write(new_content)


def patch_hgrc():
    """
    Commands for patching hgrc files in a tree.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--replace', nargs=2)
    parser.add_argument('-r', '--recurse', default=False, action="store_true")
    jaraco.logging.add_arguments(parser)
    args = parser.parse_args()
    jaraco.logging.setup(args, format="%(levelname)s:%(message)s")
    for hgrc in get_hgrcs(path.Path('.'), recurse=args.recurse):
        if args.replace:
            replace(hgrc, *args.replace)


def hide_hg_dirs():
    """
    Only useful on Windows, mark the .hg directory as hidden.
    """
    fs = importlib.import_module('jaraco.windows.filesystem')
    parser = argparse.ArgumentParser()
    parser.add_argument('-r', '--recurse', default=False, action="store_true")
    jaraco.logging.add_arguments(parser)
    args = parser.parse_args()
    jaraco.logging.setup(args, format="%(levelname)s:%(message)s")
    for hg_dir in get_hg_dirs(path.Path('.'), recurse=args.recurse):
        # make the file hidden
        fs.SetFileAttributes(hg_dir, 'hidden')
