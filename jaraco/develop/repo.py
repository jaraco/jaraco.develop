import re
import urllib.parse
import types
import functools

from jaraco.packaging import metadata


def get_project_metadata():
    _md = metadata.load('.')
    url = metadata.hunt_down_url(_md)
    version = _md['Version']
    project = urllib.parse.urlparse(url).path.strip('/')
    name = _md['Name']
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
