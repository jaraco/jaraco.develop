import urllib.parse

from build.util import project_wheel_metadata as load_metadata
from jaraco.collections import ItemsAsAttributes


class Bunch(dict, ItemsAsAttributes):
    pass


def get_project_metadata():
    _md = load_metadata('.')
    url = _md['Home-page']
    version = _md['Version']
    project = urllib.parse.urlparse(url).path.strip('/')
    return Bunch(locals())
