#!/usr/bin/env python

import sys
import os
from distutils.core import setup

import offen

setup (name = 'open-fenfen',
       #version = ftl.__version__,
       description = 'Framework for interactive fiction and text adventures.',
       #long_description = ftl.__doc__,
       #author = ftl.__author__,
       #author_email = ftl.__email__,
       url = 'github.com/miezebieze/offen',
       packages = ['offen'],
       license = 'MIT',
       platforms = 'any',
       classifiers = ['Development Status :: 4 - Beta',
         'License :: OSI Approved :: MIT License',
       ],
      )



