![SlingshotSMS](web/logo.png)

This is SlingshotSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple HTTP interface.

# Goliath

This is the Goliath branch of SlingshotSMS - it's not for public 
consumption yet, but it's very interesting if you're willing to tweak. 
Instead of just being a REST endpoint, this turns SlinghostSMS into a 
lightweight, scriptable interface for input and output of text messages. 
It has vCard import and export, Javascript hooks, a Javascript API, 
and much more.

# Requirements

* AT-compatible GSM modem

# Modem Compatibility

* [pygsm's wiki](http://wiki.github.com/adammck/pygsm)
* http://code.google.com/p/smslib/wiki/Compatibility

# Mac

* Double-click on SlingshotSMS.command

# Windows

* Double-click on slingshotsms.exe

# Running Manually

    python slingshotsms.py

## Manual Installation

* Install required libraries
* Drop into directory
* Edit slingshotsms.txt
* run `python slingshotsms.py`

## Configuration
    
* `mock=yes`
  
  will run sms_server without trying to connect to a server, to test 
  applications on the ability to POST and receive POST data

* `sms_poll`
  
  is the wait time between asking the modem for new messages
  database_file can specify what file the database will be on. Since this uses 
  sqlObject, the database engine itself is flexible, but thread safety is a concern
  because the poller runs on a separate thread from the web server
