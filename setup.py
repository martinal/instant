#!/usr/bin/env python

import sys, platform, re
from os.path import join, split, pardir
from distutils.core import setup

if sys.version_info < (2, 7):
    print("Python 2.7 or higher required, please upgrade.")
    sys.exit(1)

scripts = [join("scripts", "instant-clean"), join("scripts", "instant-showcache")]

if platform.system() == "Windows" or "bdist_wininst" in sys.argv:
    # In the Windows command prompt we can't execute Python scripts
    # without a .py extension. A solution is to create batch files
    # that runs the different scripts.
    batch_files = []
    for script in scripts:
        batch_file = script + ".bat"
        f = open(batch_file, "w")
        f.write('python "%%~dp0\%s" %%*\n' % split(script)[1])
        f.close()
        batch_files.append(batch_file)
    scripts.extend(batch_files)

version = re.findall('__version__ = "(.*)"',
                     open('instant/__init__.py', 'r').read())[0]

setup(name = "instant",
      version = version,
      description = "Instant Inlining of C/C++ in Python",
      author = "Magne Westlie, Kent-Andre Mardal, Martin Sandve Alnes and Ilmar M. Wilbers",
      author_email = "kent-and@simula.no, martinal@simula.no, ilmarw@simula.no",
      url = "http://www.fenicsproject.org",
      packages = ['instant'],
      package_dir = {'instant': 'instant'},
      package_data = {'': [join('swig', 'numpy.i')]},
      scripts = scripts,
      data_files = [(join("share", "man", "man1"),
                     [join("doc", "man", "man1", "instant-clean.1.gz"),
                      join("doc", "man", "man1", "instant-showcache.1.gz")])]
      )
