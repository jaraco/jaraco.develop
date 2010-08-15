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