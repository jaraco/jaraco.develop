import functools

def _add_MANIFEST_postarg(link_method):
	# If the method was passed in Python 2, grab the function from the
	#  UnboundMethod wrapper.
	func = getattr(link_method, 'im_func', link_method)
	@functools.wraps(func)
	def wrapper(
		self,
		target_desc,
		objects,
		output_filename,
		output_dir=None,
		libraries=None,
		library_dirs=None,
		runtime_library_dirs=None,
		export_symbols=None,
		debug=0,
		extra_preargs=None,
		extra_postargs=None,
		build_temp=None,
		target_lang=None):
			# make sure extra_postargs isn't None
			if extra_postargs is None:
				extra_postargs = []
			# make sure extra_postargs is a list (so we can append)
			extra_postargs = list(extra_postargs)
			# if /MANIFEST isn't present, add it
			if not '/MANIFEST' in extra_postargs:
				extra_postargs.append('/MANIFEST')
			return func(self, target_desc, objects, output_filename,
				output_dir, libraries, library_dirs, runtime_library_dirs,
				export_symbols, debug, extra_preargs, extra_postargs,
				build_temp, target_lang)
	return wrapper

def patch_msvc9compiler_module():
	"""
	msvc9compiler won't use MSVC 10, even though it appears to be compatible.
	See
	http://nukeit.org/compile-python-2-7-packages-with-visual-studio-2010-express/
	for more information.

	Call this method (in sitecustomize for example) to trick msvc9compiler to
	work with VS2010 if VS2008 is not present.
	"""
	import distutils.msvc9compiler as mc
	if mc.find_vcvarsall(mc.VERSION):
		# system should work in default configuration
		return
	if not mc.find_vcvarsall(10.0):
		# We don't have 10.0 either, so the default behavior is fine
		return
	mc.VERSION = 10.0

	# patch MSVCCompiler.link so the /MANIFEST parameter is present
	mc.MSVCCompiler.link = _add_MANIFEST_postarg(mc.MSVCCompiler.link)