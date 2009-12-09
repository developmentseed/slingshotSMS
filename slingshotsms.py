#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import ConfigParser, time, urllib, sys, os, re
from xml.dom import minidom
from rfc822 import parsedate as parsehttpdate

import cherrypy, pygsm, sqlite3
from pygsm.autogsmmodem import GsmModemNotFound
from sqlobject import SQLObject, IntCol, StringCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

'''
  SlingshotSMS
  version 1.5
  Tom MacWright
  http://www.developmentseed.org/
'''

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
        '''
          Private method parse_config
          no params
        '''
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
        self.database_file = self.config.get('server', 'database_file')
        self.endpoint = self.config.get('server', 'endpoint')

    def get_real_values(self, message):
        fields = {}
        if message.sent is not None:
            fields['sent'] = message.sent
        if message.received is not None:
            fields['received'] = message.received
        fields['text'] = message.text
        fields['sender'] = message.sender
        return fields

    def post_results(self):
        '''private method which POSTS messages stored in the database to endpoints defined by self.endpoint'''
        messages = MessageData.select();
        for message in messages:
            params = urllib.urlencode(self.get_real_values(message))
            print "Received ", params
            print self.endpoint
            if not self.endpoint:
                # If the main endpoint isn't set, don't
                # try posting to anything
                return
            try:
                response = urllib.urlopen(self.endpoint, params)
                # only called when urlopen succeeds here
                message.destroySelf()
                print response.read()
            except Exception, e:
                print e
        # Send messages
        out_messages = OutMessageData.select();
        for out_message in out_messages:
            self.modem.send_sms(out_message.number, out_message.text)
            out_message.destroySelf()

    def index(self):
        '''exposed method: spash page for SlingshotSMS information & status'''
        from docutils.core import publish_parts
        
        try:
            # Compile the ReST file into an HTML fragment
            documentation = publish_parts(source=open('README.rst').read(), writer_name='html')
            return """
            <html>
                <head>
                    <title>SlingshotSMS</title>
                    <link rel="stylesheet" type="text/css" href="web/style.css" />
                </head>
                <body>
                <div class="doc">%s</div>
                </body>
            </html>""" % (documentation['fragment'])
        except Exception, e:
            print e
            return "<html><body><h1>SMS REST</h1>README File not found</body></html>"
    index.exposed = True

    def reset(self):
        MessageData.dropTable(True)
        MessageData.createTable()
        OutMessageData.dropTable(True)
        OutMessageData.createTable()
        return "Reset complete"
    reset.exposed = True

    def status(self):
        """ exposed method: returns JSON object of status information """
        import simplejson
        status = {}

        if self.mock_modem:
            status['port'] = 'mocking'
        else:
            status['port'] = self.modem.device_kwargs['port']
            status['baudrate'] = self.modem.device_kwargs['baudrate']

        status['endpoint'] = self.endpoint

        return simplejson.dumps(status)

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

    def list(self):
        import simplejson
        date = parsehttpdate(cherrypy.request.headers.elements('If-Modified-Since'))
        data = {}
        messages = MessageData.select().filter(MessageData.q.received>date);
        data['messages'] = []
        data['message_count'] = messages.count()
        for message in messages:
            m = { 'text': message.text, 'sender' : message.sender, \
              'sent' : message.sent, 'received' : message.received}
            data['messages'].append(m)
        return simplejson.dumps(data)
    list.exposed = True

if __name__=="__main__":
    if sys.platform == 'darwin' and hasattr(sys, 'frozen'):
        # only runs on .app
        if os.path.exists("../../../"+SERVER_CONFIG):
            cherrypy.config.update("../../../"+SERVER_CONFIG)
        else:
            cherrypy.config.update("../../../../"+SERVER_CONFIG)
    else:
        if os.path.exists(SERVER_CONFIG):
            cherrypy.config.update(SERVER_CONFIG)
        else:
            cherrypy.config.update("../"+SERVER_CONFIG)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/web': {'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'web')}}
    cherrypy.quickstart(SMSServer(), '/', config=conf)
