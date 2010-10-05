#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
import sys, time, readline, multiprocessing
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


class OutMessageData(SQLObject):
    _connection = SQLiteConnection('slingshotsms.db')
    number = StringCol()
    text = StringCol()

def sent_watcher():
    while True:
        messages = OutMessageData.select()
        for message in messages:
            print "sent: \n%s\n to %s\n>" % (message.text, message.number)
            message.destroySelf()
        time.sleep(5)

if __name__ == '__main__':
    o = OptionParser(usage='Usage: %prog 19777777 "A message"')
    o.add_option('--i', '--interactive', action='store_true', dest='interactive')
    (opts, args) = o.parse_args()
    if opts.interactive:
        print "Interactive mode: type exit to quit"
        sender = raw_input('[what number should messages originate from?]: ')

        watcher = multiprocessing.Process(target=sent_watcher)
        watcher.start()

        input = True
        while input:
            input = raw_input('> ')
            if input == 'exit':
                watcher.join()
                sys.exit(0)
            MessageData(sender=sender, text=input, sent=int(time.time()))
            print "sent message"
    elif len(args) < 2:
        o.print_usage()
        sys.exit(1)
    else:
        MessageData(sender=args[0], text=args[1], sent=int(time.time()))
