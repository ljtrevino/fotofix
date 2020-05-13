import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run
from common.leap import getLeapInfo, getLeapFrame

from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image as CoreImage

from common.gfxutil import AnimGroup
import photo_editor

class Slider(InstructionGroup):
    def __init__(self, initial_val, min_val, max_val):
        super(Slider, self).__init__()
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val

    def get_slider_percent(self):
        return self.value/self.max_val

    # changes slider alue to new_value
    def change_value(self, new_value):
        self.value = new_value
        # adjust based on min and max values
        self.value = min(max(self.value, self.min_val), self.max_val)
        return self.value/self.max_val

    # increases or decreases slider value by delta
    # delta must be between 0 and 1
    def change_value_delta(self, delta):
        self.value += delta*(self.max_val-self.min_val)
        # adjust based on min and max values
        self.value = min(max(self.value, self.min_val), self.max_val)
        return self.value/self.max_val

class StickerBar(InstructionGroup):
    def __init__(self, label):
        super(StickerBar, self).__init__()
        self.label = label
        size_dim = min(Window.width/8, Window.height/8)
        self.left_circle = Ellipse(pos=(Window.width/8-size_dim/2, Window.height*0.02), size=(size_dim, size_dim), angle_start=180, angle_end=360)
        self.right_circle = Ellipse(pos=(Window.width*7/8-size_dim/2, Window.height*0.02), size=(size_dim, size_dim), angle_start=0, angle_end=180)
        self.rect = Rectangle(pos=(Window.width*1/8, Window.height*0.02), size=(Window.width*3/4, size_dim))
        if photo_editor.DARK_MODE:
            self.add(Color(rgba=(1,1,1,0.2)))
        else:
            self.add(Color(rgba=(0,0,0,0.2)))
        self.add(self.left_circle)
        self.add(self.right_circle)
        self.add(self.rect)
        self.add(Color(rgba=(1,1,1,1)))

        self.sticker_names = ['smile', 'heart', 'star', 'flower', 'balloons', 'cool']
        self.stickers = []

        for i in range(len(self.sticker_names)):
            size_dim = min(0.95*Window.width/8, 0.95*Window.height/8)
            sticker = Rectangle(texture=CoreImage('stickers/' + self.sticker_names[i] + '.png').texture)
            self.stickers.append(sticker)
            self.add(sticker)

        self.on_layout()

    def identify_sticker(self, x, y):
        size_dim = min(0.9*Window.width/8, 0.9*Window.height/8)

        # if y-position is reasonable
        if Window.height*0.02 + 0.05*Window.height/8 < y < Window.height*0.02 + 0.05*Window.height/8 + size_dim:
            # check for sticker x-position match
            for i in range(len(self.stickers)):
                if self.stickers[i].pos[0] < x < self.stickers[i].pos[0] + self.stickers[i].size[0]:
                    return self.sticker_names[i]
        return None

    def show_label(self, sticker):
        i = self.sticker_names.index(sticker)
        self.label.center_x = self.stickers[i].pos[0] + self.stickers[i].size[0] / 2
        self.label.center_y = max(0, self.stickers[i].pos[1] - self.label.texture_size[1] * 0.5)
        self.label.text = sticker

    def on_layout(self):
        size_dim = min(Window.width/8, Window.height/8)
        self.left_circle.pos=(Window.width/8-size_dim/2, Window.height*0.02)
        self.left_circle.size=(size_dim, size_dim)
        self.right_circle.pos=(Window.width*7/8-size_dim/2, Window.height*0.02)
        self.right_circle.size=(size_dim, size_dim)
        self.rect.pos=(Window.width*1/8, Window.height*0.02)
        self.rect.size=(Window.width*3/4, size_dim)

        for i in range(len(self.sticker_names)):
            size_dim = min(0.9*Window.width/8, 0.9*Window.height/8)
            # TODO fix layout so that stickers are more centered
            self.stickers[i].pos = (Window.width/8 + (Window.width*3/4)*i/(len(self.sticker_names)), Window.height*0.02 + 0.05*Window.height/8)
            self.stickers[i].size = (size_dim, size_dim)


class IconBar(InstructionGroup):
    def __init__(self, modes, label):
        super(IconBar, self).__init__()
        self.modes = modes
        self.label = label
        self.icons = []

        self.icon_group = AnimGroup()
        self.add(self.icon_group)

        self.generate_icons()

    def generate_icons(self):
        if photo_editor.DARK_MODE:
            self.icon_group.add(Color(rgb=(1, 1, 1)))
        else:
            self.icon_group.add(Color(rgb=(0, 0, 0)))
        for i in range(len(self.modes)):
            icon = Rectangle(pos=(0.02*Window.width, Window.height*(0.1 + 0.8*i/len(self.modes))), size=(0.8*Window.height/len(self.modes), 0.8*Window.height/len(self.modes)), texture=CoreImage('icons/' + self.modes[i] + '.png').texture)
            self.icons.append(icon)
            self.icon_group.add(icon)

    def change_mode(self, mode_index):
        self.icon_group.remove_all()
        for i in range(len(self.icons)):
            if photo_editor.DARK_MODE:
                self.icon_group.add(Color(rgb=(1, 1, 1)))
            else:
                self.icon_group.add(Color(rgb=(0, 0, 0)))
            if i == mode_index:
                # change color before adding
                self.icon_group.add(Color(rgb=(136/255, 195/255, 0)))
            self.icon_group.add(self.icons[i])

    def on_layout(self):
        for i in range(len(self.modes)):
            self.icons[i].pos=(0.02*Window.width, Window.height*(0.1 + 0.8*i/len(self.modes)))
            self.icons[i].size=(0.8*Window.height/len(self.modes), 0.8*Window.height/len(self.modes))

    # returns mode of icon at screen position (x, y)
    def identify_icon(self, x, y):
        # if x-position is reasonable
        if 0.02*Window.width < x < 0.02*Window.width + 0.5*Window.height/len(self.modes):
            # check for icon y-position match
            for i in range(len(self.modes)):
                if self.icons[i].pos[1] < y < self.icons[i].pos[1] + self.icons[i].size[1]:
                    return self.modes[i]
        return None

    def show_label(self, icon):
        i = self.modes.index(icon)
        self.label.text = icon
        self.label.center_x = self.icons[i].pos[0] + self.icons[i].size[0] + self.label.texture_size[0] * 0.6
        self.label.center_y = self.icons[i].pos[1] + self.icons[i].size[1] / 2


class Overlay(InstructionGroup):
    # TODO add code to ensure overlay widths and heights can never go negative
    def __init__(self, left_width, right_width, top_height, bottom_height, image_size, image_pos):
        super(Overlay, self).__init__()
        # create 4 rectangles with opacity of 0.7
        self.color = Color(rgba=(0, 0, 0, 0.7))
        self.add(self.color)

        self.left_rect = Rectangle(pos=image_pos, size=(left_width, image_size[1]), segments = 4)
        self.add(self.left_rect)

        self.right_rect = Rectangle(pos=(image_pos[0]+image_size[0]-right_width, image_pos[1]), size=(right_width, image_size[1]), segments = 4)
        self.add(self.right_rect)

        self.top_rect = Rectangle(pos=(image_pos[0], image_pos[1]+image_size[1]-top_height), size=(image_size[0], top_height), segments = 4)
        self.add(self.top_rect)

        self.bottom_rect = Rectangle(pos=image_pos, size=(image_size[0], bottom_height), segments = 4)
        self.add(self.bottom_rect)

        self.left_width = left_width
        self.right_width = right_width
        self.top_height = top_height
        self.bottom_height = bottom_height
        self.image_pos = image_pos
        self.image_size = image_size

    # code to change image position and size parameters when actual picture size is changed in the picture class
    def update_pos_and_size(self, image_size, image_pos):
        self.image_pos = image_pos
        self.image_size = image_size

        self.left_rect.pos = image_pos
        self.left_rect.size = (self.left_width, image_size[1])

        self.right_rect.pos = (image_pos[0]+image_size[0]-self.right_width, image_pos[1])
        self.right_rect.size = (self.right_width, image_size[1])

        self.top_rect.pos = (image_pos[0], image_pos[1]+image_size[1]-self.top_height)
        self.top_rect.size = (image_size[0], self.top_height)

        self.bottom_rect.pos = image_pos
        self.bottom_rect.size = (image_size[0], self.bottom_height)

    # adjust overlay values so that widths stay in range [0, image_size[0]//2]
    # and heights stay in range [0, image_size[1]//2]
    def normalize_delta(self, right_delta=0, left_delta=0, top_delta=0, bottom_delta=0):
        if not right_delta == 0:
            if self.right_width + right_delta > self.image_size[0]//2:
                right_delta = self.image_size[0]//2 - self.right_width
            elif self.right_width + right_delta < 0:
                right_delta = -self.right_width
            return right_delta
        if not left_delta == 0:
            if self.left_width + left_delta > self.image_size[0]//2:
                left_delta = self.image_size[0]//2 - self.left_width
            elif self.left_width + left_delta < 0:
                left_delta = -self.left_width
            return left_delta
        if not top_delta == 0:
            if self.top_height + top_delta > self.image_size[1]//2:
                top_delta = self.image_size[1]//2 - self.top_height
            elif self.top_height + top_delta < 0:
                top_delta = -self.top_height
            return top_delta
        if not bottom_delta == 0:
            if self.bottom_height + bottom_delta > self.image_size[1]//2:
                bottom_delta = self.image_size[1]//2 - self.bottom_height
            elif self.bottom_height + bottom_delta < 0:
                bottom_delta = -self.bottom_height
            return bottom_delta

    def change_left_delta(self, left_delta):
        left_delta = left_delta if left_delta == 0 else self.normalize_delta(left_delta=left_delta)
        self.left_rect.size = (self.left_rect.size[0] + left_delta, self.left_rect.size[1])
        self.left_width += left_delta

    def change_right_delta(self, right_delta):
        right_delta = right_delta if right_delta == 0 else self.normalize_delta(right_delta=right_delta)
        self.right_rect.size = (self.right_rect.size[0] + right_delta, self.right_rect.size[1])
        self.right_rect.pos = (self.right_rect.pos[0] - right_delta, self.right_rect.pos[1])
        self.right_width += right_delta

    def change_top_delta(self, top_delta):
        top_delta = top_delta if top_delta == 0 else self.normalize_delta(top_delta=top_delta)
        self.top_rect.size = (self.top_rect.size[0], self.top_rect.size[1] + top_delta)
        self.top_rect.pos = (self.top_rect.pos[0], self.top_rect.pos[1] - top_delta)
        self.top_height += top_delta

    def change_bottom_delta(self, bottom_delta):
        bottom_delta = bottom_delta if bottom_delta == 0 else self.normalize_delta(bottom_delta=bottom_delta)
        self.bottom_rect.size = (self.bottom_rect.size[0], self.bottom_rect.size[1] + bottom_delta)
        self.bottom_height += bottom_delta


# Currently unused functions, but may come in handy later --- keep for now
    # def change_left(self, new_left_width):
    #     left_delta = left_delta if left_delta == 0 else self.normalize_delta(left_delta=left_delta)
    #     self.left_rect.size = (new_left_width, self.left_rect.size[1])
    #     self.left_width = new_left_width
    #
    # def change_right(self, new_right_width):
    #     right_delta = right_delta if right_delta == 0 else self.normalize_delta(right_delta=right_delta)
    #     self.right_rect.size = (new_right_width, self.right_rect.size[1])
    #     self.right_rect.pos = (self.image_pos[0] + self.image_size[0] - new_right_width, self.right_rect.pos[1])
    #     self.right_width = new_right_width
    #
    # def change_top(self, new_top_height):
    #     top_delta = top_delta if top_delta == 0 else self.normalize_delta(top_delta=top_delta)
    #     self.top_rect.size = (self.top_rect.size[0], new_top_height)
    #     self.top_rect.pos = (self.top_rect.pos[0], self.image_pos[1] + self.image_size[1] - new_top_height)
    #     self.top_height = new_top_height
    #
    # def change_bottom(self, new_bottom_height):
    #     bottom_delta = bottom_delta if bottom_delta == 0 else self.normalize_delta(bottom_delta=bottom_delta)
    #     self.bottom_rect.size = (self.top_rect.size[0], new_bottom_height)
    #     self.bottom_height = new_bottom_height

    def reset(self):
        self.change_left_delta(-self.left_width)
        self.change_right_delta(-self.right_width)
        self.change_top_delta(-self.top_height)
        self.change_bottom_delta(-self.bottom_height)

    def on_layout(self, image_size, image_pos):
        self.left_rect.pos=image_pos
        self.left_rect.size=(self.left_width, image_size[1])

        self.right_rect.pos = (image_pos[0]+image_size[0]-self.right_width, image_pos[1])
        self.right_rect.size=(self.right_width, image_size[1])

        self.top_rect.pos=(image_pos[0], image_pos[1]+image_size[1]-self.top_height)
        self.top_rect.size=(image_size[0], self.top_height)

        self.bottom_rect.pos=image_pos
        self.bottom_rect.size=(image_size[0], self.bottom_height)
