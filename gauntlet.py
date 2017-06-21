#!/bin/python
# gauntlet.py
''' Offen extension for creating text adventures '''

#_INITIALISATION______________________________________________________________#
import random

# __offen init boilerplate_____ #
import offen
import basics
S = basics.Story ()

#_BASE_GAME_VARS______________________________________________________________#
base_json = '''{
"story_version": "0.0.0",
"story_name": null
}'''
new_game_json = '''{
}'''

#_THINGS______________________________________________________________________#
@S.object
class SizeLever (basics.Thing):
    # has a button, that has to be pushed before it can be moved, it only pops back out when the lever is completely pulled in either direction
    # pulling too far makes the player lose the ground under their feet and desperately hang on to the lever pulling it down even more
    # the lock button makes it impossible for small people to push it up
    _label = 'lever'
    strings = {
            'desc0': 'A steel grey lever that looks a bit like a T. It sits in a vertical slit {0}in the wall.',
            'desc1': 'There is a button on the side of the handle.',

            'first touch': 'You place your hand on the handle of the lever. It refuses to budge but there seems to be a button.',
            'lever stuck': 'Try as you might the lever refuses to budge.',
            'broken': 'It\'s broken and You killed it.',

            'first button': 'You push the button. You let go but the button stays in.',
            'press button': 'You push the button. Like before, it stays inside.',
            'pop button': 'When the lever reaches the end of its leeway the button pops out again.',
            'button stuck': 'The button is already pushed in.',

            'lowest setting': 'The lever seems to be at its limit.',
            'highest setting': 'The lever seems to be at its limit.',
            }

    button_out = True
    cur_position = 0
    max_position = 10
    button_found = False
    button_examined = False
    broken = False

    @property
    def description (this):
        s = this.strings['desc0'].format ('at heads height ')
        if this.button_found:
            s += ' ' + this.strings['desc1']
        return s

    def init (this):
        this.buttons['q'].set (this.back)
        this.buttons['w'].set (this.pull_up)
        this.buttons['s'].set (this.pull_down)
        this.buttons['f'].set (this.destroy)
        this.buttons['e'].set (this.examine)

    def destroy (this):
        this.broken = True
        this.back ()

    def back (this):
        this.S.B = 'story'

    def examine (this):
        this.S.tell (this.description)
        this.examined_once = True

    def call (this):
        if not this.broken:
            this.S.B = id (this)
            this.examine ()
            # TODO check size of player and show the levers' button tab
        else:
            this.tell ('broken')

    def push_button (this):
        if not this.button_examined:
            this.tell ('first button')
            this.button_examined = True
        elif not this.button_out:
            this.tell ('button stuck')
        else:
            this.tell ('press button')
        this.button_out = False

    def pop_button (this):
        this.tell ('pop button')
        this.button_out = True

    def pull_down (this):
        if not this.button_found:
            this.tell ('first touch')
            this.button_found = True
            this.buttons['a'].set (this.push_button)
        elif this.button_out:
            this.tell ('lever stuck')
        elif this.lowest:
            this.tell ('lowest setting')
        else:
            this.cur_position += 1
            this.S.tell (str (this.cur_position))
            # XXX say something
            if this.lowest:
                this.pop_button ()
        # TODO update buttons

    def pull_up (this):
        if not this.button_found:
            this.tell ('first touch')
            this.button_found = True
            this.buttons['a'].set (this.push_button)
        elif this.button_out:
            this.tell ('lever stuck')
        elif this.highest:
            this.tell ('highest setting')
        else:
            this.cur_position -= 1
            this.S.tell (str (this.cur_position))
            # XXX say something
            if this.highest:
                this.pop_button ()
        # TODO update buttons

    lowest = property (lambda this: this.cur_position == this.max_position)
    highest = property (lambda this: not this.cur_position)


#_ROOMS_______________________________________________________________________#
@S.object
class RoomGenerator (basics.Thing):
    _label = 'roomgen'
    room_spawn_chance = 40

    # __get new random room________ #
    def new_room (this,d):
        if this.S.V['open_ends'] == 1:
            return Corridor ()
        elif random.randint (1,100) < this.room_spawn_chance:
            pass

    # __aliases for the directions_ #
    def new_room_N (this): return this.new_room ('n')
    def new_room_E (this): return this.new_room ('e')
    def new_room_S (this): return this.new_room ('s')
    def new_room_W (this): return this.new_room ('w')

# __the rooms__________________ #
@S.object
class PrisonCell (basics.Room):
    _label = 'cell'

    def __init__ (this,S):
        super ().__init__ (S)
        this.go_N.set (S.T['roomgen'].new_room_N,'explore north')
        S.V['open_ends'] = 1

@S.object
class Corridor (basics.Room):

    def __init__ (this,S):
        super ().__init__ (S)

#_CHARACTERS__________________________________________________________________#
@S.object
class Player (basics.Character):
    ...

#_FUNCTIONS___________________________________________________________________#
@S.function
def real_start (S):
    S.B.clear ()
    # random encounter -- oh hey it's the lever!
    #S.V['lever'] = SizeLever ()
    S.B = PrisonCell ()

@S.function
def new_game (S):
    S.reset_vars (base_json)
    S.update_vars (new_game_json)
    RoomGenerator ()
    S.P = 'story'
    S.P.clear ()
    S.B = 'story'
    S.B.clear ()

    t = Corridor ()
    t2 = PrisonCell ()

    real_start ()

@S.function
def custom_start (S):
    ''' example menu function '''
    S.new_paragraphs ('story')
    S.P = 'story'
    S.new_buttons ('story')
    S.B = 'story'
    S.B['1'].set (new_game,'Start new game')
    S.M['ESCAPE'].set (stop,'quit')

@S.function
def stop (S):
    S.stop ()

# change the start function
S.start = custom_start

if __name__ == "__main__":
    # offen run boilerplate
    S.run ()
