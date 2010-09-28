#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from optparse import OptionParser
from sqlobject import SQLObject, IntCol, StringCol, BLOBCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

'''

  mock_client: this is a script that helps testing of SlingshotSMS
  without having a real modem or other infrastructre

'''

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


parser = OptionParser()

parser.add_option("-t", "--text", dest="text",
                  help="Your Message")
parser.add_option("-s", "--sender", dest="sender",
                  help="Your Message")
parser.add_option("-n", "--timestamp", dest="sent",
                  help="Your Message")

(options, args) = parser.parse_args()

MessageData(text = options.text, sender = options.sender, sent = int(options.sent))
