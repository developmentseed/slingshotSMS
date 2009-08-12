import cherrypy, pygsm, sqlite3, ConfigParser, time, urllib, sys, os, re
from sqlobject import SQLObject, IntCol, StringCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection
from xml.dom import minidom

'''
  rSMS
  version 0.2
  Tom MacWright
  http://www.developmentseed.org/
'''

CONFIG = "rsms.cfg"

class MessageData(SQLObject):
    _connection = SQLiteConnection('rsms.db')
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
        if not os.path.exists('rsms.db'):
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
        ''' Filter method '''
        nix_mtcba_re = re.compile('tty.MTCBA')
        if nix_mtcba_re.match(port):
            return True

    def recommend_port(self):
        print '''
A port could not be opened to connect to your modem. If you have not 
installed the drivers that came with the modem, please do so, and then edit 
rsms.cfg with the modem's port and baudrate.
Edit the port number behind the line [%s]
Ports will be recommended below if found:\n''' % self.modem_section
        if sys.platform == 'darwin':
            # only runs on mac
            for p in filter(self.nix_mtcba, os.listdir('/dev')):
                print "MultiModem: /dev/%s" % p
        elif sys.platform == 'win32':
            import scanwin, serial
            for order, port, desc, hwid in sorted(scanwin.comports()):
                print "%-10s: %s (%s) ->" % (port, desc, hwid)
        

    def parse_config(self):
        '''
          Private method parse_config
          no params
        '''
        defaults = { 'port': '/dev/tty.MTCBA-U-G1a20', 'baudrate': '115200', \
            'sms_poll' : 2, 'database_file' : 'rsms.db', \
            'endpoint' : 'http://localhost/sms', 'mock' : False, 'max_subscriptions' : 10 }

        self.config = ConfigParser.SafeConfigParser(defaults)

        # For mac distributions, look up the .app directory structure
        # to find rsms.cfg alongside the double-clickable
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

        self.config.read(config_path)
        self.port =       self.config.get       (self.modem_section, 'port')
        self.baudrate =   self.config.getint    (self.modem_section, 'baudrate')
        self.sms_poll =   self.config.getint    (self.modem_section, 'sms_poll')
        self.mock_modem = self.config.getboolean(self.modem_section, 'mock')
        self.database_file = self.config.get('server', 'database_file')
        self.endpoint = self.config.get('server', 'endpoint')
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
            try:
                response = urllib.urlopen(self.endpoint, params).read()
                # only called when urlopen succeeds here
                message.destroySelf()
                print response
            except Exception, e:
                print e
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
        try:
            documentation = open('README').read()
            return "<html><body><h1>SMS REST</h1>"+documentation+"</body></html>"
        except Exception, e:
            return "<html><body><h1>SMS REST</h1>README File not found</body></html>"
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
        for s in self.subscriptions:
            status.append('endpoint: %s' %  s)
        return "OK\n"+"\n".join(status)
    status.exposed = True



    def subscribe(self, endpoint=None, secret=None):
        '''
          Return a status message
          Given POST variables endpoint and secret
          Subscribes a site to POST updates from rSMS The given endpoint
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



if __name__=="__main__":
    if sys.platform == 'darwin' and hasattr(sys, 'frozen'):
        # only runs on .app
        cherrypy.config.update("../../../server.cfg")
    else:
        cherrypy.config.update("server.cfg")
    cherrypy.quickstart(SMSServer())
