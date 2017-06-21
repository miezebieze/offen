#!/bin/python
'''
'''
import offen

class Story (offen.Story):

    def __init__ (this):
        super ().__init__ ()
        this.T = { } # container for finding Things without references

class Thing (offen.StoryObject):
    ''' A more interactive thing than StoryObject.
    Put your text in this.strings for easy telling.
    '''
    # runtime vars
    examined_once = False

    # writetime vars (overwrite these)
    strings = { }       # dicitionary for this.tell ()
    description = ''    # you probably will overwrite this with a @property
    _label = ''         # name to find this in S.T without a reference

    def __init__ (this,S,label=None):
        super ().__init__ (S,label)
        if not this._label:
            this._label = this
        this.S.T[this._label] = this

    def tell (this,name):
        ''' Tell stuff from this.strings by their key only. '''
        if name in this.strings.keys ():
            this.S.P.add (this.strings[name])
        else:
            this.S.P.add ("Thing '{this.__repr__}' with label '{this.label}' does not have a string with name '{name}'.".format (this=this,name=name))

    def __set_label (this,label):
        if this._label != label:
            del this.S.T[this._label]
            this._label = label
            this.S.T[label] = this
    label = property (lambda this: this._label,__set_label)

class Room (Thing):

    def __init__ (this,S,label=None):
        super ().__init__ (S,label)
        this.go_N = this.buttons['w']
        this.go_E = this.buttons['d']
        this.go_S = this.buttons['s']
        this.go_W = this.buttons['a']

class Character (Thing):

    def __init__ (this,S,label=None):
        super ().__init__ (S,label)

