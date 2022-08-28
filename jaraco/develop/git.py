import subprocess
import posixpath
import importlib.resources as res

import path

from . import github


def resolve(name):
    return f'{github.username()}/' * ('/' not in name) + name


def checkout(project, target: path.Path = path.Path()):
    url = f'gh://{resolve(project)}'
    cmd = ['git', '-C', target, 'clone', url]
    subprocess.check_call(cmd)
    return target / posixpath.basename(project)


def projects():
    source = res.files('jaraco.develop').joinpath('projects.txt')
    return source.read_text().split()


def exists(project, target):
    return target.joinpath(posixpath.basename(resolve(project))).isdir()
