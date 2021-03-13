

def write_hook(cmd, basename, filename):
    import pathlib
    pathlib.Path(filename).write_text('hook is at foo/bar.py')
