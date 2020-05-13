import sys, os, time
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run
from common.gfxutil import AnimGroup, CEllipse, scale_point
from common.leap import getLeapInfo, getLeapFrame
from common.screen import ScreenManager, Screen
from common.buttons import SensorButton

from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.graphics import Rectangle, Line, Color
from kivy.graphics.instructions import InstructionGroup
from kivy.uix.label import Label

import threading
from kivy.clock import mainthread

import commands
from hand import Hand, kLeapRange
from picture import Picture
from graphics import Slider, Overlay, StickerBar, IconBar
import speech


transparency_threshold = .95
speech_deltas = {
    'slider': 0.1,
    'zoom': 0.07,
}

DARK_MODE = True
ENABLE_INSTRUCTIONS = True
filepath = 'images/test_image.jpg'

class PhotoEditor(Screen) :
    def __init__(self, sm, **kwargs):
        super(PhotoEditor, self).__init__(**kwargs)

        # start speech recognition thread
        threading.Thread(target=speech.speech_main, args=(self,)).start()

        self.sm = sm

        # initialize image object
        self.picture = Picture(filepath)
        self.canvas.add(self.picture)

        # create slider group
        self.slider_group = AnimGroup()
        self.canvas.add(self.slider_group)

        # initialize slider
        self.slider = Slider(1.0, 0, 4)
        self.slider_line = Line(points=[0.98*Window.width, 0.02*Window.height, 0.98*Window.width, 0.98*Window.height], width=10)
        self.slider_group.add(self.slider_line)
        dim_size = min(0.03*Window.width, 0.03*Window.height)
        self.canvas.add(Color(rgb=(136/255, 195/255, 0)))
        self.slider_knob = CEllipse(cpos=(0.98*Window.width, 0.02*Window.height), csize=(dim_size, dim_size))
        self.slider_group.add(self.slider_knob)

        # create overlay (4 rectangles within overlay class to mimic crop frame)
        self.overlay = Overlay(0,0,0,0, self.picture.rectangle.size, self.picture.rectangle.pos)
        self.canvas.add(self.overlay)

        # current modification self.mode; possible options are:
        # -  None: no self.mode selected
        # - 'brightness' : change brightness using slider
        # - 'contrast' : change contrast using slider
        # - 'zoom' : makes photo bigger / smaller
        # - 'crop' : change size of photo
        self.modes = ['save', 'redo', 'undo', 'sticker', 'pixelate', 'invert', 'grayscale', 'transparent', 'saturation', 'sharpness', 'brightness', 'contrast', 'rotate', 'zoom', 'crop']
        self.slider_modes = ['brightness', 'contrast', 'saturation', 'sharpness']
        self.mode = None
        self.mode_instructions = { # we only have instructions for modes that you enter, modes that are applied as soon as the mode's voice command is said are omitted
                                    'crop' : '[font=./fonts/Cairo-Bold]Crop Instructions: [/font][font=./fonts/Cairo-Regular] Use one or two hands;  Start with hand(s) outside of the image and move your hand\ntowards the screen until the cursor(s) turns green.  Then, move your hands left/right/up/down in toward the picture\nuntil you are happy with the crop.  Finally, pull your hand(s) away from the screen until the cursor(s) turn yellow.[/font]',
                                    'zoom' : '[font=./fonts/Cairo-Bold]Zoom Instructions: [/font][font=./fonts/Cairo-Regular] Move two hands towards the screen until both cursors turns green, then move\nthem horizontally/vertically towards or away from each other to zoom out or zoom in.  When you are satified,\npull both hands away from the screen until the cursors turn yellow.\n\nTo zoom using your voice, say "in" to zoom in, and "out" to zoom out.[/font]',
                                    'rotate' : '[font=./fonts/Cairo-Bold]Rotate Instructions: [/font][font=./fonts/Cairo-Regular] Move one hand towards the screen until the cursor turns green, then rotate your hand as if you were\nturning a knob so that your fingers face left/right.  The picture will rotate 90º in the direction of your fingers.\n\nTo rotate the picture using your voice, say "rotate" and the picture will rotate 90º counterclockwise.[/font]',
                                    'contrast' : '[font=./fonts/Cairo-Bold]Contrast Instructions: [/font][font=./fonts/Cairo-Regular] Move one hand towards the screen until the cursor turns green, then move your hand up/down to\nincrease/decrease the contrast.  When you are satified, pull your hand away from the screen until the cursor turns yellow.\n\nTo change the contrast using your voice, say "increase" (or a synonym) to increase the contrast, and "decrease" (or a\nsynonym) to decrease the contrast.[/font]',
                                    'brightness' : '[font=./fonts/Cairo-Bold]Brightness Instructions: [/font][font=./fonts/Cairo-Regular]  Move one hand towards the screen until the cursor turns green, then move your hand up/down to\nincrease/decrease the brightness.  When you are satified, pull your hand away from the screen until the cursor turns yellow.\n\nTo change the brightness using your voice, say "increase" (or a synonym) to increase the brightness, and "decrease" (or a\nsynonym)to decrease the brightness.[/font]',
                                    'sharpness' : '[font=./fonts/Cairo-Bold]Sharpness Instructions: [/font][font=./fonts/Cairo-Regular]  Move one hand towards the screen until the cursor turns green, then move your hand up/down to\nincrease/decrease the sharpness.  When you are satified, pull your hand away from the screen until the cursor turns yellow.\n\nTo change the sharpness using your voice, say "increase" (or a synonym) to increase the sharpness, and "decrease" (or a\nsynonym)to decrease the sharpness.[/font]',
                                    'saturation' : '[font=./fonts/Cairo-Bold]Saturation Instructions: [/font][font=./fonts/Cairo-Regular]  Move one hand towards the screen until the cursor turns green, then move your hand up/down to\nincrease/decrease the saturation.  When you are satified, pull your hand away from the screen until the cursor turns yellow.\n\nTo change the saturation using your voice, say "increase" (or a synonym) to increase the saturation, and "decrease" (or a\nsynonym)to decrease the saturation.[/font]',
                                    'pixelate' : '[font=./fonts/Cairo-Bold]Pixelate Instructions: [/font][font=./fonts/Cairo-Regular] To increase the pixelation of the image by voice, say "increase" (or a synonym).\nTo return the picture to its original state, say "undo." [/font]',
                                    'sticker' : '[font=./fonts/Cairo-Bold]Sticker Instructions: [/font][font=./fonts/Cairo-Regular] View the names of the stickers on the bottom of the screen by hovering over them. Then, hover\nover the part of the image where you want to place the sticker and say the name of the sticker you want to apply.[/font]',
                                    'transparent' : '[font=./fonts/Cairo-Bold]Transparent Instructions: [/font][font=./fonts/Cairo-Regular] Hover over the area you wish to make transparent and say "apply".  You can also modify\nthe transparency threshold in settings.  To get to the settings page, hover over the gear in the top right corner.[/font]',
                                 }
        self.mode_instructions_label = Label(halign='center', markup=True)
        self.add_widget(self.mode_instructions_label)

        # add icon bar on left_hand side
        self.icon_label = Label()
        self.icon_bar = IconBar(self.modes, self.icon_label)
        self.canvas.add(self.icon_bar)
        self.add_widget(self.icon_label)

        # sticker bar
        self.sticker_label = Label()
        self.sticker_bar = StickerBar(self.sticker_label)
        self.add_widget(self.sticker_label)

        # settings button
        self.settings_button = SensorButton(size=(Window.width/15, Window.width/15), pos=(0.97*Window.width-Window.width/15, 0.98*Window.height-Window.width/15), mode='hover', texture=CoreImage('icons/settings.png').texture)
        self.canvas.add(self.settings_button)

        # menu button
        self.menu_button = SensorButton(size=(Window.width/15, Window.width/15), pos=(0.96*Window.width-2*Window.width/15, 0.98*Window.height-Window.width/15), mode='hover', texture=CoreImage('icons/menu.png').texture)
        self.canvas.add(self.menu_button)

        self.switch_to_timer = None

        # Hand objects that represent and show palm positions
        self.hands = [Hand(1), Hand(2)]
        for h in self.hands:
            self.canvas.add(h)


    def on_enter(self):
        print(self.sm.recent_screen)
        if self.sm.recent_screen == 'home':
            if self.picture in self.canvas.children:
                self.canvas.remove(self.picture)
                self.picture = Picture(filepath)
                self.canvas.add(Color(1,1,1,1))
                self.canvas.add(self.picture)

            self.canvas.remove(self.overlay)
            self.canvas.add(self.overlay)

        self.settings_button.on_update()
        self.menu_button.on_update()

        # reset icon bar
        self.canvas.remove(self.icon_bar)
        self.icon_bar = IconBar(self.modes, self.icon_label)
        self.canvas.add(self.icon_bar)
        # reset sticker bar
        if self.sticker_bar in self.canvas.children:
            self.canvas.remove(self.sticker_bar)
            self.sticker_bar = StickerBar(self.sticker_label)
            self.canvas.add(self.sticker_bar)
        else:
            self.sticker_bar = StickerBar(self.sticker_label)

        for h in self.hands:
            self.canvas.remove(h)
            self.canvas.add(h)

        self.on_layout((Window.width, Window.height))

    def on_update(self):

        if DARK_MODE:
            self.sticker_label.color = (1,1,1,1)
            self.icon_label.color = (1,1,1,1)
            self.mode_instructions_label.color = (1,1,1,1)
        else:
            self.sticker_label.color = (0,0,0,1)
            self.icon_label.color = (0,0,0,1)
            self.mode_instructions_label.color = (0,0,0,1)

        # update instructions for the mode if applicable
        if ENABLE_INSTRUCTIONS and self.mode in self.mode_instructions.keys():
            self.mode_instructions_label.text = self.mode_instructions[self.mode]
        else:
            self.mode_instructions_label.text = ''

        screen_hands = list(filter(lambda h: not h.id == -1, self.hands))

        # icon menu bar hover
        for hand in screen_hands:
            hovered_icon = self.icon_bar.identify_icon(hand.pos[0]*Window.width, hand.pos[1]*Window.height)
            if not hovered_icon == None:
                self.icon_bar.show_label(hovered_icon)
            else:
                self.icon_label.text = ''

        # sticker menu bar hover
        if self.sticker_bar in self.canvas.children:
            for hand in screen_hands:
                hovered_sticker = self.sticker_bar.identify_sticker(hand.pos[0]*Window.width, hand.pos[1]*Window.height)
                if not hovered_sticker == None:
                    self.sticker_bar.show_label(hovered_sticker)
                else:
                    self.sticker_label.text = ''



        active_hands = list(filter(lambda h: h.active, self.hands))

        # update icon bar to show current mode
        if not self.mode == None:
            self.icon_bar.change_mode(self.modes.index(self.mode))

        ######################################
        ##              SLIDER              ##
        ######################################

        self.update_slider(active_hands=active_hands)

        ######################################
        ##       SETTINGS/MENU BUTTON       ##
        ######################################
        if screen_hands:
            norm_pt = scale_point(screen_hands[0].leap_hand.palm_pos, kLeapRange)
            screen_xy = screen_hands[0].hand.to_screen_xy(norm_pt)
            self.settings_button.set_screen_pos(screen_xy, norm_pt[2])
            self.menu_button.set_screen_pos(screen_xy, norm_pt[2])

            if self.settings_button.is_on and self.switch_to_timer == None:
                self.switch_to_timer = time.time()
                self.switch_to('settings')

            if self.menu_button.is_on and self.switch_to_timer == None:
                self.switch_to_timer = time.time()
                self.switch_to('home')

        ######################################
        ##               CROP               ##
        ######################################

        # one handed
        if self.mode == 'crop' and len(active_hands) == 1:
            # get crop zone (top, right, left, bottom)
            image_pos = self.picture.rectangle.pos
            image_size = self.picture.rectangle.size
            hand_pos = active_hands[0].pos

            # get magnitude of crop
            crop_amount = active_hands[0].pos - active_hands[0].recent_pos

            # if hand is directly to the left of the image:
            if hand_pos[0]*Window.width < image_pos[0] and image_pos[1] < hand_pos[1]*Window.height < image_pos[1] + image_size[1]:
                self.overlay.change_left_delta(crop_amount[0]*Window.width)

            # if hand is directly to the right of the image:
            if image_pos[0] + image_size[0] < hand_pos[0]*Window.width and image_pos[1] < hand_pos[1]*Window.height < image_pos[1] + image_size[1]:
                self.overlay.change_right_delta(-crop_amount[0]*Window.width)

            # if hand is directly below the image:
            if hand_pos[1]*Window.height < image_pos[1] and image_pos[0] < hand_pos[0]*Window.width < image_pos[0] + image_size[0]:
                self.overlay.change_bottom_delta(crop_amount[1]*Window.height)

            # if hand is directly above the image:
            if image_pos[1] + image_size[1] < hand_pos[1]*Window.height and image_pos[0] < hand_pos[0]*Window.width < image_pos[0] + image_size[0]:
                self.overlay.change_top_delta(-crop_amount[1]*Window.height)

            # if hand is in top left
            if hand_pos[0]*Window.width < image_pos[0] and image_pos[1] + image_size[1] < hand_pos[1]*Window.height:
                self.overlay.change_left_delta(crop_amount[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount[1]*Window.height)

            # if hand is in top right
            if image_pos[0] + image_size[0] < hand_pos[0]*Window.width and image_pos[1] + image_size[1] < hand_pos[1]*Window.height:
                self.overlay.change_right_delta(-crop_amount[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount[1]*Window.height)

            # if hand is in bottom left
            if hand_pos[0]*Window.width < image_pos[0] and hand_pos[1]*Window.height < image_pos[1]:
                self.overlay.change_left_delta(crop_amount[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount[1]*Window.height)

            # if hand is in bottom right
            if image_pos[0] + image_size[0] < hand_pos[0]*Window.width and hand_pos[1]*Window.height < image_pos[1]:
                self.overlay.change_right_delta(-crop_amount[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount[1]*Window.height)

        # two handed
        if self.mode == 'crop' and len(active_hands) == 2:
            # get crop zone (top, right, left, bottom)
            image_pos = self.picture.rectangle.pos
            image_size = self.picture.rectangle.size
            hand_pos_A = active_hands[0].pos
            hand_pos_B = active_hands[1].pos

            # get magnitude of crop
            crop_amount_A = active_hands[0].pos - active_hands[0].recent_pos
            crop_amount_B = active_hands[1].pos - active_hands[1].recent_pos

            # hand A in top left
            if hand_pos_A[0] < 0.5 and hand_pos_A[1] > 0.5:
                self.overlay.change_left_delta(crop_amount_A[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount_A[1]*Window.height)
            # hand B in top left
            elif hand_pos_B[0] < 0.5 and hand_pos_B[1] > 0.5:
                self.overlay.change_left_delta(crop_amount_B[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount_B[1]*Window.height)

            # hand A in top right
            if hand_pos_A[0] > 0.5 and hand_pos_A[1] > 0.5:
                self.overlay.change_right_delta(-crop_amount_A[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount_A[1]*Window.height)
            # hand B in top right
            elif hand_pos_B[0] > 0.5 and hand_pos_B[1] > 0.5:
                self.overlay.change_right_delta(-crop_amount_B[0]*Window.width)
                self.overlay.change_top_delta(-crop_amount_B[1]*Window.height)

            # hand A in bottom left
            if hand_pos_A[0] < 0.5 and hand_pos_A[1] < 0.5:
                self.overlay.change_left_delta(crop_amount_A[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount_A[1]*Window.height)
            # hand B in bottom left
            elif hand_pos_B[0] < 0.5 and hand_pos_B[1] < 0.5:
                self.overlay.change_left_delta(crop_amount_B[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount_B[1]*Window.height)

            # hand A in bottom right
            if hand_pos_A[0] > 0.5 and hand_pos_A[1] < 0.5:
                self.overlay.change_right_delta(-crop_amount_A[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount_A[1]*Window.height)
            # hand B in bottom right
            elif hand_pos_B[0] > 0.5 and hand_pos_B[1] < 0.5:
                self.overlay.change_right_delta(-crop_amount_B[0]*Window.width)
                self.overlay.change_bottom_delta(crop_amount_B[1]*Window.height)

        ######################################
        ##              ROTATE              ##
        ######################################
        if self.mode == 'rotate' and len(active_hands) == 1:
            if all([state == None for state in active_hands[0].recent_turn_states]) and active_hands[0].turn_state == 'right':
                self.picture.change_rotation(angle=90, update_dims=True)
                self.picture.on_update()
                self.picture.update()
            elif all([state == None for state in active_hands[0].recent_turn_states]) and active_hands[0].turn_state == 'left':
                self.picture.change_rotation(angle=-90, update_dims=True)
                self.picture.on_update()
                self.picture.update()

        ######################################
        ##               ZOOM               ##
        ######################################

        self.update_on_zoom(active_hands=active_hands)

        ######################################
        ##           HAND OBJECTS           ##
        ######################################
        # update each hand
        for h in self.hands:
            h.on_update()

        # eliminate rapid screen switching bug
        if self.switch_to_timer and time.time() - self.switch_to_timer > 2:
            self.switch_to_timer = None



    def update_slider(self, active_hands=[], keyword=None):
        # update slider value if in slider self.mode and 1 hand is engaged (i.e. z < 0.6)
        if (self.mode in self.slider_modes) and \
            (len(active_hands) == 1 or keyword in commands.slider_commands):
            # add green slider knob
            self.slider_group.remove_all()
            self.slider_group.add(self.slider_line)
            self.slider_group.add(Color(rgb=(136/255, 195/255, 0)))
            self.slider_group.add(self.slider_knob)

            if len(active_hands) == 1:
                delta = active_hands[0].pos - active_hands[0].recent_pos
                delta_y = delta[1]
            elif keyword in commands.slider_commands:
                if keyword == 'up':
                    delta_y = speech_deltas['slider']
                elif keyword == 'down':
                    delta_y = -speech_deltas['slider']
            percent = self.slider.change_value_delta(delta_y)
            self.slider_knob.cpos=(self.slider_knob.cpos[0], Window.height*(0.96*percent + 0.02))

            # update brightness or contrast based on slider value
            if self.mode == 'pixelate':
                x = self.slider.value
                new_min = 0
                new_max = 1
                old_min = 1
                old_max = 4
                normalized_x = ((new_max - new_min)/(old_max - old_min))*(x - old_max) + new_max
                print(x)
                print(normalized_x)
                # self.picture.pixelate(self.slider.value)
                self.picture.pixelate(normalized_x)
            # if self.mode == 'rotate':
            #     self.picture.change_rotation(angle=90*(self.slider.value-1), update_dims=False)
            elif self.mode in self.slider_modes:
                # works for change_contrast, change_brightness, change_sharpness, change_saturation
                eval('self.picture.change_' + self.mode + '(' + str(self.slider.value) + ')')
            self.picture.on_update()

        elif (self.mode in self.slider_modes):
            # add yellow slider knob
            self.slider_group.remove_all()
            self.slider_group.add(self.slider_line)
            self.slider_group.add(Color(rgb=(.94, .76, 0)))
            self.slider_group.add(self.slider_knob)
        else:
            self.slider_group.remove_all()


    def update_on_zoom(self, active_hands=[], keyword=None):
        if self.mode == 'zoom':
            # two handed
            if len(active_hands) == 2:
                hand_pos_A = active_hands[0].pos
                hand_pos_B = active_hands[1].pos

                # get magnitude of zoom
                zoom_amount_A = active_hands[0].pos - active_hands[0].recent_pos
                zoom_amount_B = active_hands[1].pos - active_hands[1].recent_pos

                delta_w = 0
                delta_h = 0

                # hand A in top left
                if hand_pos_A[0] < 0.5 and hand_pos_A[1] > 0.5:
                    delta_w += -zoom_amount_A[0]*Window.width
                    delta_h += zoom_amount_A[1]*Window.height
                # hand B in top left
                elif hand_pos_B[0] < 0.5 and hand_pos_B[1] > 0.5:
                    delta_w += -zoom_amount_B[0]*Window.width
                    delta_h += zoom_amount_B[1]*Window.height

                # hand A in top right
                if hand_pos_A[0] > 0.5 and hand_pos_A[1] > 0.5:
                    delta_w += zoom_amount_A[0]*Window.width
                    delta_h += zoom_amount_A[1]*Window.height
                # hand B in top right
                elif hand_pos_B[0] > 0.5 and hand_pos_B[1] > 0.5:
                    delta_w += zoom_amount_B[0]*Window.width
                    delta_h += zoom_amount_B[1]*Window.height

                # hand A in bottom left
                if hand_pos_A[0] < 0.5 and hand_pos_A[1] < 0.5:
                    delta_w += -zoom_amount_A[0]*Window.width
                    delta_h += -zoom_amount_A[1]*Window.height
                # hand B in bottom left
                elif hand_pos_B[0] < 0.5 and hand_pos_B[1] < 0.5:
                    delta_w += -zoom_amount_B[0]*Window.width
                    delta_h += -zoom_amount_B[1]*Window.height

                # hand A in bottom right
                if hand_pos_A[0] > 0.5 and hand_pos_A[1] < 0.5:
                    delta_w += zoom_amount_A[0]*Window.width
                    delta_h += -zoom_amount_A[1]*Window.height
                # hand B in bottom right
                elif hand_pos_B[0] > 0.5 and hand_pos_B[1] < 0.5:
                    delta_w += zoom_amount_B[0]*Window.width
                    delta_h += -zoom_amount_B[1]*Window.height

                self.picture.zoom_delta(delta_w=delta_w, delta_h=delta_h)
            elif keyword:
                if keyword == 'in':
                    delta_w = speech_deltas['zoom']
                    delta_h = speech_deltas['zoom']
                elif keyword == 'out':
                    delta_w = -speech_deltas['zoom']
                    delta_h = -speech_deltas['zoom']
                delta_w *= Window.width
                delta_h *= Window.height
                self.picture.zoom_delta(delta_w=delta_w, delta_h=delta_h)


    def on_layout(self, win_size):
        for h in self.hands:
            h.on_layout(win_size)

        self.picture.on_layout(win_size)
        self.overlay.on_layout(self.picture.rectangle.size, self.picture.rectangle.pos)

        # update slider positioning
        percent = self.slider.get_slider_percent()
        self.slider_knob.cpos=(0.98*Window.width, Window.height*(0.96*percent + 0.02))
        dim_size = min(0.03*Window.width, 0.03*Window.height)
        self.slider_knob.csize=(dim_size, dim_size)
        self.slider_line.points=[0.98*Window.width, 0.02*Window.height, 0.98*Window.width, 0.98*Window.height]

        # update side mode icon bar
        self.icon_bar.on_layout()

        # update sticker bar
        self.sticker_bar.on_layout()

        # update settings and menu buttons
        self.settings_button.update_pos_and_size(pos=(0.97*Window.width-Window.width/15, 0.98*Window.height-Window.width/15), size=(Window.width/15, Window.width/15))
        self.menu_button.update_pos_and_size(pos=(0.96*Window.width-2*Window.width/15, 0.98*Window.height-Window.width/15), size=(Window.width/15, Window.width/15))

        # update instructions label
        self.mode_instructions_label.center_x = Window.width/2
        self.mode_instructions_label.center_y = 19*Window.height/20
        self.mode_instructions_label.font_size = str(Window.width//170) + 'sp'


    # maps key presses to changing editing self.mode
    # to be replaced by speech commands in V2
    @mainthread
    def on_speech_recognized(self, keyword):
        print("keyword: ", keyword)
        old_mode = self.mode

        # change mode if keyword relates to a mode
        if keyword in self.modes:
            self.mode = keyword

        if keyword in commands.terminator:
            sys.exit()

        # TODO: if you call undo just once it sometimes doesn't work the first time
        if self.mode == 'undo':
            self.picture.undo()
            self.picture.on_update()
            self.overlay.update_pos_and_size(self.picture.rectangle.size, self.picture.rectangle.pos)

        elif self.mode == 'redo':
            self.picture.redo()
            self.picture.on_update()
            self.overlay.update_pos_and_size(self.picture.rectangle.size, self.picture.rectangle.pos)

        elif self.mode in self.slider_modes and keyword in commands.slider_commands:
            self.update_slider(keyword=keyword)

        elif self.mode == 'zoom' and keyword in commands.zoom_commands:
            self.update_on_zoom(keyword=keyword)

        # if switching from one self.mode to a different self.mode, update picture history
        elif not old_mode == self.mode:

            if old_mode == 'zoom':
                self.overlay.update_pos_and_size(self.picture.rectangle.size, self.picture.rectangle.pos)

            # update slider to default value to start fresh next time
            if old_mode in self.slider_modes:
                percent = self.slider.change_value(1.0)
                self.slider_knob.cpos=(self.slider_knob.cpos[0], Window.height*(0.96*percent + 0.02))


            # commit crop and remove crop overlay
            if old_mode == 'crop':
                # actually crop self.picture.temp
                self.picture.crop(l=self.overlay.left_width, t=self.overlay.top_height, r=self.overlay.right_width, b=self.overlay.bottom_height)

                # reset crop overlay width and height params to 0,0,0,0
                self.overlay.reset()
                self.picture.on_update() # ensure cropping change appears
                self.overlay.update_pos_and_size(self.picture.rectangle.size, self.picture.rectangle.pos)

            # update image history with changes
            self.picture.update() # TODO: (fix) currently this updates history every time a self.mode is changed, even if the photo is not modified while in that self.mode

        # if current mode is sticker, add a sticker based on its name
        if self.mode == 'sticker':
            if self.sticker_bar not in self.canvas.children:
                self.canvas.add(self.sticker_bar)

            if keyword in self.sticker_bar.sticker_names:
                screen_hands = list(filter(lambda h: not h.id == -1, self.hands))
                # if hand on screen and within picture area
                if len(screen_hands) == 1 and self.picture.rectangle.pos[0] < screen_hands[0].pos[0]*Window.width < self.picture.rectangle.pos[0] + self.picture.rectangle.size[0] and self.picture.rectangle.pos[1] < screen_hands[0].pos[1]*Window.height < self.picture.rectangle.pos[1] + self.picture.rectangle.size[1]:
                    # get picture position (ignoring screen position of the image)
                    x = screen_hands[0].pos[0]*Window.width - self.picture.rectangle.pos[0]
                    y = self.picture.rectangle.size[1] - (screen_hands[0].pos[1]*Window.height - self.picture.rectangle.pos[1])
                    self.picture.add_sticker('./stickers/' + keyword + '.png', x, y)
                    self.picture.on_update()
                    self.picture.update()
        else:
            self.canvas.remove(self.sticker_bar)

        if self.mode == 'transparent':
            if keyword == "apply":
                screen_hands = list(filter(lambda h: not h.id == -1, self.hands))
                if len(screen_hands) == 1 and self.picture.rectangle.pos[0] < screen_hands[0].pos[0]*Window.width < self.picture.rectangle.pos[0] + self.picture.rectangle.size[0] and self.picture.rectangle.pos[1] < screen_hands[0].pos[1]*Window.height < self.picture.rectangle.pos[1] + self.picture.rectangle.size[1]:
                    x = screen_hands[0].pos[0]*Window.width - self.picture.rectangle.pos[0]
                    y = screen_hands[0].pos[1]*Window.height - self.picture.rectangle.pos[1]
                    mask = self.picture.magic_wand(x, y, transparency_threshold)
                    self.picture.make_transparent(mask)
                    self.picture.on_update()
                    self.picture.update()

        if self.mode == 'rotate':
            if old_mode == "rotate":
                self.picture.change_rotation(angle=90, update_dims=True)
                self.picture.on_update()
                self.picture.update()

        elif self.mode == 'invert':
            self.picture.invert()
            self.picture.on_update()
            self.picture.update()

        elif self.mode == 'grayscale':
            self.picture.grayscale()
            self.picture.on_update()
            self.picture.update()

        # if current mode is save, save the image
        if self.mode == 'save':
            self.picture.save_image()
