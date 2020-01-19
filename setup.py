#!/usr/bin/env python
import setuptools

with open ('README.md','r') as fh:
    long_description = fh.read ()

setuptools.setup (
    name = 'open-fenfen',
    version = '0.0.1',
    author = 'Asterisk',
    author_email = '',
    description = 'Framework for interactive fiction and text adventures.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/miezebieze/offen',
    packages = setuptools.find_packages (),
    install_requires = ['pygame'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operation System :: OS Independent',
        ],
    #python_requires = '', # TODO
    )



