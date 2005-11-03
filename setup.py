#!/usr/bin/env python

from distutils.core import setup

setup(name="Instant", version='0.2', 
      description="Instant Inlining of C/C++ in Python", 
      author="Magne Westlie and Kent-Andre Mardal", 
      author_email ="magnew@simula.no, kent-and@simula.no", 
      url="http://www.ifi.uio.no/~kent-and/software/Instant/doc/Instant.html", 
      package_dir={'': 'src' }, 
      py_modules=['Instant'])



