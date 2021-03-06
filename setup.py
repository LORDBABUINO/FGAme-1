#-*- coding: utf8 -*-
import os
import sys
from distutils.core import setup
VERSION = '0.3.1-alpha-1'

##########################################################################
# Configure environment
##########################################################################
setup_kwds = {}

# Test if installation can compile extensions and configure them
# Currently only cpython accepts extensions
try:
    from Cython.Distutils import build_ext
    from distutils.extension import Extension
    win_platforms = ['win32', 'cygwin']
    setup_kwds.update(
        cmdclass={
            "build_ext": build_ext},
        ext_modules=[
            Extension(
                "FGAme.mathutils.cvector",
                ["src/FGAme/mathutils/cvector.pyx"],
                libraries=(
                    [] if sys.platform in win_platforms else ['m']),
                include_dirs=['src/FGAme']),

            Extension(
                "FGAme.util.cmultidispatch",
                ["src/FGAme/util/cmultidispatch.pyx"],
                libraries=[],
                include_dirs=['src/FGAme']),
        ])
except ImportError:
    # Ignore missing cython in alternative implementation
    if not (sys.platform.startswith('java') or sys.platform.startswith(
            'cli') or 'PyPy' in sys.version):
        raise

##########################################################################
# Main configuration script
##########################################################################
setup(name='FGAme',
      version=VERSION,
      description='A game engine for 2D physics',
      author='Fábio Macêdo Mendes',
      author_email='fabiomacedomendes@gmail.com',
      url='https://github.com/fabiommendes/FGAme',
      long_description=(
          r'''A game engine for 2D physics. FGAme was developed for a course on computer
games physics. Simplicity and ease to use were valued more than raw performance
and fancy graphics.

Main features:
  * AABB's, Circle and Convex Polygons collisions.
  * Backend agnostic (Pygame and sdl2 are supported, for now).
'''),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License (GPL)',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries',
      ],
      package_dir={'': 'src'},
      packages=['FGAme', 'FGAme.app', 'FGAme.backends', 'FGAme.core',
                'FGAme.demos', 'FGAme.demos.simulations',
                'FGAme.draw', 'FGAme.extra', 'FGAme.mathutils',
                'FGAme.physics', 'FGAme.objects', 'FGAme.util'],
      license='GPL',
      requires=['pygame'],
      **setup_kwds
      )
