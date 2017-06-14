#!/bin/python
# game.py
import offen
S = offen.Story ()
# /init boilerplate

# Example for changing the game config without extra game.json file:
# (remove """s to use)
"""
import json
offen.gameconfig.update (json.loads ('''{
    "buttons_gap": 5
    }'''))
"""

@S.F.function
def explore (S):
    ...

@S.F.function
def path_0 (S):
    S.B.clear ()
    S.B.K_w.set (place_0,'back')
    S.V['foo'] += 1

@S.F.function
def path_1 (S):
    S.B.clear ()
    S.B.K_q.set (place_0,'back')
    S.V['foo'] -= 1

@S.F.function
def place_0 (S):
    S.B.K_q.set (path_0,'path oh')
    S.B.K_w.set (path_1,'path one')
    S.B.K_1.set (offen.nop,'asdf')
    S.P.add ('''Hello World!''')
    S.P.add (S.V['foo'])

@S.F.function
def custom_start (S):
    ''' example menu function '''
    S.new_tab ('story')
    S.T = 'story'
    S.V['foo'] = 0
    place_0 ()

@S.F.function
def stop (S):
    S.stop ()

# change the start function
S.start = custom_start
S.menu.buttons.K_ESCAPE.set (stop,'quit')

# run boilerplate
S.run ('''{
"story_version": "0.0.1_reallywhateveryoulike"
}''')


















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
