import cherrypy, pygsm, sqlite3, ConfigParser, time, urllib
from sqlobject import *
from sqlobject.sqlite.sqliteconnection import SQLiteConnection
from xml.dom import minidom

'''
  sms_rest
  version 0.1
  Tom MacWright
  http://www.developmentseed.org/
'''


DOCUMENTATION = '''

This is sms_rest, a minimal SMS server which connects GSM modems to 
websites and applications via a simple interface. It provides only 
a few endpoints for this purpose:

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


  TROUBLESHOOTING:

  * running this server from the command line with `python sms_rest.py`
    Will give a log of modem messages.
    CMS ERROR: 515 indicates that the modem has not connected yet

  * Set the serial port of the modem in sms_rest.cfg. It will be autodetected
    in the future, but we want to maintain compatibility across modems, so it
    currently is not.
'''

class MessageData(SQLObject):
    _connection = SQLiteConnection('sms_rest.db')
    sent = IntCol()
    received = IntCol()
    sender = StringCol()
    text = StringCol()

class SMSServer:
    # The port varies, but I don't know a way to automatically determine it yet.
    # it is too much to ask the user to 'ls /dev/tty*'
    def __init__(self):
        self.parse_config()
        if self.mock_modem == False:
            self.modem = pygsm.GsmModem(port=self.port, baudrate=self.baudrate)
        self.message_watcher = cherrypy.process.plugins.Monitor(cherrypy.engine, \
            self.retrieve_sms, self.sms_poll)
        self.message_watcher.subscribe()
        self.message_watcher.start()
        self.messages_in_queue = []
        self.subscriptions = []

    def index(self):
        return "<html><body><h1>SMS REST</h1><pre>"+DOCUMENTATION+"</pre></body></html>"
    index.exposed = True

    def reset(self):
        MessageData.dropTable(True)
        MessageData.createTable()
        return "Reset complete"
    reset.exposed = True

    def status(self):
        status = []
        if self.mock_modem:
            status.append('Mocking modem. No messages will be sent')
        return "OK\n"+"\n".join(status)
    status.exposed = True

    def parse_config(self):
        defaults = { 'port': '/dev/tty.MTCBA-U-G1a20', 'baudrate': '115200', \
            'sms_poll' : 2, 'database_file' : 'sms_rest.db', \
            'endpoint' : 'http://localhost/sms', 'mock' : False, 'max_subscriptions' : 10 }
        self.config = ConfigParser.SafeConfigParser(defaults)
        self.config.read('sms_rest.cfg')
        self.port = self.config.get('modem', 'port')
        self.baudrate = self.config.getint('modem', 'baudrate')
        self.sms_poll = self.config.getint('modem', 'sms_poll')
        self.database_file = self.config.get('server', 'database_file')
        self.endpoint = self.config.get('server', 'endpoint')
        self.mock_modem = self.config.getboolean('modem', 'mock')
        self.secret = self.config.get('subscribe', 'secret')
        self.max_subscriptions = self.config.getint('subscribe', 'max_subscriptions')

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
        if secret == self.secret:
            if (len(self.subscriptions) + 1) > self.max_subscriptions:
                return "no subscriptions left"
            self.subscriptions.append(endpoint)
            return "subscribed"
        else:
            return "provided secret was incorrect"
    subscribe.exposed = True

    def post_results(self):
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


    def send(self, number=None, message=None):
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

# Run server
cherrypy.quickstart(SMSServer())
