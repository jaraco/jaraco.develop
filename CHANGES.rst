v7.2.2
======

* Fix Python 3.6 compatibility.

v7.2.1
======

* Fixed bug in github.Repo handling (where authentication was missing).

v7.2.0
======

* Add add-github-secret routine.

v7.1.0
======

* Add create-github-release routine.

v7.0.0
======

* Removed many crufty modules and trimmed dependencies.

v6.2.0
======

* macos-build-python now checks that dependencies are installed.

v6.1.0
======

* Improve reliability of macOS build with reference to xz.

v6.0.0
======

* Require Python 3.6 or later.
* Removed 'make-namespace-package' command associated
  functionality in ``namespace`` module.
* Removed Bitbucket-related functionality. Nobody is going
  to need that again.
* Removed Github module. Use `hub <https://hub.github.com/>`_
  command.
* Removed selenium code that is old and with limited utility
  except on Windows.
* Removed all other command-line scripts.

5.0
===

Switch to `pkgutil namespace technique
<https://packaging.python.org/guides/packaging-namespace-packages/#pkgutil-style-namespace-packages>`_
for the ``jaraco`` namespace.

Drop support for Python 3.5.

4.2
===

Updated github to expect a token instead of username/password
in the keyring.

4.1
===

Exposed ``jaraco.develop.lib2to3.patch_for_newlines``.

4.0
===

Refreshed package metadata. Dropped support for Python 3.3.

Added ``jaraco.develop.lib2to3``, which addresses Python #11594
by retaining newlines.

3.0
===

Drop support for Python 3.0.

2.29.1
======

Use ``path.Path`` for compatibility with path.py 10.

2.29
====

Allow creation of Github repositories in an organization.

2.28
====

Moved hosting to Github.

2.27
====

Render README and CHANGES with .rst extensions for nicer rendering
on Github.

2.26
====

Add migration script, adapted from ``bitbucket_issue_migration``.

2.25
====

Add .travis.yml to skeleton.

2.24
====

In project skeleton generation, set default hosting to github.com.

2.23
====

Add github create repo command.

2.22
====

* Include wheels in releases

2.20
====

* Added stub for "extra" dependencies.

2.19
====

* Write templates using LF for line endings.

2.18
====

* Remove documentation link from README in skeleton generation.

2.17
====

* Setup template now includes package data by default.
* Added stub for entry points to define where in the script
  it should appear.

2.16
====

* Regenerated project structure using ``make-namespace-package``.
* Normalized syntax around plat requirements.

2.15
====

* Use setuptools_scm in sphinx config.

2.14
====

* Allow make-namespace-package to complete even when
  the tree already exists.

2.13
====

* Include the jaraco.develop version used to generate the package.

2.12
====

* Add link to documentation from readme.
* Remove changelog from package metadata.
* Include the history in the documentation.

2.11
====

* Drop dependency on jaraco.util.

2.10
====

* Use setuptools_scm.
* Add test = pytest alias.

2.9
===

* Include pytest and sphinx only when indicated.

2.8
===

* Added placeholder for install_requires.
* Use pytest.ini for pytest settings.

2.7
===

* Added sphinx doc and release alias.

2.2
===

* Runs natively on Python 3.

2.1
===

* Specify PyPI for releases.

2.0
===

* Removed 'url' parameter from calls in bitbucket module.
* Now use Requests in favor of restclient for bitbucket operations.

1.10
====

* Added ``add_version`` to ``bitbucket`` module.

1.9
===

* Added command to mark .hg directories as hidden (Windows).

1.8
===

* Added keyring support for bitbucket operations.
* Added command to patch hgrc files in a tree (patch-hgrc).

1.7
===

* Added support for recursive globs in indent module.

1.6.3
=====

* Updated jaraco.develop.msvc to support Python 3.

1.6.2
=====

* create-namespace-package will now also generate non-namespace packages.

1.6.1
=====

* Updated create-bitbucket-repository command so it now passes the new
  required parameter 'scm' (always mercurial).

1.6
===

* Added `compiler` module with a function `can_compile_extension` which
  will check if distutils can likely compile an extension module.

1.5
===

* Added build-python command, which finds Visual Studio, loads the
  appropriate environment, and then builds Python in the current PCBuild
  directory.
* Added vs-upgrade command which will take a Visual Studio project or solution
  file and upgrade it to the latest version.

1.4
===

* Added support for 4-space indentation in namespace package generation.
* Added preliminary bitbucket support (create-repo command).
* Added Python 3 support.

1.3
===

* Added package module (from jaraco.util).
* Added some helpful routines for invoking saucelabs including shortcuts
  for selecting browsers.
* Added a script to create the simple namespace package configuration.
* Added env_tool from the Gryphon project.

1.2
===

* Adding module for patching the msvc9compiler module
* Added command-line options to start-selenium

1.1
===

* Added routines for working with the Core CPython project (building,
  applying patches, etc).

1.0
===

* Initial release
