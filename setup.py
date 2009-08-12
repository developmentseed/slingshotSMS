from distutils.core import setup
import py2exe

setup(console=['rsms.py'], data_files=['README', 'rsms.cfg', 'server.cfg'])