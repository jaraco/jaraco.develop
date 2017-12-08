import lib2to3.refactor
import runpy
import functools


if __name__ == '__main__':
	lib2to3.refactor._open_with_encoding = functools.partial(open, newline='')
	runpy.run_module('lib2to3')
