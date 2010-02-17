![SlingshotSMS](web/logo.png)

This is SlingshotSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple HTTP interface.

# Requirements


* Python 2.5 or newer
* cherrypy, sqlobject, pySerial, PyRSS2Gen
* AT-compatible GSM modem
* This project uses [pygsm](http://github.com/rapidsms/pygsm/tree/master/), sponsored by [UNICEF](http://www.unicef.org/). A version of pygsm is included.

# Modem Compatibility

* [pygsm's wiki](http://wiki.github.com/adammck/pygsm)
* http://code.google.com/p/smslib/wiki/Compatibility

# Mac

There are two main options:

* To open SlingshotSMS in a terminal, double-click 
  on SlingshotSMS.command
* To open SlingshotSMS as an application, double-click on 
  the SlingshotSMS application icon. If this doesn't boot up,
  open Console (under System Utilities) to see SlingshotSMS debugging
  messages

# Windows

* Double-click on slingshotsms.exe

# Running Manually

    python slingshotsms.py

## Manual Installation

* Install required libraries
* Drop into directory
* Edit slingshotsms.txt
* run `python slingshotsms.py`

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

## HTTP Methods

* /send
  
  Accepts POST data with keys "message" and "number" and immediately
  dispatches messages to the modem
* [/status](/status) (Returns a multi-line status string)
* [/list](/list) (returns a list of received messages as JSON)

## Server Authentication

TODO

## Sending a Message

Python

    >>> params = urllib.urlencode({'message': 'Hello, world', 'number': 19737144557})
    >>> urllib.urlopen('http://127.0.0.1:8080/send', params).read()

PHP

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

<form action="/send" method="POST">
<input type="text" name="number" value="1973... cell number" />
<input type="text" name="message" value="Message" />
<input type="submit" value="Send" />
</form>

## Configuration
    
* `mock=yes`
  
  will run sms_server without trying to connect to a server, to test 
  applications on the ability to POST and receive POST data

* `sms_poll`
  
  is the wait time between asking the modem for new messages
  database_file can specify what file the database will be on. Since this uses 
  sqlObject, the database engine itself is flexible, but thread safety is a concern
  because the poller runs on a separate thread from the web server

# Troubleshooting

* running this server from the command line with `python slingshotsms.py`
  Will give a log of modem messages.
  CMS ERROR: 515 indicates that the modem has not connected yet

## Roadmap

* Unit tests + better test runners
