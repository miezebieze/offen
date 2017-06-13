#!/bin/python
# offen.py 5
import pygame
import json
import time
import functools # partial,wraps
import types # FunctionType
import pdb

import logger
logger = logger.Logger (4)

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

"colour_background": [ 51,51,51,255 ],
"textbox_margin": 5,
"textbox_gap": 5,

"button_margin": 6,

"buttons_gap": 2,
"buttons_margin": 2,

"buttonpanel_nx": 5,
"buttonpanel_ny": 4,

"sidebar_width": 170,
"sidebar_margin": 2
} ''')

# Try to load game.json:
try:
    with open ('game.json','r') as conf:
        gameconfig.update (json.load (conf))
except FileNotFoundError:
    pass

# Compute and add additional settings:
KEYBOARDLAYOUTS = {
    'qwerty': [ "1","2","3","4","5", "q","w","e","r","t", "a","s","d","f","g", "z","x","c","v","b" ]
    }

gameconfig.update ({
    'buttonpanel_keysyms': ['K_{0}'.format (k) for k in KEYBOARDLAYOUTS[gameconfig['keyboard']]],
    'menubar_keysyms': ['K_ESCAPE'] + ['K_F{0}'.format (n+1) for n in range (12)]
    })
#-STUFF-----------------------------------------------------------------------#
class BaseOffenException (BaseException): ...
def nop (*args,**kwargs): ...

#-WRITER_INTERFACE------------------------------------------------------------#
class Functions (object):
    ''' advanced class with lots of double underscore functions and even a decorator (oooh)
        Added functions have to have the story object as their first argument.
        >>> 
        # add function under its own __name__
        >>> @this.function
        ... def function (): ...
        >>> this += function
        # add function under alias
        >>> this['alias'] = function
        >>> this.alias = function
        # get function
        >>> this.alias
        >>> this['function']
    '''
    def function (this,f):
        @functools.wraps (f)
        def decorated ():
            return f (this.story)
        vars (this)[decorated.__name__] = decorated
        return decorated

    def __init__ (this,story):
        vars (this)['story'] = story

    def __setattr__ (this,name,fun):
        if isinstance (fun,types.FunctionType):
            vars (this)[name] = functools.partial (fun,this.story)
        else:
            raise BaseOffenException ('Boo! This is no fun(ction):' + fun)

    def __setitem__ (this,name,fun):
        setattr (this,name,fun)

    def __iadd__ (this,fun):
        if isinstance (fun,types.FunctionType):
            setattr (this,fun.__name__,fun)
            return this
        else:
            raise BaseOffenException ('Boo! This is no fun(ction):' + fun)

    def __getitem__ (this,name):
        return getattr (this,name)

class Button (object):
    ''' Has a function and a label.
        >>> this.set ('label')                  # set label
        >>> this.set (function)                 # set function
        >>> this.set ('label',function)         # set both
        >>> this.set (( function,'label' ))     # set both; [Reihenfolge]'s not fixed
        >>> this.set ('label1','label2')        # set label to 'label2'; last one wins
        >>> this ()                             # call function
        >>> this.clear ()                       # clear; reset values
    '''
    function = nop
    label = ''

    def __init__ (this,tab,name):
        this.tab = tab
        this.name = name

    def set (this,*values):
        for value in values:
            if isinstance (value,Button):
                this.function,this.label = value.function,value.label
            elif isinstance (value,types.FunctionType):
                this.function = value
            elif isinstance (value,str):
                this.label = value
                this.tab.button_updates.add (this.name)
            elif hasattr (value,'__iter__'):
                # The has to be after str, because str is an iterable in python 3
                this.set (*value)
            else:
                logger.log ('Invalid input for Button:',value,l=1)
                raise BaseOffenException ( )

    def __call__ (this,*args,**kwargs):
        return this.function (*args,**kwargs)

    def clear (this): this.set (nop,'')

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

    def __init__ (this,tab):
        this.tab = tab
        this.keys = set ()

    def register_keys (this,*keys):
        for key in keys:
            if key.startswith ('K_'):
                this.keys.add (key)
                setattr (this,key,Button (this.tab,key))
            else:
                this.register_keys ('K_' + key)
        this.tab.story.game.register_button_keys (this.tab.name,keys)

    def __getitem__ (this,k):
        if k.startswith ('K_'):
            if k not in this.keys:
                raise KeyError ('No button with key %s registered.' % k)
            return getattr (this,k)
        else:
            return this['K_' + k]

    def __setitem__ (this,k,v):
        if k.startswith ('K_'):
            if k not in this.keys:
                raise KeyError ('No button %s registered.' % k)
            this[k].set (v)
            this.tab.button_updates.add (k)
        else:
            this['K_' + k] = v

    def clear (this):
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

    def __init__ (this,tab):
        this.tab = tab
        this.paragraphs = { }

    def clear (this):
        this.tab.paragraph_updates.update (this.keys ())
        this.paragraphs = { }

    def add (this,*strings):
        for string in strings:
            t = str (time.time ())
            this.paragraphs[t] = str (string)
            this.tab.paragraph_updates.add (t)

    def __getitem__ (this,k):
        return this.paragraphs[k]
    def keys (this):
        return this.paragraphs.keys ()
    def values (this):
        return this.paragraphs.values ()
    def items (this):
        return this.paragraphs.items ()

class Tab (object):
    ''' data container '''

    def __init__ (this,story,name):
        this.story = story
        this.name = name
        this.buttons = Buttons (this)
        this.paragraphs = Paragraphs (this)
        this.button_updates = set ()
        this.paragraph_updates = set ()

class Story (object):
    ''' main object and writer interface

    quick access to important instance members and their class:
        T: current tab                  Tab
        B: buttons of current tab       Buttons
        P: paragraphs of current tab    Paragraphs
        F: functions                    Functions
        V: variables                    dict
    '''
    keep_running = True
    active_tab = None

    def stop (this):
        this.keep_running = False

    def new_tab (this,name):
        if name not in this.tabs.keys ():
            this.game.register_tab (name)
            this.tabs[name] = Tab (this,name)
            this.tabs[name].buttons.register_keys (*gameconfig['buttonpanel_keysyms'])
        else:
            logger.log ('Story already has a tab:',tab,'Not creating new one.',l=2)

    def __init__ (this):
        this.game = Main (this)
        this.F = this.functions = Functions (this)
        this.V = this.vars = { }
        this.tabs = { }
        this.start = nop

        # A Tab, that holds all the buttons not in the buttonpanel. It has no paragraphs.
        this.game.register_tab ('menu')
        this.menu = Tab (this,'menu')
        this.menu.buttons.register_keys (*gameconfig['menubar_keysyms'])

        this.new_tab ('system')

    def run (this,init_json=None):
        if init_json is not None:
            this.vars.update (json.loads (init_json))
        this.game.run ()

    def __set_tab (this,tab):
        if tab in this.tabs.keys ():
            this.active_tab = this.tabs[tab]
        else:
            raise BaseOffenException ('Not in names of registered tabs: ' + tab)
    T = property (lambda this: this.active_tab,__set_tab,None,'Get active tab or Set by its name.')

    @property
    def P (this):
        return this.active_tab.paragraphs
    @property
    def B (this):
        return this.active_tab.buttons


#-USER_INTERFACE--------------------------------------------------------------#
class Main (object):

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
                            #this.rerender_textbox = True
                            this.textbox_scroll += 10
                            if this.textbox_scroll > this.get_textbox_text_height (S.T) - this.textbox_rect.height:
                                this.textbox_scroll = this.get_textbox_text_height (S.T) - this.textbox_rect.height
                        elif e.button == 5:
                            #this.rerender_textbox = True
                            this.textbox_scroll -= 10
                            if this.textbox_scroll < 0:
                                this.textbox_scroll = 0

            if button_id is not None:
                try:
                    S.B[button_id].function ()
                except KeyError:
                    S.menu.buttons[button_id].function ()

            ### update
            #if S.T.button_updates:
            #    logger.log (S.T.button_updates,l=3)
            this.process_tab_updates (S.T)
            this.process_tab_updates (S.menu)

            ### draw
            # TODO visual scroll indicator
            this.screen.fill (( 0x33,0x33,0x33,0xff ))
            this.draw_buttons (S.menu)
            this.draw_tab (S.T)
            #this.screen.blit (this.textbox_surf,this.textbox_rect.topleft)
            if debug_areas:
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.textbox_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.buttonpanel_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.sidebar_rect,1)
                pygame.draw.rect (this.screen,( 0xee,0xee,0xee,0xff ),this.infobox_rect,1)

            pygame.display.flip ()
            pygame.time.delay (100)

    def draw_tab (this,tab):
        this.draw_buttons (tab)
        this.draw_textbox (tab)

    def draw_buttons (this,tab):
        for id,surf in this.button_label_surfs[tab.name].items ():
            if surf is not None:
                pygame.draw.rect (this.screen,( 0xff,0xff,0xff ),this.button_rects[id],1)
                this.screen.blit (surf,this.button_rects[id].move (
                        gameconfig['buttons_gap'],gameconfig['buttons_gap']))

    def draw_textbox (this,tab):
        #if this.rerender_textbox:
        _tb_rect = this.textbox_rect
        # area of textbox - margins
        bottom = _tb_rect.bottom - gameconfig['textbox_margin']
        top = _tb_rect.top + gameconfig['textbox_margin']
        # bottom of bottomest paragraph
        drawpos = bottom + this.textbox_scroll
        for i,paragraph in enumerate (reversed (sorted (this.paragraph_surfs[tab.name].items ()))):
            if drawpos <= top: break
            p_surf = paragraph[1]
            p_rect = p_surf.get_rect ()
            p_rect.topleft = ( _tb_rect.x + gameconfig['textbox_margin'],drawpos - p_rect.height )

            if _tb_rect.contains (p_rect):
                this.screen.blit (p_surf,p_rect)
            #if p_surf.get_rect ().top < this.textbox_rect.height:
            #    this.textbox_surf.blit (p_surf,( gameconfig['textbox_margin'],y - p_surf.get_rect ().height ))
            drawpos = drawpos - p_surf.get_rect ().height - gameconfig['textbox_gap']

    def get_textbox_text_height (this,tab):
        return sum ([ps.get_rect ().height for ps in this.paragraph_surfs[tab.name].values ()]) + gameconfig['textbox_gap'] * (len (this.paragraph_surfs) - 1)

    def process_tab_updates (this,tab):
        # update buttons and rerender their labels
        if tab.button_updates:
            for id_ in tab.button_updates:
                if tab.buttons[id_].label:
                    this.button_label_surfs[tab.name][id_] = this.font.render (tab.buttons[id_].label,1,( 0xff,0xff,0xff,0xff ))
                elif id_ in this.button_label_surfs[tab.name]:
                    del this.button_label_surfs[tab.name][id_]
            tab.button_updates.clear ()
        # update paragraphs in textbox
        if not tab.paragraphs:
            this.paragraph_surfs[tab.name] = { }
        elif tab.paragraph_updates:
            for i in tab.paragraph_updates:
                if i not in tab.paragraphs.keys ():
                    del this.paragraph_surfs[tab.name][i]
                else:
                    this.paragraph_surfs[tab.name][i] = this.render_paragraph (tab.paragraphs[i])
            tab.paragraph_updates.clear ()

    def register_tab (this,name):
        if name not in this.button_label_surfs.keys ():
            this.button_label_surfs[name] = {}
            this.paragraph_surfs[name] = {}

    def register_button_keys (this,name,keys):
        if name in this.button_label_surfs.keys ():
            this.button_label_surfs[name].update ({k:None for k in keys})
        else:
            logger.log ('Tab does not exist:',name,l=1)
            raise BaseOffenException ()

    def render_paragraph (this,paragraph):
        # render words
        word_surfs = [this.font.render (word,1,( 0xff,0xff,0xff,0xff )) for word in paragraph.split (' ')]

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
                lines[-1].fill (gameconfig['colour_background'])
            lines[-1].blit (word,( x,0 ))
            x += word.get_rect ().width + space_rect.width

        # make paragraph and blit lines into
        paragraph_surf = pygame.Surface (( maxwidth,len (lines) * space_rect.height ),this.screen.get_flags ())
        paragraph_surf.fill (gameconfig['colour_background'])
        for x in range (len (lines)):
            paragraph_surf.blit (lines[x],( 0,x * space_rect.height ))

        return paragraph_surf

    def __init__ (this,story):
        pygame.init ()
        this.story = story
        this.screen = pygame.display.set_mode (( gameconfig['screen_width'],gameconfig['screen_height'] ),pygame.SRCALPHA)
        this.screen_rect = this.screen.get_rect ()
        this.font = pygame.font.Font (gameconfig['fontname'],gameconfig['fontsize'])
        this.space_surf = this.font.render (' ',0,( 0,0,0 ))

        this.paragraph_surfs = { } # {tabname:{pid:surf}}
        this.button_label_surfs = { } # {tabname:{buttonkey:surf}}

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
        #this.menubar_key_binding = { }
        for i,key in enumerate (gameconfig['menubar_keysyms']):
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

