import sys

if sys.platform == 'win32':
    from distutils.core import setup
    import py2exe
    setup(console=['rsms.py'], data_files=['README', 'rsms.cfg'])
if sys.platform == 'darwin':
    import py2app
    from setuptools import setup
    setup(app=['rsms.py'], data_files=['README', 'rsms.cfg'])
