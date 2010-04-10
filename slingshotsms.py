#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import ConfigParser, time, urllib, sys, os, re
from xml.dom import minidom
from rfc822 import parsedate as parsehttpdate

import cherrypy, pygsm, sqlite3, serial, markdown2
from pygsm.autogsmmodem import GsmModemNotFound
from sqlobject import SQLObject, IntCol, StringCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

import keyauth

'''
  SlingshotSMS
  version 2.0 Goliath
  Tom MacWright
  http://www.developmentseed.org/
'''

# TODO: built complete mock modem for better testing

CONFIG = "slingshotsms.txt"
SERVER_CONFIG = "server.txt"

class MessageData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    # in sqlite, these columns will be default null
    sent = IntCol(default=None)
    received = IntCol(default=None)
    sender = StringCol()
    text = StringCol()

class OutMessageData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    number = StringCol()
    text = StringCol()

class SMSServer:
    def __init__(self, config=None):
        '''
          Initialize GsmModem (calling the constructor calls .boot() on
          the object), start message_watcher thread and initialize variables
        '''
        try:
            self.parse_config()
        except Exception, e:
            print e
            raw_input("Press any key to continue")
        if not os.path.exists('slingshotsms.db'):
            self.reset()
        if self.mock_modem == False:
            try:
                self.modem = pygsm.GsmModem(port=self.port, baudrate=self.baudrate)
            except Exception, e:
                try:
                    self.modem = pygsm.AutoGsmModem()
                except GsmModemNotFound, e:
                    raw_input("No modems were autodetected - you will need to edit \
                            slingshotsms.txt to point Slingshot at your working GSM modem.")
                    sys.exit()
        self.message_watcher = cherrypy.process.plugins.Monitor(cherrypy.engine, \
            self.retrieve_sms, self.sms_poll)
        self.message_watcher.subscribe()
        self.message_watcher.start()
        self.messages_in_queue = []
        
    def parse_config(self):
        """no params: this assists in parsing the config file with defaults"""
        import ConfigParser
        defaults = { 'port': '/dev/tty.MTCBA-U-G1a20', 'baudrate': '115200', \
            'sms_poll' : 2, 'database_file' : 'slingshotsms.db', \
            'endpoint' : 'http://localhost/sms', 'mock' : False }

        self.config = ConfigParser.SafeConfigParser(defaults)

        # For mac distributions, look up the .app directory structure
        # to find slingshotsms.txt alongside the double-clickable
        if (sys.platform != "win32") and hasattr(sys, 'frozen'):
            config_path = '../../../'+CONFIG
        else:
            config_path = CONFIG

        # Choose modem sections based on OS in order to have a singular
        # config file
        # TODO: just have the sections named the same as the platforms 
        if sys.platform == 'win32':
            self.modem_section = 'winmodem'
        elif sys.platform == 'darwin':
            self.modem_section = 'macmodem'
        else:
            self.modem_section = 'modem'

        self.config.read([config_path, '../'+config_path])

        self.port =       self.config.get       (self.modem_section, 'port')
        self.baudrate =   self.config.getint    (self.modem_section, 'baudrate')
        self.sms_poll =   self.config.getint    (self.modem_section, 'sms_poll')
        self.mock_modem = self.config.getboolean(self.modem_section, 'mock')

        self.private_key = self.config.get      ('hmac', 'private_key')
        self.public_key = self.config.get       ('hmac', 'public_key')
        self.endpoint = self.config.get         ('hmac', 'endpoint')

    def get_real_values(self, message):
        """ attempts to get values out of an input message which could have a different
        form, depending on modem choice"""
        fields = {}
        if message.sent is not None:
            fields['sent'] = message.sent
        if message.received is not None:
            fields['received'] = message.received
        fields['text'] = message.text
        fields['sender'] = message.sender
        return fields

    def post_results(self):
        '''private method which POSTS messages stored in the database 
        to endpoints defined by self.endpoint'''

        # Send messages
        out_messages = OutMessageData.select();
        for out_message in out_messages:
            self.modem.send_sms(out_message.number, out_message.text)
            out_message.destroySelf()

        # Post retrieved messages if endpoint is set
        if self.endpoint:
            messages = MessageData.select();
            for message in messages:
                params = self.get_real_values(message)
                print "Received ", params
                print self.endpoint
                try:
                    response = keyauth.keyauth_post(self.endpoint, self.public_key, self.private_key, \
                        urllib.urlencode({'timestamp': params['received'], 'title': params['sender'], \
                        'description': params['text'], 'received': params['received'], \
                        }))
                    message.destroySelf()
                except Exception, e:
                    print e

    def index(self):
        '''exposed self: input home'''
        # TODO: rewrite, place index.html elsewhere
        homepage = open('index.html')
        return homepage.read()
    index.exposed = True

    def docs(self):
        '''exposed method: spash page for SlingshotSMS information & status'''
        
        try:
            # Compile the ReST file into an HTML fragment
            documentation = markdown2.markdown_path('README.md')
            return """
            <html>
                <head>
                    <title>SlingshotSMS</title>
                    <link rel="stylesheet" type="text/css" href="web/style.css" />
                </head>
                <body>
                <div class="doc">%s</div>
                </body>
            </html>""" % (documentation)
        except Exception, e:
            print e
            return "<html><body><h1>SlingshotSMS</h1>README File not found</body></html>"
    docs.exposed = True

    def reset(self):
        """ Drop and recreate all tables according to schema. """
        MessageData.dropTable(True)
        MessageData.createTable()
        OutMessageData.dropTable(True)
        OutMessageData.createTable()
        return "Reset complete"
    reset.exposed = True

    def status(self):
        """ exposed method: returns JSON object of status information """
        status = {}
        if self.mock_modem:
            status['port'] = 'mocking'
        else:
            status['port'] = self.modem.device_kwargs['port']
            status['baudrate'] = self.modem.device_kwargs['baudrate']
        status['endpoint'] = self.endpoint
        return repr(status)
    status.exposed = True

    def send(self, number=None, message=None):
        '''
          Return status code "ok"
          Public API method which sends an SMS message when given a number
          and message as POST variables
        '''
        if number and message:
            print "Sending %s a message consisting of %s" % (number, message)
            if self.mock_modem:
                return "ok"
            OutMessageData(number=number, text=message)
            return "ok"
    send.exposed = True

    def retrieve_sms(self):
        if self.mock_modem:
            print "Mocking modem, no SMS will be received."
            self.post_results()
            return
        try:
            msg = self.modem.next_message()
            if msg is not None:
                print "Message retrieved"
                data = {}
                # some modems do not provide these attributes
                try:
                    # print int(time.mktime(msg.sent.timetuple()))
                    data['sent'] = int(time.mktime(time.localtime(int(msg.sent.strftime('%s')))))
                except Exception, e:
                    print e
                    pass
                # we can count on these attributes from all modems
                data['sender'] = msg.sender
                data['text'] = msg.text
                MessageData(**data)
        except Exception, e:
            print "Exception caught: ", e
        self.post_results()

    def list(self, limit = 100):
        """ exposed method that generates a list of messages in RSS 2.0 """
        import PyRSS2Gen, datetime
        from socket import gethostname, gethostbyname
        date = parsehttpdate(cherrypy.request.headers.elements('If-Modified-Since'))
        if date:
            messages = MessageData.select().filter(MessageData.q.received>date).limit(limit);
        else:
            messages = MessageData.select().limit(limit)
        rss = PyRSS2Gen.RSS2(
                title = "SlingshotSMS on %s" % gethostname(),
                link = gethostbyname(gethostname()),
                description = "Incoming SMS messages",
                lastBuildDate = datetime.datetime.now(),
                items = [PyRSS2Gen.RSSItem(
                    description = message.text,
                    author = message.sender,
                    pubDate = datetime.datetime.fromtimestamp(message.sent)) for message in messages])
        return rss.to_xml()
    list.exposed = True

if __name__=="__main__":
    """ run as command line """
    # hasattr(sys, 'frozen') confirms that this is running as a py2app-compiled Application
    if sys.platform == 'darwin' and hasattr(sys, 'frozen'):
        if os.path.exists("../../../"+SERVER_CONFIG):
            cherrypy.config.update("../../../"+SERVER_CONFIG)
        else:
            cherrypy.config.update("../../../../"+SERVER_CONFIG)
    else:
        if os.path.exists(SERVER_CONFIG):
            cherrypy.config.update(SERVER_CONFIG)
        else:
            cherrypy.config.update("../"+SERVER_CONFIG)
    # see http://www.py2exe.org/index.cgi/WhereAmI
	# use of __file__ is dangerous when packaging with py2exe and console
    if hasattr(sys,"frozen"):
        current_dir=os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/web': {'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'web')}}
    cherrypy.quickstart(SMSServer(), '/', config=conf)
