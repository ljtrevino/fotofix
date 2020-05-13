import glob
import sys, os, math, time
sys.path.insert(0, os.path.abspath('..'))

from common.screen import Screen
from common.buttons import SensorButtonPhoto
from common.gfxutil import scale_point

from kivy.core.window import Window
from kivy.core.image import Image as CoreImage
from kivy.uix.label import Label

from hand import Hand, kLeapRange
import photo_editor

class Homepage(Screen) :
    def __init__(self, **kwargs):
        super(Homepage, self).__init__(**kwargs)
        self.switch_to_timer = None

        self.title = Label(text='Fotofix', font_name='./fonts/Cairo-Regular', color=(63/255, 127/255, 191/255, 1))
        self.add_widget(self.title)

        self.buttons = []
        photo_paths = [f for f in (glob.glob("./images/*.jpg") + glob.glob("./images/*.jpeg") + glob.glob("./images/*.png"))]
        for i, path in enumerate(photo_paths):
            button = SensorButtonPhoto(mode='hover', texture=CoreImage(path).texture, path=path)
            self.canvas.add(button)
            self.buttons.append(button)

        # Hand objects that represent and show palm positions
        self.hands = [Hand(1), Hand(2)]
        for h in self.hands:
            self.canvas.add(h)

        self.on_layout((Window.width, Window.height))

    def on_enter(self):
        for button in self.buttons:
            self.canvas.remove(button)

        self.buttons = []
        photo_paths = [f for f in (glob.glob("./images/*.jpg") + glob.glob("./images/*.jpeg") + glob.glob("./images/*.png"))]
        for i, path in enumerate(photo_paths):
            button = SensorButtonPhoto(mode='hover', texture=CoreImage(path).texture, path=path)
            self.canvas.add(button)
            self.buttons.append(button)

        self.on_layout((Window.width, Window.height))

    def on_layout(self, winsize):
        self.title.center_x = Window.width/2
        self.title.center_y = 9*Window.height/10
        self.title.font_size = str(Window.width//30) + 'sp'

        photo_paths = [f for f in (glob.glob("./images/*.jpg") + glob.glob("./images/*.jpeg") + glob.glob("./images/*.png"))]
        dim = self.getDimension(len(photo_paths)-1)
        dim_size = min(Window.width, Window.height*8/10)
        for i in range(len(self.buttons)):
            size=(1/dim*dim_size*0.9, 1/dim*dim_size*0.9)
            pos=((i%(2*dim))/dim*dim_size + 1/dim*dim_size*0.05, Window.height*4/5 - (math.ceil((i+1)/(2*dim))/dim*dim_size) + 1/dim*dim_size*0.05)
            self.buttons[i].update_pos_and_size(pos, size)

        for h in self.hands:
            h.on_layout((Window.width, Window.height))


    def on_update(self):
        screen_hands = list(filter(lambda h: not h.id == -1, self.hands))

        if screen_hands:
            norm_pt = scale_point(screen_hands[0].leap_hand.palm_pos, kLeapRange)
            screen_xy = screen_hands[0].hand.to_screen_xy(norm_pt)
            for b in self.buttons:
                b.set_screen_pos(screen_xy, norm_pt[2])
        else:
            for b in self.buttons:
                b.inside_rect.size = (b.size2[0], 0)


        # update each hand
        for h in self.hands:
            h.on_update()

        chosen_image = None
        for b in self.buttons:
            if b.is_on and self.switch_to_timer == None:
                self.switch_to_timer = time.time()
                photo_editor.filepath = b.path
                self.switch_to('photo_editor')


        # eliminate rapid screen switching bug
        if self.switch_to_timer and time.time() - self.switch_to_timer > 2:
            self.switch_to_timer = None


    def getDimension(self, N):
        for i in range(0, 5):
            if N < i*(2*i):
                return i
