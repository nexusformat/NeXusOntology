#!/usr/bin/env python
#
# To use this file type:
#
#        python setup.py install
#
from setuptools import setup

from setuptools import setup

__entry_points__ = {
    "console_scripts": [
        "nexusontology = nxsOnto.generator:main",
    ],
    # 'gui_scripts': [],
}

setup(name='NeXusOntologyGenerator',
      version='1.1',
      description='Generates an ontology from nxdl files',
      author='Steve Collins',
      url="https://github.com/nexusformat/NeXusOntology/code/nxsOnto",
      packages=['nxsOnto'],
      license='Apache 2',
      entry_points=__entry_points__,
      )
