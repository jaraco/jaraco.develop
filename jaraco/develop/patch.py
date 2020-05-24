import subprocess
import sys
import os
import urllib.request
import urllib.parse


class Patch(str):
    """
    A unified diff object that can be applied to a file or folder.
    Depends on GNU patch.exe being in the path.
    """

    def __new__(cls, *args, **kwargs):
        return str.__new__(cls, *args)

    def __init__(self, *args, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def urlopen(cls, url):
        filename = urllib.parse.unquote(os.path.basename(url))
        return cls(urllib.request.urlopen(url).read(), filename=filename)

    def apply(self, target):
        print(
            "Applying {filename} on {target}".format(
                filename=self.filename, target=target
            )
        )
        cmd = ['patch', '-p0', '-t', '-d', target]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        stdout, stderr = proc.communicate(self)
        if proc.returncode != 0:
            print("Error applying patch", file=sys.stderr)
            raise RuntimeError("Error applying patch")
