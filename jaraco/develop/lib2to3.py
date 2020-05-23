import lib2to3.refactor
import runpy
import functools


def patch_for_newlines():
    """
    Workaround for https://bugs.python.org/issue11594
    """
    lib2to3.refactor._open_with_encoding = functools.partial(open, newline='')


if __name__ == '__main__':
    patch_for_newlines()
    runpy.run_module('lib2to3')
