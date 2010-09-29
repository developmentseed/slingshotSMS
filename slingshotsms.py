#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import ConfigParser, time, urllib, sys, os, json, logging
from rfc822 import parsedate as parsehttpdate

import cherrypy, pygsm, sqlite3, serial
from pygsm.autogsmmodem import GsmModemNotFound
from sqlobject import SQLObject, IntCol, StringCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

# for RSS generation, possibly remove soon
import PyRSS2Gen, datetime
from socket import gethostname, gethostbyname

# for keyauth
import hmac, random, hashlib, urllib2

'''
  SlingshotSMS
  version 2.1 Pico
  Tom MacWright
  http://www.developmentseed.org/
'''

# TODO: use optionparser for arguments
# TODO: split UI / metadata parts into separate file
# TODO: Analyze performance
# TODO: Give UTF-8 a long, hard look
# TODO: Build UI for running this - don't settle with .command file
# TODO: Write demos for ruby/sinatra, django, drupal, node, html/js
# TODO: clarify, fix configuration
# TODO: have json-returning pages return correct Content-Type

CONFIG = "slingshotsms.txt"
SERVER_CONFIG = "server.txt"

class MessageData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    sent = IntCol(default=None)
    received = IntCol(default=None)
    sender = StringCol()
    text = StringCol()

class OutMessageData(SQLObject):
    ''' messages going out - these are essentially a queue '''
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
        try:
            if self.modem_config['mock'] != 'yes':
                self.modem = pygsm.GsmModem(port=self.modem_config['port'], 
                        baudrate=self.modem_config['baudrate'])
        except Exception, e:
            try:
                self.modem = pygsm.AutoGsmModem()
            except GsmModemNotFound, e:
                raw_input("No modems were autodetected - you will need to edit \
                        slingshotsms.txt to point Slingshot at your working GSM modem.")
                sys.exit()
        self.message_watcher = cherrypy.process.plugins.Monitor(cherrypy.engine, \
            self.retrieve_sms, int(self.modem_config['poll_interval']))
        self.message_watcher.subscribe()
        self.message_watcher.start()

    def jsonp(self, json, jsoncallback):
        """ serve a page with an optional jsonp callback """
        if jsoncallback:
            json = "%s(%s)" % (jsoncallback, json)
            #self.set_header('Content-Type', 'text/javascript') TODO: rewrite for cherrypy or port
        else:
            json = "%s" % json
            #self.set_header('Content-Type', 'application/json')
        return json

    def keyauth_random(self):
        " Provide a random, time dependent string "
        hash = hashlib.md5()
        hash.update(str(random.random()))
        return hash.hexdigest()

    def keyauth_sign(self, message):
        nonce = self.keyauth_random()[0]
        timestamp = str(int(time.time()))
        hash = hmac.new(self.endpoint['private_key'], 
                message + nonce + timestamp, hashlib.sha1)
        return {
                'nonce': nonce,
                'timestamp': timestamp,
                'public_key': self.endpoint['public_key'],
                'message': message,
                'hash': hash.hexdigest()}
        
    def keyauth_post(self, message):
        message_encoded = self.keyauth_sign(message)
        request = urllib2.urlopen(urllib2.Request(
            url=self.endpoint['url'], 
            data=urllib.urlencode(message_encoded)))
        return request.read()
        
    def parse_config(self):
        """no params: this assists in parsing the config file with defaults"""

        # For mac distributions, look up the .app directory structure
        # to find slingshotsms.txt alongside the double-clickable
        if (sys.platform != "win32") and hasattr(sys, 'frozen'):
            config_path = '../../../'+CONFIG
        else:
            config_path = CONFIG

        self.config = ConfigParser.SafeConfigParser({
            'port': '/dev/tty.MTCBA-U-G1a20',
            'baudrate': '115200',
            'sms_poll': 2,
            'mock_modem': False,
            'database_file': 'slingshotsms.db',
            'endpoint': 'http://localhost/sms'})

        self.config.read([config_path, '../'+config_path])
        self.modem_config = dict(self.config.items(sys.platform, True))
        self.endpoint = dict(self.config.items('endpoint', True))

    def post_results(self):
        '''private method which POSTS messages stored in the database 
        to endpoints defined by self.endpoint'''
        logging.info('posting results')
        out_messages = OutMessageData.select();
        for out_message in out_messages:
            logging.info('sending sms to %s' % out_message.number)
            self.modem.send_sms(out_message.number, out_message.text)
            out_message.destroySelf()

        if self.endpoint['url']:
            messages = MessageData.select();
            try:
                self.keyauth_post(self.messages_json(messages))
            except urllib2.HTTPError, e:
                cherrypy.log('Request to %s failed with status %s' % 
                        (self.endpoint['url'], e.code), severity=logging.ERROR)
            for message in messages:
                message.destroySelf()

    def messages_json(self, messages):
        return json.dumps([
            {'received': m.received, 'sender': m.sender, 'text': m.text }
            for m in messages])

    def retrieve_sms(self):
        ''' worker method, runs in a separate thread watching for messages '''
        if self.modem_config['mock'] != 'yes':
            msg = self.modem.next_message()
            if msg is not None:
                logging.info("Message retrieved")
                MessageData(
                        sent=int(time.mktime(time.localtime(int(msg.sent.strftime('%s'))))),
                        sender=msg.sender,
                        text=msg.text)
        self.post_results()

    def reset(self):
        """ Drop and recreate all tables according to schema. """
        # TODO: authenticate with HMAC
        MessageData.dropTable(True)
        MessageData.createTable()
        OutMessageData.dropTable(True)
        OutMessageData.createTable()
        return json.dumps({'status': 'ok', 'msg': 'SlingshotSMS reset'})
    reset.exposed = True

    def status(self):
        """ exposed method: returns JSON object of status information """
        if self.modem_config['mock'] != 'yes':
            return json.dumps({
                'port': self.modem.device_kwargs['port'],
                'baudrate': self.modem.device_kwargs['baudrate'],
                'endpoint': self.endpoint['url']})
        else:
            return json.dumps({
                'port': 'Mocking modem',
                'endpoint': self.endpoint['url']})
    status.exposed = True

    def send(self, data):
        '''
          Return status code "ok"
          Public API method which sends an SMS message when given messages as JSON
          '''
        messagedata = json.loads(data)
        for m in messagedata:
            logging.info("Sending %s a message consisting of %s" % (m.number, m.text))
            OutMessageData(number=m.number, text=m.text)
        return json.dumps({'status': 'ok', 'msg': '%d messages sent' % len(messagedata)})
    send.exposed = True

    def list(self, limit=100, format='rss'):
        """ exposed method that generates a list of messages in RSS 2.0 """
        date = parsehttpdate(cherrypy.request.headers.elements('If-Modified-Since'))
        limit = int(limit)
        if date:
            messages = MessageData.select().filter(MessageData.q.received>date).limit(limit);
        else:
            messages = MessageData.select().limit(limit)
        if format == 'rss':
            rss = PyRSS2Gen.RSS2(
                    title = "SlingshotSMS on %s" % gethostname(),
                    link = gethostbyname(gethostname()),
                    description = "Incoming SMS messages",
                    lastBuildDate = datetime.datetime.now(),
                    items = [PyRSS2Gen.RSSItem(
                        description = message.text,
                        author = message.sender,
                        pubDate = datetime.datetime.fromtimestamp(message.sent)) 
                        for message in messages])
            return rss.to_xml()
        if format == 'json':
            return json.dumps([{
                'text': message.text,
                'sender': message.sender,
                'sent': datetime.datetime.fromtimestamp(message.sent).strftime('%Y-%m-%dT%H:%M:%S')} 
                for message in messages])
    list.exposed = True

    def index(self):
        '''exposed self: input home'''
        # TODO: rewrite, place index.html elsewhere
        homepage = open('index.html')
        return homepage.read()
    index.exposed = True

def config_path():
    if sys.platform == 'darwin' and hasattr(sys, 'frozen'):
        return "../../../" + SERVER_CONFIG
    else:
        return SERVER_CONFIG

def start():
    """ run as command line """
    # hasattr(sys, 'frozen') confirms that this is running as a py2app-compiled Application
    cherrypy.config.update(config_path())
    # see http://www.py2exe.org/index.cgi/WhereAmI
	# use of __file__ is dangerous when packaging with py2exe and console
    if hasattr(sys, "frozen"):
        current_dir=os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
    conf = {'/web': {'tools.staticdir.on': True,
        'tools.staticdir.dir': os.path.join(current_dir, 'web')}}
    return cherrypy.quickstart(SMSServer(), '/', config=conf)

if __name__ == "__main__":
    start()
