#!/bin/python
# game.py
import offen
''' A very simple example.
Bonus: How to change the number of buttons.
'''

# Example for changing the game config without extra game.json file:
# (remove """s to use)
import json
offen.gameconfig.update (json.loads ('''{
    "buttonpanel_ny": 1,
    "keyboard_layouts": {
        "qwerty": [ "1","2","3","4","5" ]
        }
    }'''))

S = offen.Story ()


@S.function
def explore (S):
    ...

@S.function
def path_0 (S):
    S.B.clear ()
    S.B.K_3.set (place_0,'back')
    S.V['foo'] += 1

@S.function
def path_1 (S):
    S.B.clear ()
    S.B.K_2.set (place_0,'back')
    S.V['foo'] -= 1

@S.function
def place_0 (S):
    S.B.K_2.set (path_0,'path oh')
    S.B.K_3.set (path_1,'path one')
    S.B.K_1.set (offen.nop,'asdf')
    S.P.add ('''Hello World!''')
    S.P.add (S.V['foo'])

@S.function
def custom_start (S):
    ''' example menu function '''
    S.new_paragraphs ('story')
    S.T = 'story'
    S.V['foo'] = 0
    place_0 ()

@S.function
def stop (S):
    S.stop ()

# change the start function
S.start = custom_start
S.M.K_ESCAPE.set (stop,'quit')

S.reset_vars ('''{
"story_version": "0.0.1_reallywhateveryoulike"
}''')

S.run ()


















'''
stuff for a potential undo addon
    def undo (this,times=1):
        if len (this.history) >= times:
            this.buttons = this.history[times-1]['buttons']
            this.paragraphs = this.history[times-1]['paragraphs']
            this.game_vars = this.history[times-1]['game_vars']
            del this.history[:times]
            this.update_everything = True

    def snapshot (this):
        this.history.insert (0,{
                'buttons': copy.copy (this.buttons),
                'paragraphs': copy.copy (this.paragraphs),
                'game_vars': copy.deepcoy (this.game_vars) })
        if len (this.history) > GameConfig.undo_scrollback:
            del this.history[-1]
        this.history = [ ]          # undo history
        '''
