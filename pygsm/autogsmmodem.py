#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from __future__ import with_statement

# debian/ubuntu: apt-get install python-tz

import re
import datetime
import time
import errors
import threading
import gsmcodecs
from gsmmodem import GsmModem
from devicewrapper import DeviceWrapper
from pdusmshandler import PduSmsHandler
from textsmshandler import TextSmsHandler

class GsmModemNotFound(Exception):
    pass

class AutoGsmModem(GsmModem):
    """AutoGsmModem is a wrapper around GsmModem which attempts to automatically
    choose a port and baudrate for the first GSM modem connected to a system. If it
    is not successful (in the case that there is no modem), it throws a NoModemConnected
    exception."""


    # override these after init, and
    # before boot. they're not sanity
    # checked, so go crazy.
    cmd_delay = 0.1
    retry_delay = 2
    max_retries = 10
    modem_lock = threading.RLock()
    
    
    def __init__(self, *args, **kwargs):
        import prober
        """See the documentation for GsmModem.__init__ for details; this is a 
        wrapper function that attempts to find attached modems and then reconnects
        to an initialized modem."""

        if kwargs.get('verbose', False):
            proberargs = {'verbose': True}
        else:
            proberargs = {}

        try:
            del kwargs['verbose']
        except:
            pass

        ports = prober.probe(**proberargs)
        if len(ports) > 0:
            kwargs['port'] = ports[0][0]
            kwargs['baudrate'] = ports[0][1]
            super(AutoGsmModem, self).__init__(*args, **kwargs)
        else:
            raise GsmModemNotFound()

    
if __name__ == "__main__":

    import sys
    # all subsequent options are parsed as key=value
    # pairs, to be passed on to GsmModem.__init__ as
    # kwargs, to configure the serial connection
    conf = dict([
        arg.split("=", 1)
        for arg in sys.argv[2:]
        if arg.find("=") > -1
    ])

    # dump the connection settings
    # print "pyGSM Demo App"
    # print "  Port: %s" % (port)
    # print "  Config: %r" % (conf)
    # print

    # connect to the modem (this might hang
    # if the connection settings are wrong)
    print "Connecting to GSM Modem..."
    modem = AutoGsmModem(verbose=True)
    print "Waiting for incoming messages..."

    # check for new messages every two
    # seconds for the rest of forever
    while True:
        msg = modem.next_message()

        # we got a message! respond with
        # something useless, as an example
        if msg is not None:
            print "Got Message: %r" % msg
            msg.respond("Received: %d characters '%s'" %
                (len(msg.text),msg.text))

        # no messages? wait a couple
        # of seconds and try again
        else: 
            time.sleep(2)

    # the serial port must be provided
    # we're not auto-detecting, yet
    else:
        print "Usage: python -m pygsm.gsmmodem PORT [OPTIONS]"
