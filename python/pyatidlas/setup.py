import os, sys
from distutils.command.build_ext import build_ext
from setuptools import Extension, setup
from distutils.sysconfig import get_python_inc
from distutils import sysconfig
from imp import find_module
from glob import glob

platform_cflags = {}
platform_ldflags = {}
platform_libs = {}
class build_ext_subclass(build_ext):
    """Shamelessly stolen from
    https://stackoverflow.com/questions/724664
    """
    def build_extensions(self):
        c = self.compiler.compiler_type
        if c in platform_cflags.keys():
            for e in self.extensions:
                e.extra_compile_args = platform_cflags[c]
        if c in platform_ldflags.keys():
            for e in self.extensions:
                e.extra_link_args = platform_ldflags[c]
        if c in platform_libs.keys():
            for e in self.extensions:
                try:
                    e.libraries += platform_libs[c]
                except:
                    e.libraries = platform_libs[c]
        build_ext.build_extensions(self)

def main():

    def recursive_glob(rootdir='.', suffix=''):
        return [os.path.join(looproot, filename)
                for looproot, _, filenames in os.walk(rootdir)
                for filename in filenames if filename.endswith(suffix)]

    def remove_prefixes(optlist, bad_prefixes):
        for bad_prefix in bad_prefixes:
            for i, flag in enumerate(optlist):
                if flag.startswith(bad_prefix):
                    optlist.pop(i)
                    break
        return optlist

    cvars = sysconfig.get_config_vars()
    cvars['OPT'] = "-DNDEBUG -O3 -std=c++11 " + str.join(' ', remove_prefixes(cvars['OPT'].split(), ['-g', '-O', '-Wstrict-prototypes', '-DNDEBUG']))
    cvars["CFLAGS"] = cvars["BASECFLAGS"] + " " + cvars["OPT"]
    cvars["LDFLAGS"] = '-Wl,--no-as-needed ' + cvars["LDFLAGS"]
    
    DEFINES = []
    INCLUDE_DIRS = ['${CMAKE_CURRENT_SOURCE_DIR}/external/boost/include',
                     os.path.join(find_module("numpy")[1], "core", "include"),
                    '${PROJECT_SOURCE_DIR}/include']
    LIBRARY_DIRS = ['${CMAKE_BINARY_DIR}/lib']

    src = [os.path.join('${CMAKE_CURRENT_SOURCE_DIR}', 'src', sf) for sf in ['_atidlas.cpp']]

    boostsrc = '${CMAKE_CURRENT_SOURCE_DIR}/external/boost/libs/'
    for s in ['numpy','python','smart_ptr','system','thread']:
        src = src + [x for x in recursive_glob('${CMAKE_CURRENT_SOURCE_DIR}/external/boost/libs/' + s + '/src/','.cpp') if 'win32' not in x and 'pthread' not in x]
    # make sure next line succeeds even on Windows
    src = [f.replace("\\", "/") for f in src]
    if sys.platform == "win32":
        src += glob(boostsrc + "/thread/src/win32/*.cpp")
        src += glob(boostsrc + "/thread/src/tss_null.cpp")
    else:
        src += glob(boostsrc + "/thread/src/pthread/*.cpp")
    src= [f for f in src  if not f.endswith("once_atomic.cpp")]


    setup(
		name="pyatidlas",
		package_dir={ '': '${CMAKE_CURRENT_SOURCE_DIR}' },
		version=[],
		description="Auto-tuned input-dependent linear algebra subroutines",
		author='Philippe Tillet',
		author_email='ptillet@g.harvard.edu',
		classifiers=[
		    'Environment :: Console',
		    'Development Status :: 1 - Experimental',
		    'Intended Audience :: Developers',
		    'Intended Audience :: Other Audience',
		    'Intended Audience :: Science/Research',
		    'License :: OSI Approved :: MIT License',
		    'Natural Language :: English',
		    'Programming Language :: C++',
		    'Programming Language :: Python',
		    'Programming Language :: Python :: 2',
		    'Programming Language :: Python :: 2.6',
		    'Programming Language :: Python :: 2.7',
		    'Programming Language :: Python :: 3',
		    'Programming Language :: Python :: 3.2',
		    'Programming Language :: Python :: 3.3',
		    'Programming Language :: Python :: 3.4',
		    'Topic :: Scientific/Engineering',
		    'Topic :: Scientific/Engineering :: Mathematics',
		    'Topic :: Scientific/Engineering :: Physics',
		    'Topic :: Scientific/Engineering :: Machine Learning',
		],

		packages=["pyatidlas"],
		ext_package="pyatidlas",
		ext_modules=[Extension(
                    '_atidlas',src,
		    extra_compile_args= ['-Wno-unused-function', '-Wno-unused-local-typedefs'],
                    extra_link_args=['-Wl,-soname=_atidlas.so'],
		    define_macros=DEFINES,
		    undef_macros=[],
		    include_dirs=INCLUDE_DIRS,
		    library_dirs=LIBRARY_DIRS,
                    libraries=['OpenCL', 'atidlas']
		)],
		cmdclass={'build_ext': build_ext_subclass}
    )

if __name__ == "__main__":
    main()
