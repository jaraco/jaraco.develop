import functools
import re
import types
import urllib.parse

import jaraco.packaging.metadata


def get_project_metadata():
    return process(jaraco.packaging.metadata.load('.'))


def process(metadata):
    url = jaraco.packaging.metadata.hunt_down_url(metadata)
    version = metadata['Version']
    project = urllib.parse.urlparse(url).path.strip('/')
    name = metadata['Name']
    return types.SimpleNamespace(**locals())


def substitute_name(match, metadata):
    subs = process(metadata)
    lookup = dict(
        PROJECT_PATH=subs.project,
        PROJECT=subs.name,
        PROJECT_RTD=subs.name.replace('.', '').lower(),
    )
    return lookup[match.group(0)]


def sub_placeholders(input, metadata):
    replacer = functools.partial(substitute_name, metadata=metadata)
    return re.sub(r'PROJECT\w+', replacer, input)
