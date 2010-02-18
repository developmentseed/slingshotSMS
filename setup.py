#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys
from setuptools import setup

# Support for building on mac & linux, and installation
# on Unix
if sys.platform == 'darwin':
    extra_options = dict(
        setup_requires=['py2app'],
        app=['slingshotsms.py'],
        )
elif sys.platform  == 'win32':
    from distutils.core import setup
    import py2exe	
    extra_options = dict(	
        setup_requires=['py2exe'],
		console=['slingshotsms.py'],
        excludes=['javax.comm']
        )
else:
    extra_options = dict(
        # Normally unix-like platforms will use "setup.py install"
        # and install the main script as such
        scripts=['slingshotsms.py'],
        )

setup(
    name="SlingshotSMS",
    data_files=['README.md'],
    **extra_options
    )
