from __future__ import annotations

import autocommand

from . import github
from . import repo


@autocommand.autocommand(__name__)
def run(project: github.Repo | None = None):
    md = repo.get_project_metadata()
    (project or github.Repo.detect()).create_release(tag=f'v{md.version}')
