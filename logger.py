#!/bin/python
# logger.py
import time
import sys

class Logger (object):
    levels = ['','ERRR','WARN','INFO','DEBG']

    def __init__ (this,stdoutlevel=3,filelevel=0,file_=None):
        this.stdoutlevel = stdoutlevel
        this.filelevel = filelevel
        if filelevel:
            this.file = open (file_ + '@' + str (int (time.time ())) + '.txt','x')

    def log (this,*messages,l=3):
        t = int (time.time () * 1000000) # microseconds
        if this.stdoutlevel and l <= this.stdoutlevel:
            print (this.levels[l],t,*messages)
        if this.filelevel and l <= this.filelevel:
            print (this.levels[l],t,*messages,file=this.file)

    def linebreak (this,l=2):
        ''' blank line without timestamp '''
        if this.stdoutlevel and l <= this.stdoutlevel:
            print ()
        if this.filelevel and l <= this.filelevel:
            print (file=this.file)
