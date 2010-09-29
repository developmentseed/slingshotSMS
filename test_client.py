#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import sys, time
from optparse import OptionParser
from sqlobject import SQLObject, IntCol, StringCol, BLOBCol
from sqlobject.sqlite.sqliteconnection import SQLiteConnection

'''

  mock_client: this is a script that helps testing of SlingshotSMS
  without having a real modem or other infrastructre

'''

class MessageData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    sent = IntCol(default=None)
    received = IntCol(default=None)
    sender = StringCol()
    text = StringCol()

if __name__ == '__main__':
    o = OptionParser(usage='Usage: %prog 19777777 "A message"')
    (opts, args) = o.parse_args()
    if len(args) < 2:
        o.print_usage()
        sys.exit(1)
    MessageData(sender=args[0], text=args[1], sent=int(time.time()))
