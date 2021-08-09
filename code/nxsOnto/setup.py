#!/usr/bin/env python
#
# To use this file type:
#
#        python setup.py install
#
from setuptools import setup

setup(name='NeXusOntologyGenerator',
      version='1.1',
      description='Generates an ontology from nxdl files',
      author='Steve Collins',
      url="https://github.com/nexusformat/NeXusOntology/script",
      packages=['nxsOnto'],
      license='Apache 2',
      install_requires=[
		"owlready2",
		"pygithub"
     ]

      )
