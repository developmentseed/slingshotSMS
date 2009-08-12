import cherrypy, pygsm, sqlite3, ConfigParser, time, urllib, sys, os, re
from sqlobject import SQLObject, IntCol, StringCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection
from xml.dom import minidom

'''
  agilesms
  version 0.2
  Tom MacWright
  http://www.developmentseed.org/
'''


DOCUMENTATION = '''

This is agileSMS, a minimal SMS server which connects GSM modems to 
websites and applications via a simple interface. It provides only 
a few endpoints for this purpose:

  REQUIREMENTS:

  Python 2.5, 2.6... possibly 3
  cherrypy, sqlite3, sqlobject, pyserial
  AT-compatible GSM modem

  This project uses pygsm
  http://github.com/rapidsms/pygsm/tree/master

  compatibility at:
  http://wiki.github.com/adammck/pygsm

  INSTALLATION:

  * Install required libraries
  * Drop into directory
  * Edit sms_server.cfg
  * run
    python sms_server.py

  METHODS:

  * /send
    
    Accepts POST data with keys "message" and "number" and immediately
    dispatches messages to the modem

    DEMO

>>> params = urllib.urlencode({'message': 'Hello, world', 'number': 19737144557})
>>> urllib.urlopen('http://127.0.0.1:8080/send', params).read()

  * /status

    Returns a multi-line status string

  * /list (currently turned off)

    Returns a list of received messages as JSON

  * edit sms_rest.cfg to set endpoint POST data should be pointed at
  
  * /subscribe

    Experimental subscription facility

    DEMO

>>> params = urllib.urlencode({'endpoint': 'http://127.0.0.1:8888', 'secret': 'crob'})
>>> urllib.urlopen('http://127.0.0.1:8080/subscribe', params).read()
'subscribed'
    
    After subscribing, the endpoint will have POST data sent to it whenever messages
    are received

  CONFIGURATION:
    
    mock=yes will run sms_server without trying to connect to a server, to test 
    applications on the ability to POST and receive POST data

    sms_poll is the wait time between asking the modem for new messages

    database_file can specify what file the database will be on. Since this uses 
    sqlObject, the database engine itself is flexible, but thread safety is a concern
    because the poller runs on a separate thread from the web server

  TROUBLESHOOTING:

  * running this server from the command line with `python sms_rest.py`
    Will give a log of modem messages.
    CMS ERROR: 515 indicates that the modem has not connected yet

  * Set the serial port of the modem in sms_rest.cfg. It will be autodetected
    in the future, but we want to maintain compatibility across modems, so it
    currently is not.
'''

class MessageData(SQLObject):
    _connection = SQLiteConnection('agilesms.db')
    sent = IntCol()
    received = IntCol()
    sender = StringCol()
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
        if not os.path.exists('agilesms.db'):
            self.reset()
        if self.mock_modem == False:
            try:
                self.modem = pygsm.GsmModem(port=self.port, baudrate=self.baudrate)
            except Exception, e:
                self.recommend_port()
                raw_input("Press any key to continue")
                sys.exit()
        self.message_watcher = cherrypy.process.plugins.Monitor(cherrypy.engine, \
            self.retrieve_sms, self.sms_poll)
        self.message_watcher.subscribe()
        self.message_watcher.start()
        self.messages_in_queue = []
        self.subscriptions = []

    def nix_mtcba(self, port):
        nix_mtcba_re = re.compile('tty.MTCBA')
        if nix_mtcba_re.match(port):
            return True

    def recommend_port(self):
        print '''
A port could not be opened to connect to your modem. If you have not 
installed the drivers that came with the modem, please do so, and then edit 
agilesms.cfg with the modem's port and baudrate.
Ports will be recommended below if found:\n'''
        if sys.platform == 'darwin':
            for p in filter(self.nix_mtcba, os.listdir('/dev')):
                print "MultiModem: /dev/%s" % p
        elif sys.platform == 'win32':
            import scanwin, serial
            for order, port, desc, hwid in sorted(scanwin.comports()):
                print "%-10s: %s (%s) ->" % (port, desc, hwid)

        
    '''
      Private method parse_config
      no params
    '''
    def parse_config(self):
        defaults = { 'port': '/dev/tty.MTCBA-U-G1a20', 'baudrate': '115200', \
            'sms_poll' : 2, 'database_file' : 'agilesms.db', \
            'endpoint' : 'http://localhost/sms', 'mock' : False, 'max_subscriptions' : 10 }
        self.config = ConfigParser.SafeConfigParser(defaults)
        # For mac distributions, look up the .app directory structure
        # to find agilesms.cfg alongside the double-clickable
        if (sys.platform != "win32") and hasattr(sys, 'frozen'):
            config_path = '../../../agilesms.cfg'
        else:
            config_path = 'agilesms.cfg'
        self.config.read(config_path)
        self.port = self.config.get('modem', 'port')
        self.baudrate = self.config.getint('modem', 'baudrate')
        self.sms_poll = self.config.getint('modem', 'sms_poll')
        self.database_file = self.config.get('server', 'database_file')
        self.endpoint = self.config.get('server', 'endpoint')
        self.mock_modem = self.config.getboolean('modem', 'mock')
        self.secret = self.config.get('subscribe', 'secret')
        self.max_subscriptions = self.config.getint('subscribe', 'max_subscriptions')

    def post_results(self):
        '''
          Return None
          private method which POSTS messages stored in the database
          to endpoints defined by self.endpoint
        '''
        messages = MessageData.select();
        for message in messages:
            params = urllib.urlencode({
                'sent' :     message.sent,
                'timestamp' : message.received,
                'text' :     message.text,
                'sender' :   message.sender})
            print "Received ", params
            print self.endpoint
            message.destroySelf()
            response = urllib.urlopen(self.endpoint, params).read()
            print response
            for endpoint in self.subscriptions:
                print "Posting to %s " % endpoint
                try:
                    response = urllib.urlopen(endpoint, params).read()
                except Exception, e:
                    print e


    def index(self):
        '''
          Return a semi-well-formed HTML file with REST documentation
          Public method
        '''
        return "<html><body><h1>SMS REST</h1><pre>"+DOCUMENTATION+"</pre></body></html>"
    index.exposed = True

    def reset(self):
        MessageData.dropTable(True)
        MessageData.createTable()
        return "Reset complete"
    reset.exposed = True


    def status(self):
        '''
          Exposed method /status
          returns plain-text string of
          OK
          [Status message]
        '''
        status = []
        # TODO: Add signal strength number provided by pygsm
        if self.mock_modem:
            status.append('Mocking modem. No messages will be sent')
        return "OK\n"+"\n".join(status)
    status.exposed = True


    # List API method
    # Try to use If-Modified-Since
    # def list(self):
    # import simplejson
    #     messages = MessageData.select();
    #     data = {}
    #     # items = [x + ': ' + y for x,y in cherrypy.request.headers.get('If-Modified-Since')]
    #     # return "<br />".join(items)
    #     
    #     data['messages'] = []
    #     data['message_count'] = messages.count()
    #     for message in messages:
    #         m = { 'text': message.text, 'sender' : message.sender, \
    #           'sent' : message.sent, 'received' : message.received}
    #         data['messages'].append(m)
    #     return simplejson.dumps(data)
    #     # xml.appendChild(messages)
    #     # for msg in self.messages_in_queue:
    #     #     x = xml.createElement('message')
    #     #     x.setAttribute('sent', str(msg.sent))
    #     #     x.setAttribute('received', str(msg.received))
    #     #     t = xml.createElement('text')
    #     #     n = xml.createElement('number')
    #     #     n.appendChild(xml.createTextNode(msg.sender))
    #     #     t.appendChild(xml.createTextNode(msg.text))
    #     #     messages.appendChild(x)
    #     #     x.appendChild(t)
    #     #     x.appendChild(n)
    #     cherrypy.response.headers['Content-Type'] = 'text/xml'
    #     return xml.toxml('UTF-8')
    # list.exposed = True


    def subscribe(self, endpoint=None, secret=None):
        '''
          Return a status message
          Given POST variables endpoint and secret
          Subscribes a site to POST updates from sms_rest.py. The given endpoint
          will be included in future calls.
        '''
        if secret == self.secret:
            if (len(self.subscriptions) + 1) > self.max_subscriptions:
                return "no subscriptions left"
            self.subscriptions.append(endpoint)
            return "subscribed"
        else:
            return "provided secret was incorrect"
    subscribe.exposed = True

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
            self.modem.send_sms(number, message)
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
                MessageData(sent=int(time.mktime(msg.sent.timetuple())), sender=msg.sender, \
                    received=int(time.mktime(msg.received.timetuple())), text=msg.text)
        except Exception, e:
            print "Exception caught: ", e
        self.post_results()

if __name__=="__main__":
    cherrypy.quickstart(SMSServer())
