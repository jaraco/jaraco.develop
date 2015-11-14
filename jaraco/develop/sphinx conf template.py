#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import setuptools_scm

extensions = [
    'sphinx.ext.autodoc',
]

# General information about the project.
project = '{project_name}'
copyright = '{year} Jason R. Coombs'

# The short X.Y version.
version = setuptools_scm.get_version(root='..', relative_to=__file__)
# The full version, including alpha/beta/rc tags.
release = version

master_doc = 'index'
