
import subprocess

from jaraco.develop import github
import path


repo = path.Path('.')

def modified():
	res = subprocess.check_output(['hg', 'status', '-mar']).decode('utf-8')
	return bool(res)


def run():
	remote = subprocess.check_output(['hg', 'paths', 'default']).decode('utf-8')
	prefix = 'bb://jaraco/'
	if not remote.startswith(prefix):
		return
	_, _, name = remote.partition(prefix)
	name = name.strip()
	print("Working on", name)
	if modified():
		print(repo.getcwd().basename(), 'modified... skipping.')
		return
	update_hgrc()
	try:
		print("created git repo", github.create_repository(name))
	except Exception:
		pass
	get_skeleton()


def update_hgrc():
	hgrc = repo/'.hg/hgrc'
	if not hgrc.isfile():
		return
	text = hgrc.text()
	if 'bb' not in text:
		return
	skeleton_line = 'skeleton = gh://jaraco/skeleton#master\n'
	hgrc.write_text(text.replace('bb://jaraco', 'gh://jaraco') + skeleton_line)


def rename_docs():
	readme = repo / 'README.txt'
	changes = repo / 'CHANGES.txt'
	for file in (readme, changes):
		if file.isfile():
			subprocess.check_call(['hg', 'mv', file, file.replace('.txt', '.rst')])
	if not modified():
		return
	subprocess.check_call(['hg', 'ci', '-m', 'rename docs for Github compatibility'])


def get_skeleton():
	subprocess.check_call(['hg', 'update'])
	rename_docs()
	subprocess.check_call(['hg', 'bookmark', 'master'])
	subprocess.check_call(['hg', 'pull', 'skeleton'])
	subprocess.check_call(['hg', 'bookmark', '-r', 'tip', '-f', 'skeleton'])
	subprocess.check_call(['hg', 'merge', '-r', 'skeleton'])
	subprocess.check_call(['hg', 'ci', '-m', 'Merge with skeleton'])


if __name__ == '__main__':
	run()
