import subprocess


def close_branch(name, message="Closing inactive branch"):
    cmd = ['hg', 'update', name]
    subprocess.check_call(cmd)
    cmd = ['hg', 'commit', '--close-branch', '-m', message]
    subprocess.check_call(cmd)


def get_inactive_branches():
    cmd = ['hg', 'branches']
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in proc.stdout:
        # line looks like
        # <name>, ws, <id>:<rev>, ' (inactive)'?
        line, sep, last = line.strip().rpartition(' ')
        if last != ('(inactive)'):
            continue
        name, sep, rev = line.rpartition(' ')
        name = name.rstrip()
        yield name
    proc.wait()


def main():
    map(close_branch, get_inactive_branches())


if __name__ == '__main__':
    main()
