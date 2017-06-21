#!/bin/python
# offen.py 5
import pygame
import json
import time
import functools # partial,wraps
import types # FunctionType
import pdb
import sys

#-DOC-------------------------------------------------------------------------#
"""
# configuration file options (game.json)
# self explanatory
"fontsize": 16
"fontname": null
"screen_width": 720
"screen_height": 400

# keyboard layout
"keyboard": "qwerty"

# margin around text inside buttons
"button_margin": 6

# gap between adjacent buttons
"buttons_gap": 2,
# margin around any group buttons
"buttons_margin": 2,

# number of buttons in buttonpanel on x/y
# # changing these is not supported
"buttonpanel_nx": 5
"buttonpanel_ny": 4
# width of button panel, when negative, it's relative to window (positive not implemented)
"buttonpanel_width": -170
# # (the button panel is always in the lower left corner)

# width of sidebar
"sidebar_width": 170
# space around stuff in sidebar
"sidebar_margin": 2
"""

#-SETUP-----------------------------------------------------------------------#
# Default config:
# having the json handy for pasting into a file is nice.
gameconfig = json.loads ('''{
"undo_scrollback": 128,

"keyboard": "qwerty",
"fontsize": 16,
"fontname": null,
"screen_width": 900,
"screen_height": 600,

"colours": {
    "background": [ 33,33,33,255 ],
    "button_shadow": [ 45,45,45,255 ],
    "button_label": [ 255,255,255,255 ],
    "button_hint": [ 200,200,200,255 ],
    "button_border": [ 200,200,200,255 ],
    "text": [ 255,255,255,255 ]
},

"textbox_margin": 5,
"textbox_gap": 5,

"button_margin": 5,

"buttons_gap": 4,
"buttons_margin": 3,

"buttonpanel_nx": 5,
"buttonpanel_ny": 4,

"sidebar_width": 170,
"sidebar_margin": 2,

"keyboard_layouts": {
    "qwerty": [ "1","2","3","4","5", "q","w","e","r","t", "a","s","d","f","g", "z","x","c","v","b" ]
    }
} ''')

# Try to load game.json:
try:
    with open ('offen.json','r') as conf:
        gameconfig.update (json.load (conf))
except FileNotFoundError:
    pass

# Compute and add additional settings:
gameconfig.update ({
    'buttonpanel_keysyms': ['K_{0}'.format (k) for k in gameconfig['keyboard_layouts'][gameconfig['keyboard']]],
    'menubar_keysyms': ['K_ESCAPE'] + ['K_F{0}'.format (n+1) for n in range (12)]
    })

#-STUFF-----------------------------------------------------------------------#
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
logger = Logger (4)

class BaseOffenException (BaseException): ...
def nop (*args,**kwargs): ...

#-WRITER_INTERFACE_PARTS------------------------------------------------------#
class Button (object):
    ''' Has a function and a label.
        >>> this.set ('label')                  # set label
        >>> this.set (function)                 # set function
        >>> this.set ('label',function)         # set both
        >>> this.set (( function,'label' ))     # set both; can be an iterator; order does not matter
        >>> SO = StoryObject ()                 # make an instance;
        # You can use offen.StoryObject or just make a class which has attributes '__call__' and 'label'
        >>> this.set (SO)                       # set both; needs an instance!; gets label from SO
        >>> this.set (SO,'explicit')            # set to SO; set label explicitly; order matters!
        >>> this.set ('label1','label2')        # set label to 'label2'; last one wins
        >>> this ()                             # call function or object
        >>> this.clear ()                       # clear; reset values
    '''
    _function = nop
    label = ''

    def __init__ (this,buttons,name):
        this.buttons = buttons
        this.name = name

    def __set_function (this,function):
        if function is not this._function:
            if isinstance (this._function,StoryObject):
                this._function.unregister_parent (this)
            this._function = function
            if isinstance (this._function,StoryObject):
                this._function.register_parent (this)
    function = property (lambda this: this._function,__set_function)

    def set (this,*values):
        for value in values:
            if isinstance (value,Button):
                this.function,this.label = value.function,value.label
            elif hasattr (value,'__call__'):
                this.function = value
                if hasattr (value,'label'):
                    this.set (value.label)
                else:
                    this.set (value.__name__)
            elif isinstance (value,str):
                this.label = value
                this.buttons.updates.add (this.name)
            elif hasattr (value,'__iter__'):
                # The has to be after str, because str is an iterable in python 3
                this.set (*value)
            else:
                logger.log ('Invalid input for Button:',value,l=1)
                raise BaseOffenException ()

    def update (this):
        this.buttons.updates.add (this)

    def __call__ (this):
        return this.function ()

    def clear (this):
        this.set (nop,'')

class Buttons (object):
    ''' Holds the Buttons of one tab.
    dict wrapper with explicitly changeable keys, which begin with K_
    access can happen without K_
    deleting this makes it deleteing all its buttons
        >>> this.register_key ('b')             # add key
        >>> this.register_keys ('b','F1')       # add more keys
        >>> this.K_b                            # get Button
        >>> this['b']
        >>> this['K_b']
        >>> this.K_b.set ('label',nop)          # set Button
        >>> this.clear ()                       # same (until del works)
    '''
    NOBUTTON = 'No button with key %s / %s registered.'

    def __init__ (this,story,object):
        this.story = story
        this.object = object
        this.keys = set ()
        this.updates = set ()

    def register_keys (this,*keys):
        for key in keys:
            if key.startswith ('K_'):
                this.keys.add (key)
                setattr (this,key,Button (this,key))
            else:
                this.register_keys ('K_' + key)
        this.story.game.register_button_keys (this.object,keys)

    def __getitem__ (this,k):
        if k.startswith ('K_'):
            if k not in this.keys:
                raise KeyError (this.NOBUTTON % (k,k[-1]))
            return getattr (this,k)
        else:
            return this['K_' + k]

    def __setitem__ (this,k,v):
        if k.startswith ('K_'):
            if k not in this.keys:
                raise KeyError (this.NOBUTTON % (k,k[-1]))
            this[k].set (v)
            this.updates.add (k)
        else:
            this['K_' + k] = v

    def clear (this):
        this.updates.clear ()
        for k in this.keys:
            this[k].clear ()

class Paragraphs (object):
    ''' Holds the paragraphs of one tab.
    dict wrapper with some conveniences
    lots of double underscores
        >>> this.add ('paragraph')              # add paragraph
        >>> this.add ('paragraph','p')          # add more
        >>> this.clear ()                       # clear
    '''

    def __init__ (this,story,name):
        this.story = story
        this.name = name
        this.paragraphs = { }
        this.updates = set ()

    def clear (this):
        ''' delete all paragraphs '''
        this.updates.clear ()
        this.updates.update (this.keys ())
        this.paragraphs.clear ()

    def add (this,*strings):
        for string in strings:
            t = str (time.time ())
            this.paragraphs[t] = str (string)
            this.updates.add (t)

    def __getitem__ (this,k):
        return this.paragraphs[k]
    def keys (this):
        return this.paragraphs.keys ()
    def values (this):
        return this.paragraphs.values ()
    def items (this):
        return this.paragraphs.items ()

#-WRITER_INTERFACE------------------------------------------------------------#
class StoryObject (object):
    ''' A generic thing to give to give to your Buttons.
        Inherit this when creating classes with @Story.object .
        If you define __init__, the second parameter must be the story object.
        If you define __init__, __call__ or __delete__, you need to write either of
            super ().__init__ (S,[label,][...,]*a,**kw)
            super ().__call__ ()
            super ().__delete__ ()
        on the next line.
    '''
    # TODO: have an automatic super ().__****__ (S)
    _label = None

    def __init__ (this,S,label=None,*a,**kw):
        this.S = S
        if label is not None:
            this._label = label
        elif this._label is None:
            label = this.__repr__
            logger.log ("StoryObject '{}' has no label.".format (this),l=2)
        # else: skip
        S.new_buttons (this)
        this.buttons = this.S.buttonss[this]
        this.parents = [] # things that take an interest in changes of this.label

    def register_parent (this,parent):
        this.parents.append (parent)
    def unregister_parent (this,parent):
        if parent in this.parents:
            del this.parents[this.parents.index (parent)]

    def __set_label (this,label):
        if label != this._label:
            for i in this.parents:
                i.update (this)
            this._label = label
    label = property (lambda this: this._label,__set_label)

    def __call__ (this):
        ''' Overwrite me! '''

    def __delete__ (this):
        ''' Overwrite me! '''
        this.S.del_buttons (this)

class Story (object):
    ''' main object and writer interface

    quick access to important instance members and their class:
        B: current buttons              Buttons
        P: cureent paragraphs           Paragraphs
        V: variables                    dict
    '''
    keep_running = True
    active_buttons = None
    active_paragraphs = None

    def function (this,f,*a,**kw):
        ''' Create functions with automatical access to the main Story object. '''
        @functools.wraps (f)
        def decorated (*a,**kw):
            return f (this,*a,**kw)
        return decorated

    def object (this,c,*a,**kw):
        ''' Create objects with automatical access to the main Story object.
            You should inherit offen.StoryObject.
        '''
        @functools.wraps (c)
        def decorated (*a,**kw):
            return c (this,*a,**kw)
        return decorated

    def stop (this):
        this.keep_running = False

    def new_buttons (this,object):
        if object not in this.buttonss.keys ():
            this.game.register_buttons (object)
            this.buttonss[object] = Buttons (this,object)
            this.buttonss[object].register_keys (*gameconfig['buttonpanel_keysyms'])
        else:
            logger.log ('Story already has a Buttons:',object.label,'Not creating new one.',l=2)

    def del_buttons (this,object):
        if object in this.buttonss.keys ():
            this.game.unregister_buttons (object)
            del this.buttonss[object]
        else:
            logger.log ('Story does not has a Buttons:',object.label,'Not deleting.',l=2)

    def new_paragraphs (this,object):
        if object not in this.paragraphss.keys ():
            this.game.register_paragraphs (object)
            this.paragraphss[object] = Paragraphs (this,object)
        else:
            logger.log ('Story already has a Paragraphs:',object.label,'Not creating new one.',l=2)

    def del_paragraphs (this,object):
        if object in this.paragraphss.keys ():
            this.game.unregister_paragraphs (object)
            del this.paragraphss[object]
        else:
            logger.log ('Story does not has a Paragraphs:',object.label,'Not deleting.',l=2)

    def tell (this,*strings):
        this.P.add (*strings)

    def __init__ (this):
        this.game = Main (this)
        this.vars = { }
        this.paragraphss = { }
        this.buttonss = { }
        this.start = nop

        # A Tab, that holds all the buttons for the menubar. It has no paragraphs.
        this.game.register_buttons ('menu')
        this.M = Buttons (this,'menu')
        this.M.register_keys (*gameconfig['menubar_keysyms'])

        # The main Buttons and Paragraphs
        this.new_paragraphs ('system')
        this.new_buttons ('system')
        this.P = 'system'
        this.B = 'system'

    def run (this):
        this.game.run ()

    ### single letter attributes
    def reset_vars (this,vars):
        if isinstance (vars,dict):
            this.vars = vars
        else: # assume json
            this.vars = json.loads (vars)
    def update_vars (this,vars):
        if isinstance (vars,dict):
            this.vars.update (vars)
        else: # assume json
            this.vars.update (json.loads (vars))
    V = property (lambda this: this.vars,reset_vars)

    def __set_p (this,p):
        if p in this.paragraphss.keys ():
            this.active_paragraphs = this.paragraphss[p]
        else:
            raise BaseOffenException ('Not in names of registered Paragraphss: ' + p)
    P = property (lambda this: this.active_paragraphs,__set_p)

    def __set_b (this,b):
        if b in this.buttonss.keys ():
            this.active_buttons = this.buttonss[b]
        else:
            raise BaseOffenException ('Not in names of registered Buttonss: ' + b)
    B = property (lambda this: this.active_buttons,__set_b)


#-USER_INTERFACE--------------------------------------------------------------#
class Main (object):
    textbox_scroll_speed = 15

    def run (this):
        S = this.story
        S.start ()

        debug_areas = 0

        this.textbox_scroll = 0
        while S.keep_running:
            # reset
            #this.rerender_textbox = False
            button_id = None

            # events
            for e in pygame.event.get ():
                if e.type == pygame.QUIT:
                    S.stop ()
                elif e.type == pygame.KEYDOWN:
                    # keyboard scrolling
                    try:
                        button_id = this.keysym_constants[e.key]
                    except KeyError:
                        ...
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if this.buttonpanel_rect.collidepoint (e.pos):
                        if e.button == 1:
                            for i,rect in this.button_rects.items ():
                                if rect.collidepoint (e.pos):
                                    button_id = i
                    elif this.textbox_rect.collidepoint (e.pos):
                        if e.button == 4:
                            if not this.get_textbox_text_height (S.P.name) < this.textbox_rect.height:
                                this.textbox_scroll += this.textbox_scroll_speed
                                if this.textbox_scroll > this.get_textbox_text_height (S.P.name) - this.textbox_rect.height:
                                    this.textbox_scroll = this.get_textbox_text_height (S.P.name) - this.textbox_rect.height
                        elif e.button == 5:
                            this.textbox_scroll -= this.textbox_scroll_speed
                            if this.textbox_scroll < 0:
                                this.textbox_scroll = 0

            if button_id is not None:
                try:
                    S.B[button_id].function ()
                except KeyError:
                    S.M[button_id].function ()

            ### update / (re-)render stuff
            this.process_buttons_updates (S.M)
            this.process_buttons_updates (S.B)
            this.process_paragraphs_updates (S.P)

            ### draw
            this.screen.fill (gameconfig['colours']['background'])
            # TODO visual scroll indicator
            this.draw_button_shadows ()
            this.draw_buttons (S.M)
            this.draw_buttons (S.B)
            this.draw_paragraphs (S.P)
            #this.screen.blit (this.textbox_surf,this.textbox_rect.topleft)
            if debug_areas:
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.textbox_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.buttonpanel_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.sidebar_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.infobox_rect,1)

            pygame.display.flip ()
            pygame.time.delay (100)

    def draw_button_shadows (this):
        for id,i in this.button_rects.items ():
            pygame.draw.rect (this.screen,gameconfig['colours']['button_shadow'],i)

    def draw_buttons (this,buttons):
        for id,surf in this.button_surfs[buttons.object].items ():
            if surf is not None:
                r = this.button_rects[id]
                pygame.draw.rect (this.screen,gameconfig['colours']['button_border'],r,1)
                this.screen.blit (surf,r.move ( gameconfig['button_margin'],r.height/2 - surf.get_rect ().height/2 ))

    def draw_paragraphs (this,paragraphs):
        #if this.rerender_textbox:
        _tb_rect = this.textbox_rect
        # area of textbox - margins
        bottom = _tb_rect.bottom - gameconfig['textbox_margin']
        top = _tb_rect.top + gameconfig['textbox_margin']
        # bottom of bottomest paragraph
        drawpos = bottom + this.textbox_scroll
        for i,paragraph in enumerate (reversed (sorted (this.paragraph_surfs[paragraphs.name].items ()))):
            if drawpos <= top: break
            p_surf = paragraph[1]
            p_rect = p_surf.get_rect ()
            p_rect.topleft = ( _tb_rect.x + gameconfig['textbox_margin'],drawpos - p_rect.height )

            if _tb_rect.contains (p_rect):
                this.screen.blit (p_surf,p_rect)
            # TODO render overlapping paragraphs
            drawpos = drawpos - p_surf.get_rect ().height - gameconfig['textbox_gap']

    def get_textbox_text_height (this,name):
        return sum ([ps.get_rect ().height for ps in this.paragraph_surfs[name].values ()]) + gameconfig['textbox_gap'] * (len (this.paragraph_surfs[name]) - 1)

    def process_buttons_updates (this,buttons):
        # update buttons and rerender their labels
        for id_ in buttons.updates:
            if buttons[id_].label:
                this.button_surfs[buttons.object][id_] = this.font.render (buttons[id_].label,1,gameconfig['colours']['button_label'])
            elif id_ in this.button_surfs[buttons.object]:
                this.button_surfs[buttons.object][id_] = None
        buttons.updates.clear ()

    def process_paragraphs_updates (this,paragraphs):
        # update paragraphs in textbox
        for i in paragraphs.updates:
            if i not in paragraphs.keys ():
                del this.paragraph_surfs[paragraphs.name][i]
            else:
                this.paragraph_surfs[paragraphs.name][i] = this.render_paragraph (paragraphs[i])
        paragraphs.updates.clear ()

    def register_buttons (this,name):
        if name not in this.button_surfs.keys ():
            this.button_surfs[name] = { }
    def unregister_buttons (this,name):
        if name in this.button_surfs.keys ():
            del this.button_surfs[name]

    def register_paragraphs (this,name):
        if name not in this.paragraph_surfs.keys ():
            this.paragraph_surfs[name] = { }
    def unregister_paragraphs (this,name):
        if name in this.paragraph_surfs.keys ():
            del this.paragraph_surfs[name]

    def register_button_keys (this,name,keys):
        if name in this.button_surfs.keys ():
            this.button_surfs[name].update ({k:None for k in keys})
        else:
            logger.log ('Buttons is not registered:',name,l=1)
            raise BaseOffenException ()

    def render_paragraph (this,paragraph):
        # render words
        word_surfs = [this.font.render (word,1,gameconfig['colours']['text']) for word in paragraph.split (' ')]

        # stuff
        space_rect = this.space_surf.get_rect ()
        lines = [ ]
        x = this.textbox_rect.width
        maxwidth = x - 2 * gameconfig['textbox_margin']
        line_rect = pygame.Rect (0,0,maxwidth,space_rect.height)

        # make lines and blit words into
        for word in word_surfs:
            if x + word.get_rect ().width > maxwidth:
                x = 0
                lines.append (pygame.Surface (line_rect.size,this.screen.get_flags ()))
                lines[-1].fill (gameconfig['colours']['background'])
            lines[-1].blit (word,( x,0 ))
            x += word.get_rect ().width + space_rect.width

        # make paragraph and blit lines into
        paragraph_surf = pygame.Surface (( maxwidth,len (lines) * space_rect.height ),this.screen.get_flags ())
        paragraph_surf.fill (gameconfig['colours']['background'])
        for x in range (len (lines)):
            paragraph_surf.blit (lines[x],( 0,x * space_rect.height ))

        return paragraph_surf

    def __init__ (this,story):
        pygame.init ()
        this.story = story
        this.screen = pygame.display.set_mode (( gameconfig['screen_width'],gameconfig['screen_height'] ),pygame.SRCALPHA,32)
        this.screen_rect = this.screen.get_rect ()
        this.font = pygame.font.Font (gameconfig['fontname'],gameconfig['fontsize'])
        this.space_surf = this.font.render (' ',0,( 0,0,0 ))

        this.paragraph_surfs = { } # {Paragraphs.name:{pid:surf}}
        this.button_surfs = { } # {Buttons.object:{buttonkey:surf}}

        this.ui_setup ()

    def ui_setup (this):
        ''' Initialize widgets and keys.
        I did my best but if you like pretty code or PEP8, you really should look at the code. '''
        # Pygame constant to name bindings.
        this.keysym_constants = { }
        this.keysym_constants.update ({getattr (pygame,k):k for k in gameconfig['buttonpanel_keysyms']})
        this.keysym_constants.update ({getattr (pygame,k):k for k in gameconfig['menubar_keysyms']})

        # Set up button sizes and buttonpanel_rect.
        button_height = gameconfig['button_margin']*2+gameconfig['fontsize']
        buttonpanel_height = gameconfig['buttonpanel_ny']*button_height+(gameconfig['buttonpanel_ny']-1)*gameconfig['buttons_gap']+2*gameconfig['buttons_margin']
        buttonpanel_width = this.screen_rect.width - gameconfig['sidebar_width']
        this.buttonpanel_rect = pygame.Rect (
                0,this.screen_rect.height-buttonpanel_height,buttonpanel_width,buttonpanel_height)
        button_width = (this.buttonpanel_rect.width-2*gameconfig['buttons_margin']-(gameconfig['buttonpanel_nx']-1)*gameconfig['buttons_gap'])/gameconfig['buttonpanel_nx']

        # Set up buttonpanel buttons and key bindings.
        this.button_rects = { }
        for y in range (gameconfig['buttonpanel_ny']):
            for x in range (gameconfig['buttonpanel_nx']):
                this.button_rects[gameconfig['buttonpanel_keysyms'][x+y*gameconfig['buttonpanel_nx']]] = pygame.Rect (
                        this.buttonpanel_rect.x+gameconfig['buttons_margin']+x*(button_width+gameconfig['buttons_gap']),
                        this.buttonpanel_rect.y+gameconfig['buttons_margin']+y*(button_height+gameconfig['buttons_gap']),
                        button_width,button_height)

        # Set up menubar key bindings.
        for i,key in enumerate (gameconfig['menubar_keysyms'][:gameconfig['buttonpanel_nx']]):
            this.button_rects[key] = pygame.Rect (
                        gameconfig['buttons_margin']+i*(button_width+gameconfig['buttons_gap']),
                        gameconfig['buttons_margin'],
                        button_width,
                        button_height)

        # Set up text box.
        this.textbox_rect = pygame.Rect (
                0,
                button_height+2*gameconfig['buttons_margin'],
                this.screen_rect.width-gameconfig['sidebar_width'],
                this.screen_rect.height-this.buttonpanel_rect.height-button_height-2*gameconfig['buttons_margin'])
        # Set up side bar.
        this.sidebar_rect = pygame.Rect (
                this.textbox_rect.width,
                button_height+2*gameconfig['buttons_margin'],
                gameconfig['sidebar_width'],
                this.screen_rect.height-button_height-2*gameconfig['buttons_margin'])
        # Set up info box.
        this.infobox_rect = pygame.Rect (
                this.textbox_rect.width,
                0,
                gameconfig['sidebar_width'],
                this.screen_rect.height-this.sidebar_rect.height)

