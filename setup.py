try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import re
import os

packageName = 'crosswordpy'
packageDir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          packageName)

## Version Stuff
versionFile = os.path.join(packageDir, 'version.py')

with open(versionFile, 'r') as f:
      s = f.read()

# Look up the string value assigned to __version__ in version.py using regexp
versionRegExp = re.compile("__version__ = \"(.*?)\"")
# Assign to __version__
__version__ =  versionRegExp.findall(s)[0]

setup(# package information
      name=packageName,
      version=__version__,
      description='Tools for the Guardian Crossword',
      long_description=''' A module which, on import, yields functions for automatically printing the Guardian crossword.
      Based on a Python script written by Jonny Nichols (University of Leicester) in the distant past.''',
                packages=[packageName,],
      package_dir={packageName:'crosswordpy'},
      install_requires=[]
      )
