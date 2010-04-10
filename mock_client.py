from optparse import OptionParser
from sqlobject import SQLObject, IntCol, StringCol, BLOBCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

class ContactData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    # in reference to
    # http://en.wikipedia.org/wiki/VCard
    TEL = StringCol()
    UID = StringCol()
    PHOTO = BLOBCol()
    N = StringCol()
    FN = StringCol()
    # contains all data as serialized vc, including the above columns
    data = BLOBCol()

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
