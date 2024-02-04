from __future__ import annotations

import autocommand

from . import github


@autocommand.autocommand(__name__)
def run(name, value, project: github.Repo | None = None):
    (project or github.Repo.detect()).add_secret(name, value)
