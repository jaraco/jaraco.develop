import urllib.parse

import pep517.meta
from jaraco.collections import ItemsAsAttributes


class Bunch(dict, ItemsAsAttributes):
    pass


def get_project_metadata():
    dist = pep517.meta.load('.')
    url = dist.metadata['Home-page']
    version = dist.version
    project = urllib.parse.urlparse(url).path.strip('/')
    return Bunch(locals())
