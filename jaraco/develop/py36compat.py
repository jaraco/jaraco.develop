import sys
import functools
import subprocess


params = dict(universal_newlines=True) if sys.version_info < (3, 7) else dict(text=True)
subprocess_run_text = functools.partial(subprocess.run, **params)
