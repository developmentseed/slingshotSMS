.. image:: web/logo.png

This is SlingshotSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple HTTP interface.

REQUIREMENTS
============

Python 2.5, 2.6... possibly 3
cherrypy, sqlite3 (included in Python), sqlobject, pyserial
AT-compatible GSM modem

This project uses `pygsm <http://github.com/rapidsms/pygsm/tree/master/>`_, sponsored by `UNICEF <http://www.unicef.org/>`_.

Modem Compatibility
-------------------

* `pygsm's wiki <http://wiki.github.com/adammck/pygsm>`_
* http://code.google.com/p/smslib/wiki/Compatibility

MANUAL INSTALLATION
===================

* Install required libraries
* Drop into directory
* Edit slingshotsms.txt
* run ``python slingshotsms.py``

  The main requirement for this tool to work is to get the right serial port
  set in slingshotsms.py If you have no idea what this is, but you have a modem installed 
  and connected, you can try running slingshotsms and it can recommend possible ports.

BUILDING
========

Building on Windows
-------------------

In cmd.exe::

  C:\Python25\python.exe setup.py py2exe

Building on Mac
---------------

In Terminal.app::

  py2applet slingshotsms.py

METHODS
=======

* /send
  
  Accepts POST data with keys "message" and "number" and immediately
  dispatches messages to the modem
* `/status </status>`_ (Returns a multi-line status string)
* `/list </list>`_ (returns a list of received messages as JSON)
* /subscribe

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


Subscribing (beta)
------------------

>>> params = urllib.urlencode({'endpoint': 'http://127.0.0.1:8888', 'secret': 'crob'})
>>> urllib.urlopen('http://127.0.0.1:8080/subscribe', params).read()
'subscribed'

.. raw:: html

   <form action="/subscribe" method="POST">
   <input type="text" name="endpoint" value="http://127.0.0.1:8888/" />
   <input type="text" name="secret" value="crob" />
   <input type="submit" value="Subscribe" />
   </form>
    
After subscribing, the endpoint will have POST data sent to it whenever messages
are received

CONFIGURATION
=============
    
* ``mock=yes``
  
  will run sms_server without trying to connect to a server, to test 
  applications on the ability to POST and receive POST data

* ``sms_poll``
  
  is the wait time between asking the modem for new messages
  database_file can specify what file the database will be on. Since this uses 
  sqlObject, the database engine itself is flexible, but thread safety is a concern
  because the poller runs on a separate thread from the web server

TROUBLESHOOTING
===============

* running this server from the command line with ``python slingshotsms.py``
  Will give a log of modem messages.
  CMS ERROR: 515 indicates that the modem has not connected yet

ROADMAP
=======

* Fully implement subscriptions: subscriptions should be persisted in the 
  database so that they aren't forgotten on restart

* Detect more modems: currently you can just 'ls /dev' to find all the devices
  on your system that might be modems, and slingshotsms detects MultiModems

* Implement /list, which should use If-Modified-Since to narrow down results.
  This is very close to completion, collaboration would be welcome.
