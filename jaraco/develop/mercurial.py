import argparse
import re
import logging
import itertools

import path
import jaraco.util.logging

log = logging.getLogger(__name__)

def get_hgrcs(base, recurse=False):
	candidates = (base,)
	if recurse:
		candidates = itertools.chain(candidates, base.walkdirs())
	candidates = (dir for dir in candidates if dir.basename() != '.hg')
	hgrcs = (dir / '.hg' / 'hgrc' for dir in candidates)
	return (hgrc for hgrc in hgrcs if hgrc.isfile())

def replace(filename, pattern, repl):
	with open(filename, 'rb') as file:
		content = file.read()
	new_content = re.sub(pattern, repl, content)
	if new_content == content:
		log.warning("No change in {filename}".format(**vars()))
		return
	with open(filename, 'wb') as file:
		file.write(new_content)

def patch_hgrc():
	"""
	Commands for patching hgrc files in a tree.
	"""
	parser = argparse.ArgumentParser()
	parser.add_argument('--replace', nargs=2)
	parser.add_argument('-r', '--recurse', default=False, action="store_true")
	jaraco.util.logging.add_arguments(parser)
	args = parser.parse_args()
	jaraco.util.logging.setup(args)
	for hgrc in get_hgrcs(path.path('.'), recurse=args.recurse):
		if args.replace:
			replace(hgrc, *args.replace)
