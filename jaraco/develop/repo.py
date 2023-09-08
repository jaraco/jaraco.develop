import urllib.parse
import types

from build.util import project_wheel_metadata as load_metadata


def get_project_metadata():
    _md = load_metadata('.')
    url = _md['Home-page']
    version = _md['Version']
    project = urllib.parse.urlparse(url).path.strip('/')
    return types.SimpleNamespace(**locals())
