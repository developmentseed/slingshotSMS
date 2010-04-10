# Building

## Building on Windows

In cmd.exe

    C:\Python25\python.exe setup.py py2exe

## Building on Mac

In terminal.app

    make buildmac

This Makefile corrects several flaws in the Python packaging workflow:

* py2app excludes are ineffective with Frameworks
* The docutils recipe for py2app is not actually working 
  for serious use, because docutils was not written for 
  any degree of portability
* iconfile is only a command-line option, rather than an 
  option that can be set in setup.py
