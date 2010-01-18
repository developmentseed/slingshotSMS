.. image:: web/logo.png

This is SlingshotSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple HTTP interface.

Requirements
============

* Python 2.5 or newer
* cherrypy, sqlobject, pySerial, PyRSS2Gen
* AT-compatible GSM modem
* This project uses `pygsm <http://github.com/rapidsms/pygsm/tree/master/>`_, sponsored by `UNICEF <http://www.unicef.org/>`_. A version of pygsm is included.

Modem Compatibility
-------------------

* `pygsm's wiki <http://wiki.github.com/adammck/pygsm>`_
* http://code.google.com/p/smslib/wiki/Compatibility

Manual Installation
===================

* Install required libraries
* Drop into directory
* Edit slingshotsms.txt
* run ``python slingshotsms.py``

Building
========

Building on Windows
-------------------

In cmd.exe::

  C:\Python25\python.exe setup.py py2exe

Building on Mac
---------------

In Terminal.app::

  py2applet slingshotsms.py

HTTP Methods
============

* /send
  
  Accepts POST data with keys "message" and "number" and immediately
  dispatches messages to the modem
* `/status </status>`_ (Returns a multi-line status string)
* `/list </list>`_ (returns a list of received messages as JSON)

Server Authentication
=====================

With version 2.0, SlingshotSMS introduced a system of key-based authentication 
similar to Flickr and Amazon Web Services implementations. The default setup 
is with a Drupal website using the 
`Services Module <http://drupal.org/project/services>`_ and a feature customized 
to receive messages. Configuration for this system is in the [server] section of
the configuration file ``slingshotsms.txt``. A sample configuration might look like


server section::
  
  endpoint=http://localhost/~tmcw/services-6--1/?q=/services/xmlrpc
  key=57e3ec004e7b5bfe2e5aeaea0314c3d1
  domain=localhost
  node=3

In which node= refers to the node id of the feed object.

Older POST-based message sending is no longer supported because this method is 
more secure.

Sending a Message
-----------------

Python::

   >>> params = urllib.urlencode({'message': 'Hello, world', 'number': 19737144557})
   >>> urllib.urlopen('http://127.0.0.1:8080/send', params).read()

PHP::

   if (function_exists('curl_init')) {
     $request = curl_init();
     $headers[] = 'User-Agent: YourApp (+http://yourapp.com/)';
     curl_setopt($request, CURLOPT_URL, $endpoint);
     curl_setopt($request, CURLOPT_POST, TRUE);
     curl_setopt($request, CURLOPT_POSTFIELDS, $params);
     curl_setopt($request, CURLOPT_RETURNTRANSFER, TRUE);
     curl_setopt($request, CURLOPT_HTTPHEADER, $headers);
     curl_setopt($request, CURLOPT_HEADER, TRUE);
     $data = curl_exec($request);
     $header_size = curl_getinfo($request, CURLINFO_HEADER_SIZE);
     curl_close ($request); 
     return substr($data, $header_size);
   } 

.. raw:: html

   <form action="/send" method="POST">
   <input type="text" name="number" value="1973... cell number" />
   <input type="text" name="message" value="Message" />
   <input type="submit" value="Send" />
   </form>

Configuration
=============
    
* ``mock=yes``
  
  will run sms_server without trying to connect to a server, to test 
  applications on the ability to POST and receive POST data

* ``sms_poll``
  
  is the wait time between asking the modem for new messages
  database_file can specify what file the database will be on. Since this uses 
  sqlObject, the database engine itself is flexible, but thread safety is a concern
  because the poller runs on a separate thread from the web server

Troubleshooting
===============

* running this server from the command line with ``python slingshotsms.py``
  Will give a log of modem messages.
  CMS ERROR: 515 indicates that the modem has not connected yet

Roadmap
=======

* Unit tests + better test runners
