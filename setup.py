# -*- coding: utf-8 -*-

"""
A setuptools based setup module for opengrid.

Adapted from 
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
#with open(path.join(here, 'README.md'), encoding='utf-8') as f:
#    long_description = f.read()

import subprocess
if subprocess.call(["pip", "install","-r", path.join(here, "requirements.txt"), "-v", "--no-cache"]):
    raise Exception("Could not install dependencies")

setup(
    name='opengrid',
    version="0.4.9",
    description='Open-source algorithms for data-driven building analysis and control',
    #long_description=long_description,
    url='https://github.com/opengridcc/opengrid',
    author='Roel De Coninck and many others',
    author_email='roeldeconinck@gmail.com',
    license='Apache 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: Apache Software License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],

    keywords='algorithms buildings monitoring analysis control',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #py_modules=["tmpo.py"],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    # Note: for creating the source distribution, they had to be included in the
    # MANIFEST.in as well. 
    package_data={
        'opengrid': ['LICENSE', 'README.md', 'requirements.txt', 'opengrid/library/houseprint/tests/test_saved_hp.hp',
                     'opengrid/library/tests/*', 'opengrid/library/tests/data/*', 'opengrid/library/tests/data/cache_day/*',
                     'notebooks/*'],
    },
)
