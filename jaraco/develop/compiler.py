import tempfile
import contextlib
import shutil
import mimetypes

from distutils import ccompiler, sysconfig

from jaraco.util.editor import EditableFile

@contextlib.contextmanager
def temp_dir():
	"""
	A context with a temporary directory that's finally wiped.
	"""
	dir = tempfile.mkdtemp()
	try:
		yield dir
	finally:
		shutil.rmtree(dir)

def get_include_dirs():
	"""From distutils.command.build_ext:148"""
	py_include = sysconfig.get_python_inc()
	plat_py_include = sysconfig.get_python_inc(plat_specific=1)
	include_dirs = []
	include_dirs.append(py_include)
	if plat_py_include != py_include:
		include_dirs.append(plat_py_include)
	return include_dirs

class FalseString(str):
	def __nonzero__(self): return False

def can_compile_extension():
	"""
	Put together a compiler much like distutils might and see if it can
	compile the simplest of extensions. Return True if it succeeds, else
	return a string of the error reason (which also resolves to boolean
	False for simple testing).
	"""
	test_compiler_c = "#include <python.h>\n"
	# make sure mimetypes knows the extension for c files
	mimetypes.add_type('text/x-c', '.c')
	with EditableFile(test_compiler_c, 'text/x-c') as file:
		with temp_dir() as output_dir:
			try:
				compiler = ccompiler.new_compiler()
				out = compiler.compile([file.name], output_dir=output_dir,
					include_dirs=get_include_dirs())
				result = True
			except Exception as e:
				result = FalseString(e)
	return result
