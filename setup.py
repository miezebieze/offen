#!/usr/bin/env python

import sys
import os
from distutils.core import setup

import offen

setup (name = 'open-fenfen',
       #version = offen.__version__,
       description = 'Framework for interactive fiction and text adventures.',
       #long_description = offen.__doc__,
       #author = offen.__author__,
       #author_email = offen.__email__,
       url = 'github.com/miezebieze/offen',
       packages = ['offen'],
       license = 'MIT',
       platforms = 'any',
       classifiers = ['Development Status :: 4 - Beta',
         'License :: OSI Approved :: MIT License',
       ],
      )



