#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

'''
  SlingshotSMS
  version 2.0 Goliath
  Tom MacWright
  http://www.developmentseed.org/
'''

from Tkinter import *
from multiprocessing import Process
import slingshotsms

class App:

    def __init__(self, master):

        frame = Frame(master)
        frame.pack()

        self.console = Text(frame)
        self.console.pack()

        self.button = Button(frame, text="Quit", fg="red", command=frame.quit)
        self.button.pack(side=LEFT)

        self.start_button = Button(frame, text="Start", command=self.start)
        self.start_button.pack(side=LEFT)

        self.stop_button = Button(frame, text="Stop", command=self.stop)
        self.stop_button.pack(side=LEFT)

    def stop(self):
        if self.p:
            self.p.terminate()

    def start(self):
        self.p = Process(target=slingshotsms.start)
        self.p.start()

root = Tk()
root.title("SlingshotSMS")

app = App(root)

root.mainloop()
