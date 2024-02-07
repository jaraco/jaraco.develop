.. image:: https://img.shields.io/pypi/v/jaraco.develop.svg
   :target: https://pypi.org/project/jaraco.develop

.. image:: https://img.shields.io/pypi/pyversions/jaraco.develop.svg

.. image:: https://github.com/jaraco/jaraco.develop/actions/workflows/main.yml/badge.svg
   :target: https://github.com/jaraco/jaraco.develop/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v2.json
    :target: https://github.com/astral-sh/ruff
    :alt: Ruff

.. image:: https://readthedocs.org/projects/jaracodevelop/badge/?version=latest
   :target: https://jaracodevelop.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2024-informational
   :target: https://blog.jaraco.com/skeleton

This package includes a collection of libraries and scripts used by `jaraco <https://www.jaraco.com>`_ and many of the `projects maintained by jaraco <https://pypi.org/user/jaraco>`_.

It includes facilities for managing scores of repositories with SCM tools like Git, working with Read the Docs, determining release versions from pertinent changes, synchronizing related histories, automatically resolving known merge conflicts, and more.

Many of the modules in this package are executable using ``runpy`` (e.g. ``python -m jaraco.develop.macos-build-python``).

Although this package is built on assumptions about jaraco's workflow, these routines are provided here for shared use across those projects, transparency of operations, and for potential re-use. Contributions and feedback are welcome.
