import sys, os, time
sys.path.insert(0, os.path.abspath('..'))
from common.screen import ScreenManager, Screen
from common.buttons import SensorButton
from common.gfxutil import scale_point

from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.label import Label

from hand import Hand, kLeapRange, update_window_size, get_window_size
import photo_editor

class Settings(Screen) :
    def __init__(self, **kwargs):
        super(Settings, self).__init__(**kwargs)

        self.title = Label(text='Settings', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.title)

        self.photo_editor_button = SensorButton(mode='hover', texture=CoreImage('icons/image.png').texture)
        self.canvas.add(self.photo_editor_button)

        self.dark_mode_label = Label(text='Dark Mode', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.dark_mode_label)
        self.dark_mode_button = SensorButton(mode='hover', texture=CoreImage('icons/dark_mode.png').texture)
        self.light_mode_button = SensorButton(mode='hover', texture=CoreImage('icons/light_mode.png').texture)
        self.canvas.add(self.dark_mode_button)
        self.canvas.add(self.light_mode_button)
        self.dm_value_label = Label(text=("dark" if photo_editor.DARK_MODE else "light"), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.dm_value_label)

        self.instructions_label = Label(text='Instructions Visible', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.instructions_label)
        self.instructions_on_button = SensorButton(mode='hover', texture=CoreImage('icons/instructions_on.png').texture)
        self.instructions_off_button = SensorButton(mode='hover', texture=CoreImage('icons/instructions_off.png').texture)
        self.canvas.add(self.instructions_on_button)
        self.canvas.add(self.instructions_off_button)
        self.i_value_label = Label(text=("on" if photo_editor.ENABLE_INSTRUCTIONS else "off"), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.i_value_label)

        self.gesture_smooth_label = Label(text='Gesture Smoothness', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.gesture_smooth_label)
        self.gs_down_button = SensorButton(mode='hover', texture=CoreImage('icons/down.png').texture)
        self.gs_up_button = SensorButton(mode='hover', texture=CoreImage('icons/up.png').texture)
        self.canvas.add(self.gs_down_button)
        self.canvas.add(self.gs_up_button)
        self.gs_value_label = Label(text=str(get_window_size()), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.gs_value_label)
        self.gs_timer = None

        self.voice_delta_label = Label(text='Voice Slider Delta', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.voice_delta_label)
        self.vd_down_button = SensorButton(mode='hover', texture=CoreImage('icons/down.png').texture)
        self.vd_up_button = SensorButton(mode='hover', texture=CoreImage('icons/up.png').texture)
        self.canvas.add(self.vd_down_button)
        self.canvas.add(self.vd_up_button)
        self.vd_value_label = Label(text=str(get_window_size()), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.vd_value_label)
        self.vd_timer = None

        self.voice_delta_label2 = Label(text='Voice Zoom Delta', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.voice_delta_label2)
        self.vd_down_button2 = SensorButton(mode='hover', texture=CoreImage('icons/down.png').texture)
        self.vd_up_button2 = SensorButton(mode='hover', texture=CoreImage('icons/up.png').texture)
        self.canvas.add(self.vd_down_button2)
        self.canvas.add(self.vd_up_button2)
        self.vd_value_label2 = Label(text=str(get_window_size()), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.vd_value_label2)
        self.vd_timer2 = None

        self.transparency_threshold_label = Label(text='Transparency Threshold', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.transparency_threshold_label)
        self.tt_down_button = SensorButton(mode='hover', texture=CoreImage('icons/down.png').texture)
        self.tt_up_button = SensorButton(mode='hover', texture=CoreImage('icons/up.png').texture)
        self.canvas.add(self.tt_down_button)
        self.canvas.add(self.tt_up_button)
        self.tt_value_label = Label(text=str(get_window_size()), font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.tt_value_label)
        self.tt_timer = None

        # Hand objects that represent and show palm positions
        self.hands = [Hand(1), Hand(2)]
        for h in self.hands:
            self.canvas.add(h)

    def set_dark_mode(self, is_dark):
        photo_editor.DARK_MODE = is_dark
        if is_dark:
            Window.clearcolor = (0,0,0,1)
        else:
            Window.clearcolor = (0.9,0.9,0.9,1)

    def on_layout(self, winsize):
        # update title label
        self.title.center_x = Window.width/2
        self.title.center_y = 9*Window.height/10
        self.title.font_size = str(Window.width//30) + 'sp'
        self.switch_to_timer = None

        self.dark_mode_label.center_x = 3*Window.width/10
        self.dark_mode_label.center_y = 7*Window.height/10
        self.dark_mode_label.font_size = str(Window.width//60) + 'sp'
        self.dm_value_label.center_x = 11/16*Window.width
        self.dm_value_label.center_y = 7*Window.height/10
        self.dm_value_label.font_size = str(Window.width//60) + 'sp'
        self.dark_mode_button.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 7*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.light_mode_button.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 7*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.instructions_label.center_x = 3*Window.width/10
        self.instructions_label.center_y = 6*Window.height/10
        self.instructions_label.font_size = str(Window.width//60) + 'sp'
        self.i_value_label.center_x = 11/16*Window.width
        self.i_value_label.center_y = 6*Window.height/10
        self.i_value_label.font_size = str(Window.width//60) + 'sp'
        self.instructions_on_button.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 6*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.instructions_off_button.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 6*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.gesture_smooth_label.center_x = 3*Window.width/10
        self.gesture_smooth_label.center_y = 5*Window.height/10
        self.gesture_smooth_label.font_size = str(Window.width//60) + 'sp'
        self.gs_value_label.center_x = 11/16*Window.width
        self.gs_value_label.center_y = 5*Window.height/10
        self.gs_value_label.font_size = str(Window.width//60) + 'sp'
        self.gs_down_button.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 5*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.gs_up_button.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 5*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.voice_delta_label.center_x = 3*Window.width/10
        self.voice_delta_label.center_y = 4*Window.height/10
        self.voice_delta_label.font_size = str(Window.width//60) + 'sp'
        self.vd_value_label.center_x = 11/16*Window.width
        self.vd_value_label.center_y = 4*Window.height/10
        self.vd_value_label.font_size = str(Window.width//60) + 'sp'
        self.vd_down_button.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 4*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.vd_up_button.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 4*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.voice_delta_label2.center_x = 3*Window.width/10
        self.voice_delta_label2.center_y = 3*Window.height/10
        self.voice_delta_label2.font_size = str(Window.width//60) + 'sp'
        self.vd_value_label2.center_x = 11/16*Window.width
        self.vd_value_label2.center_y = 3*Window.height/10
        self.vd_value_label2.font_size = str(Window.width//60) + 'sp'
        self.vd_down_button2.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 3*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.vd_up_button2.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 3*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.transparency_threshold_label.center_x = 3*Window.width/10
        self.transparency_threshold_label.center_y = 2*Window.height/10
        self.transparency_threshold_label.font_size = str(Window.width//60) + 'sp'
        self.tt_value_label.center_x = 11/16*Window.width
        self.tt_value_label.center_y = 2*Window.height/10
        self.tt_value_label.font_size = str(Window.width//60) + 'sp'
        self.tt_down_button.update_pos_and_size(pos=(5/8*Window.width-Window.width/40, 2*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))
        self.tt_up_button.update_pos_and_size(pos=(6/8*Window.width-Window.width/40, 2*Window.height/10-Window.width/40), size=(Window.width/20, Window.width/20))

        self.photo_editor_button.update_pos_and_size(pos=(0.02*Window.width, 0.98*Window.height-Window.width/15), size=(Window.width/15, Window.width/15))


        for h in self.hands:
            h.on_layout((Window.width, Window.height))

    def on_update(self):

        self.dark_mode_button.on_update()
        self.light_mode_button.on_update()
        self.instructions_on_button.on_update()
        self.instructions_off_button.on_update()
        self.gs_down_button.on_update()
        self.gs_up_button.on_update()
        self.vd_down_button.on_update()
        self.vd_up_button.on_update()
        self.vd_down_button2.on_update()
        self.vd_up_button2.on_update()
        self.tt_down_button.on_update()
        self.tt_up_button.on_update()
        self.photo_editor_button.on_update()

        screen_hands = list(filter(lambda h: not h.id == -1, self.hands))

        if screen_hands:
            norm_pt = scale_point(screen_hands[0].leap_hand.palm_pos, kLeapRange)
            screen_xy = screen_hands[0].hand.to_screen_xy(norm_pt)
            self.photo_editor_button.set_screen_pos(screen_xy, norm_pt[2])
            self.dark_mode_button.set_screen_pos(screen_xy, norm_pt[2])
            self.light_mode_button.set_screen_pos(screen_xy, norm_pt[2])
            self.instructions_on_button.set_screen_pos(screen_xy, norm_pt[2])
            self.instructions_off_button.set_screen_pos(screen_xy, norm_pt[2])
            self.gs_down_button.set_screen_pos(screen_xy, norm_pt[2])
            self.gs_up_button.set_screen_pos(screen_xy, norm_pt[2])
            self.vd_down_button.set_screen_pos(screen_xy, norm_pt[2])
            self.vd_up_button.set_screen_pos(screen_xy, norm_pt[2])
            self.vd_down_button2.set_screen_pos(screen_xy, norm_pt[2])
            self.vd_up_button2.set_screen_pos(screen_xy, norm_pt[2])
            self.tt_down_button.set_screen_pos(screen_xy, norm_pt[2])
            self.tt_up_button.set_screen_pos(screen_xy, norm_pt[2])

            if self.photo_editor_button.is_on and self.switch_to_timer == None:
                self.switch_to_timer = time.time()
                self.switch_to('photo_editor')

            if self.dark_mode_button.is_on:
                self.set_dark_mode(True)
                self.dm_value_label.text = "dark"
            if self.light_mode_button.is_on:
                self.set_dark_mode(False)
                self.dm_value_label.text = "light"

            if self.instructions_on_button.is_on:
                photo_editor.ENABLE_INSTRUCTIONS = True
                self.i_value_label.text = "on"
            if self.instructions_off_button.is_on:
                photo_editor.ENABLE_INSTRUCTIONS = False
                self.i_value_label.text = "off"

            self.gs_value_label.text = str(get_window_size())
            if self.gs_down_button.is_on or self.gs_up_button.is_on:
                if self.gs_timer == None:
                    self.gs_timer = time.time()
                elif time.time() - self.gs_timer > 1:
                    self.gs_timer = None
                    multiplier = -1 if self.gs_down_button.is_on else 1
                    update_window_size(get_window_size() + multiplier*5)
            else:
                self.gs_timer =  None

            self.vd_value_label.text = str(photo_editor.speech_deltas["slider"])
            if self.vd_down_button.is_on or self.vd_up_button.is_on:
                if self.vd_timer == None:
                    self.vd_timer = time.time()
                elif time.time() - self.vd_timer > 1:
                    self.vd_timer = None
                    multiplier = -1 if self.vd_down_button.is_on else 1
                    if 0.12 >= round(photo_editor.speech_deltas["slider"] + multiplier*0.01, 2) >= 0.01:
                        photo_editor.speech_deltas["slider"] += multiplier*0.01
                        photo_editor.speech_deltas["slider"] = round(photo_editor.speech_deltas["slider"], 2)
            else:
                self.vd_timer =  None

            self.vd_value_label2.text = str(photo_editor.speech_deltas["zoom"])
            if self.vd_down_button2.is_on or self.vd_up_button2.is_on:
                if self.vd_timer2 == None:
                    self.vd_timer2 = time.time()
                elif time.time() - self.vd_timer2 > 1:
                    self.vd_timer2 = None
                    multiplier = -1 if self.vd_down_button2.is_on else 1
                    if 0.1 >= round(photo_editor.speech_deltas["zoom"] + multiplier*0.01, 2) >= 0.02:
                        photo_editor.speech_deltas["zoom"] += multiplier*0.01
                        photo_editor.speech_deltas["zoom"] = round(photo_editor.speech_deltas["zoom"], 2)
            else:
                self.vd_timer2 =  None

            self.tt_value_label.text = str(photo_editor.transparency_threshold)
            if self.tt_down_button.is_on or self.tt_up_button.is_on:
                if self.tt_timer == None:
                    self.tt_timer = time.time()
                elif time.time() - self.tt_timer > 1:
                    self.tt_timer = None
                    multiplier = -1 if self.tt_down_button.is_on else 1
                    if 1 >= photo_editor.transparency_threshold + multiplier*0.01 >= 0.01:
                        photo_editor.transparency_threshold += multiplier*0.05
                        photo_editor.transparency_threshold = round(photo_editor.transparency_threshold, 2)
            else:
                self.tt_timer =  None

        # update each hand
        for h in self.hands:
            h.on_update()

        # eliminate rapid screen switching bug
        if self.switch_to_timer and time.time() - self.switch_to_timer > 2:
            self.switch_to_timer = None
