![SlingshotSMS](web/logo.png)

This is SlingshotSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple HTTP interface.

# Experimental

Hi! This is the experimental branch of SlingshotSMS. Here's what's different and better:

* Minimal slingshotsms.py core: it's lost a hundred lines of code since Goliath and does things in a much more concise fashion
* Multiple messages with JSON: now fewer POSTs required when you have a lot of messages going from place to place
* Way better testing functionality: interactive mode lets you test web applications quickly
* More straightforward configuration
* Uses CherryPy's logging facilities, so logs are easily redirected and repurposed

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
