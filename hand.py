import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.gfxutil import Cursor3D, scale_point
from common.leap import getLeapInfo, getLeapFrame

from kivy.core.window import Window
from kivy.graphics import Color
from kivy.graphics.instructions import InstructionGroup

import photo_editor
# for use with scale_point to convert millimeters to unit-coordinates
# x, y, and z ranges to define a 3D bounding box
kLeapRange   = ( (-150, 200), (100, 400), (-200, 200) )

# set up size / location of 3DCursor objects
kMargin = 0
kCursorAreaSize = Window.width, Window.height
kCursorAreaPos = kMargin, kMargin

WINDOW_SIZE = 10
TURN_STATE_THRESHOLD = 5

def update_window_size(new_size):
    global WINDOW_SIZE
    if new_size <= 0:
        new_size = 1
    if new_size == 6:
        new_size = 5
    if new_size <= 100:
        WINDOW_SIZE = new_size

def get_window_size():
    global WINDOW_SIZE
    return WINDOW_SIZE

# single hand
class Hand(InstructionGroup):
    def __init__(self, num):
        super(Hand, self).__init__()
        self.color = (.94, .76, 0)
        self.leap_hand = None
        self.hand = Cursor3D(kCursorAreaSize, kCursorAreaPos, self.color)
        self.num = num
        self.active = False
        self.pos_window = []
        self.recent_pos = (0.5, 0.5, 0)
        self.pos = (0.5, 0.5, 0)
        self.id = -1
        self.recent_turn_states = [None]*TURN_STATE_THRESHOLD
        self.turn_state = None
        self.add(self.hand)

    def on_update(self):
        leap_frame = getLeapFrame()
        self.leap_hand = leap_frame.hands[self.num % 2]
        self.id = leap_frame.hands[self.num % 2].id

        # update turn state
        self.recent_turn_states = self.recent_turn_states[1:] + [self.turn_state]
        # if all but one finger are to the left of the palm position:
        if len(list(filter(lambda x: x==True, [finger[0] < self.leap_hand.palm_pos[0]-20 for finger in self.leap_hand.fingers]))) >= 4:
            self.turn_state = 'left'
        elif len(list(filter(lambda x: x==True, [finger[0] > self.leap_hand.palm_pos[0]+10 for finger in self.leap_hand.fingers]))) >= 3:
            self.turn_state = 'right'
        elif sum([finger[0] for finger in self.leap_hand.fingers]) / len(self.leap_hand.fingers) + 10 > self.leap_hand.palm_pos[0]:
            self.turn_state = None

        norm_pt = scale_point(self.leap_hand.palm_pos, kLeapRange)

        # update current and recent position values
        self.pos_window.append(norm_pt)
        if len(self.pos_window) == WINDOW_SIZE:
            self.pos_window = self.pos_window[1:]
        if len(self.pos_window) > WINDOW_SIZE and len(self.pos_window) > 2:
            self.pos_window = self.pos_window[2:]

        self.recent_pos = self.pos
        self.pos = sum(self.pos_window) / len(self.pos_window)

        self.hand.set_pos(self.pos)


        # hide hand if leap does not sense it
        # Change color to green if hand is active (i.e. z < 0.5) and yellow otherwise
        if self.id == -1:
            if photo_editor.DARK_MODE:
                self.hand.set_color((0, 0, 0))
            else:
                self.hand.set_color((1, 1, 1))
        elif (norm_pt[2] < 0.6):
            self.hand.set_color((136/255, 195/255, 0))
            self.active = True
        else:
            self.hand.set_color((.94, .76, 0))
            self.active = False

        return 'id: {} x: {:.2f} y: {:.2f} z: {:.2f}\n'.format(self.leap_hand.id, *norm_pt)

    def on_layout(self, win_size):
        # set boundary to update bounding box
        kCursorAreaSize = win_size
        self.hand.set_boundary(kCursorAreaSize, kCursorAreaPos)
