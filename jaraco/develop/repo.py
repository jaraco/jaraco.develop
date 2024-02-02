import re
import urllib.parse
import types
import functools

from build.util import project_wheel_metadata as load_metadata


def get_project_metadata():
    _md = load_metadata('.')
    url = _md['Home-page']
    version = _md['Version']
    project = urllib.parse.urlparse(url).path.strip('/')
    name = _md['Name']
    summary = _md.get('Summary')
    return types.SimpleNamespace(**locals())


def substitute_name(match, metadata):
    lookup = dict(
        PROJECT_PATH=metadata.project,
        PROJECT=metadata.name,
        PROJECT_RTD=metadata.name.replace('.', '').lower(),
    )
    return lookup[match.group(0)]


def sub_placeholders(input):
    replacer = functools.partial(substitute_name, metadata=get_project_metadata())
    return re.sub(r'PROJECT\w+', replacer, input)
