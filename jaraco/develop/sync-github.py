"""
Sync GitHub metadata repo across all projects.

Metadata includes description, homepage (RTD docs if available) and topics.
"""

import autocommand

from . import filters
from . import git
from . import github
from . import repo
from . import rtd


@autocommand.autocommand(__name__)
def main(
    keyword: filters.Keyword = None,  # type: ignore
    tag: filters.Tag = None,  # type: ignore
):
    for project in filter(tag, filter(keyword, git.projects())):
        with git.temp_checkout(project, depth=1):
            md = repo.get_project_metadata()
            gh = github.Repo.from_project(project)
            gh_metadata = gh.get_metadata()
            # https://github.com/jaraco/pytest-perf/issues/10#issuecomment-1913669951
            # homepage = md.homepage
            homepage = (
                gh_metadata.get('homepage')
                or (project.rtd_url if rtd.rtd_exists(project) else None)
            )
            description = gh_metadata.get('description') or md.summary
            print(f'\n[Metadata for {gh}]')
            print('Homepage:', homepage)
            print('Description:', description)
            print('Topics:', ', '.join(project.topics))
            gh.update_metadata(
                homepage=homepage,
                description=description,
            )
            print('\nUpdated metadata.')
            gh.add_topics(*project.topics)
            print('Added topics.\n')
            print(gh.url)
