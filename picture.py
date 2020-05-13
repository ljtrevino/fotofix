import sys, os
sys.path.insert(0, os.path.abspath('..'))

from kivy.core.window import Window
from kivy.graphics import Rectangle, Rotate, PushMatrix, PopMatrix
from kivy.graphics.instructions import InstructionGroup
from kivy.core.image import Image as CoreImage

from io import BytesIO
from PIL import Image, ImageEnhance, ImageOps
import numpy as np

# helper functions
def get_color(data, x, y, w):
    return data[get_index(x, y, w)]

def is_similar_color(a, b, threshold = .5):
    assert(threshold >= 0 and threshold <= 1)

    max_delta = (((255**2) * 3)**.5) * (1 - threshold)
    distance = (a[0] - b[0])**2 + (a[1] - b[1])**2 + (a[2] - b[2])**2
    distance = distance**.5
    return distance <= max_delta

def get_index(x, y, width):
    return y*width + x

# yields indexes for all pixels in the "megapixel"
# starting from x, y and having h height / w width
# imwidth is the total width
def pixels_from_square(x, y, h, w, imheight, imwidth):
    for j in range(x*h, min((x+1)*h, imheight)):
        for i in range(y*w, min((y+1)*w, imwidth)):
            yield j, i

class Picture(InstructionGroup):
    def __init__(self, filepath):
        super(Picture, self).__init__()

        im = Image.open(filepath).convert("RGBA")
        self.image = im.copy()
        self.temp = im.copy()
        self.filepath = filepath

        # Save states
        self.history = [(im, im.size[0], im.size[1])] # includes current state
        self.history_pos = 0

        # Size and graphics
        width, height = self.image.size
        pos=(Window.width - width)//2, (Window.height - height)//2
        size=(width, height)

        # allow rotation:
        self.add(PushMatrix())
        self.rotate = Rotate(angle = 0)
        self.add(self.rotate)

        # create rectangle to hold image
        self.rectangle = Rectangle(pos=pos, size=size)
        self.add(PopMatrix())
        self.on_update()
        self.add(self.rectangle)

    def update_filepath(self, new_filepath):
        im = Image.open(new_filepath).convert("RGBA")
        self.image = im.copy()
        self.temp = im.copy()
        self.filepath = new_filepath

    def zoom_delta(self, delta_w=0, delta_h=0):
        ratio = min(delta_w/self.rectangle.size[0], delta_h/self.rectangle.size[1])
        self.rectangle.size = (self.rectangle.size[0]*(1+ratio), self.rectangle.size[1]*(1+ratio))
        self.on_layout((Window.width, Window.height))

    def on_layout(self, win_size):
        # TODO: add code to resize image if it is bigger than Window.width or Window.height
        self.rectangle.pos = (win_size[0] - self.rectangle.size[0])//2, (win_size[1] - self.rectangle.size[1])//2

    def on_update(self):
        # convert PIL image to input for CoreImage
        data = BytesIO()
        self.temp.save(data, format='png')
        data.seek(0)

        # update image
        self.rectangle.texture = CoreImage(BytesIO(data.read()), ext='png').texture

    # saves the image
    def save_image(self, extra=""):
        path_without_extension = os.path.splitext(self.filepath)[0]
        new_path = path_without_extension + "_fotofix" + extra + ".png"
        self.image.save(new_path)

    # undo the change
    def undo(self):
        if self.history_pos > 0:
            self.history_pos -= 1
            assert self.history_pos >= 0

            image, width, height = self.history[self.history_pos]

            self.image = image
            self.temp = image

            # update size of rectangle
            self.rectangle.pos = (Window.width - width)//2, (Window.height - height)//2
            self.rectangle.size=(width, height)

        else:
            print("Can't undo anymore")

    # redo the change
    def redo(self):
        if self.history_pos < len(self.history)-1:
            self.history_pos += 1
            assert self.history_pos < len(self.history)

            image, width, height = self.history[self.history_pos]

            self.image = image
            self.temp = image

            # update size of rectangle
            self.rectangle.pos = (Window.width - width)//2, (Window.height - height)//2
            self.rectangle.size=(width, height)

        else:
            print("Can't redo anymore")

    # update the image and history
    def update(self):
        if self.history_pos < len(self.history)-1: # at old state
            # keep history up to current state
            self.history = self.history[:self.history_pos + 1]

        self.history.append((self.temp, self.rectangle.size[0], self.rectangle.size[1]))
        self.image = self.temp

        self.history_pos += 1
        print(len(self.history))
        assert self.history_pos < len(self.history)
        assert self.history_pos >= 0

    # display the image in the iamge viewer
    def show(self):
        self.temp.show()

    # change the brightness by factor
    # factor > 1: brighter
    # factor = 1: original
    # factor = 0: black
    def change_brightness(self, factor):
        assert factor >= 0
        enhancer = ImageEnhance.Brightness(self.image)
        result = enhancer.enhance(factor)
        self.temp = result

    # change the contrast by factor
    # factor > 1: more contrast
    # factor = 1: original
    # factor = 0: gray
    def change_contrast(self, factor):
        assert factor >= 0
        enhancer = ImageEnhance.Contrast(self.image)
        result = enhancer.enhance(factor)
        self.temp = result

    # crops the image by the specified amount in each direction
    def crop(self, l=0, t=0, r=0, b=0):
        view_width, view_height = self.rectangle.size
        width, height = self.image.size

        # adjust specificed amount based on actual image size (incase image has been zoomed in or out)
        right = r/view_width*width
        left = l/view_width*width
        top = t/view_height*height
        bottom = b/view_height*height

        # change borders
        right = width - right
        bottom = height - bottom
        borders = (left, top, right, bottom)

        # apply the crop
        result = self.image.crop(borders)
        self.temp = result

        # update size of rectangle
        w, h = (self.rectangle.size[0] - r - l, self.rectangle.size[1] - t - b)
        self.rectangle.pos = (Window.width - w)//2, (Window.height - h)//2
        self.rectangle.size=(w, h)

    # applies a sticker centered on (x, y) in the image
    # stickerfp is the filepath of the sticker
    def add_sticker(self, stickerfp, x, y):

        # convert x, y from rectangle coordinate (might be modified by zoom) to image coordinates
        view_width, view_height = self.rectangle.size
        width, height = self.image.size
        x = int(width * x/view_width)
        y = int(height * y/view_height)

        sticker = Image.open(stickerfp).convert("RGBA")
        w, h = sticker.size

        # paste uses top left corner, so we need to offset to place in the center
        new_x, new_y = x - (w//2), y - (h//2)
        assert(new_x >= 0)
        assert(new_y >= 0)

        location = (new_x, new_y)
        copy = self.temp.copy()
        copy.paste(sticker, location, sticker)
        self.temp = copy

    # selects all neighboring pixels with the same color as (x, y) with threshold
    # returns a mask array of 0s and 1s where 0 is an unselected pixel and 1 is selected
    # not done yet its complicated
    def magic_wand(self, x, y, threshold = .5):
        view_width, view_height = self.rectangle.size
        width, height = self.image.size
        x = int(width * x/view_width)
        y = int(height * y/view_height)

        img_data = self.temp.getdata()
        output = np.zeros(len(img_data)).tolist()

        w, h = self.temp.size
        selected_color = get_color(img_data, x, y, w)

        stack = [(x, x, y)] # rows to work through, list of [left bound, right bound, y]
        done = set() # finished rows

        # function to check if point already in bitmap
        def is_in_bitmap(xi, yi):
            return output[get_index(xi, yi, w)] == 1

        # function to get row segment given point and add to bitmap
        def get_row(xi, yi):
            curr_x = xi
            left, right = xi, xi # bounds of the color row
            color = get_color(img_data, curr_x, yi, w)

            # check left
            while curr_x >= 0:
                color = get_color(img_data, curr_x, yi, w)
                if is_similar_color(selected_color, color, threshold):
                    output[get_index(curr_x, yi, w)] = 1    # update the bitmap
                    left = curr_x                          # set new left bound
                    curr_x -= 1                             # try pixel to the left
                else:
                    break

            # reset iterating values
            curr_x = xi
            color = get_color(img_data, curr_x, yi, w)

            # check right
            while curr_x < w:
                color = get_color(img_data, curr_x, yi, w)
                if is_similar_color(selected_color, color, threshold):
                    output[get_index(curr_x, yi, w)] = 1    # update the bitmap
                    right = curr_x                          # set new right bound
                    curr_x += 1                             # try pixel to the right
                else:
                    break

            return (left, right, yi)

        # work through stack of rows to find all connected points
        while stack:
            # print(stack)
            row = stack.pop()
            if row in done:
                continue
            else:
                done.add(row)

            left, right, curr_y = row
            above = curr_y - 1
            below = curr_y + 1

            # check above and below for each point in row
            for x in range(left, right+1):
                # check above
                if (above >= 0
                    and is_similar_color(selected_color, get_color(img_data, x, above, w), threshold)
                    and not is_in_bitmap(x, above)):

                    new_row = get_row(x, above)
                    if new_row in done:
                        continue
                    else:
                        stack.append(new_row)

                # check below
                if (below < h
                    and is_similar_color(selected_color, get_color(img_data, x, below, w), threshold)
                    and not is_in_bitmap(x, below)):

                    new_row = get_row(x, below)
                    if new_row in done:
                        continue
                    else:
                        stack.append(new_row)

        return output

    # selects all similar colored pixels
    # returns a mask array of 0s and 1s where 0 is an unselected pixel and 1 is selected
    def select_similar_pixels(self, x, y, threshold = .5):
        # convert x, y from rectangle coordinate (might be modified by zoom) to image coordinates
        view_width, view_height = self.rectangle.size
        width, height = self.image.size
        x = int(width * x/view_width)
        y = int(height * y/view_height)

        img_data = self.temp.getdata()
        output = np.zeros(len(img_data)).tolist()

        w, __ = self.temp.size
        selected_color = get_color(img_data, x, y, w)

        for i in range(len(img_data)):
            color = img_data[i]
            if is_similar_color(color, selected_color, threshold):
                output[i] = 1

        return output

    # makes all pixels that are labelled 1 in mask transparent
    def make_transparent(self, mask):
        new_data = []
        img_data = self.temp.getdata()

        for i in range(len(mask)):
            if mask[i]:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(img_data[i])

        self.temp.putdata(new_data)

    # makes all pixels that are labelled 1 in mask bright red
    def highlight_pixel(self, mask):
        new_data = []
        img_data = self.temp.getdata()

        for i in range(len(mask)):
            if mask[i]:
                new_data.append((255, 0, 0, 255))
            else:
                new_data.append(img_data[i])

        self.temp.putdata(new_data)

    # change the saturation by factor
    # factor > 1: more saturation
    # factor = 1: original
    # factor = 0: black and white
    def change_saturation(self, factor):
        assert factor >= 0
        enhancer = ImageEnhance.Color(self.image)
        result = enhancer.enhance(factor)
        self.temp = result

    # change the sharpness by factor
    # factor = 2: sharpened
    # factor = 1: original
    # factor = 0: blurry
    def change_sharpness(self, factor):
        assert factor >= 0
        enhancer = ImageEnhance.Sharpness(self.image)
        result = enhancer.enhance(factor)
        self.temp = result

    # rotate the image by angle degrees
    # if update_dims, update image dimensions to fit rotated image
    # else image is cropped to original size
    def change_rotation(self, angle=90, update_dims=True):
        result = self.image.rotate(angle, expand=update_dims)
        # if not update_dims:
        #     print(angle)
        #     self.rotate.angle += angle
        #     self.rotate.angle %= 360
        # if update_dims and angle==90:
        new_width = self.rectangle.size[1]
        new_height = self.rectangle.size[0]
        self.rectangle.pos = (Window.width - new_width)//2, (Window.height - new_height)//2
        self.rectangle.size = (new_width, new_height)
        self.temp = result

    # Sets all the pixels in square given by coord x,y
    # and size w,h to the avg pixel color
    def make_pixel(self, x, y, h, w):
        width, height = self.image.size
        img_data = self.image.getdata()
        pixels = []

        # get all pixels
        for j, i in pixels_from_square(x, y, h, w, height, width):
            index = get_index(i, j, width)
            pixels.append(img_data[index])

        if len(pixels) == 0:
            # can't seem to find the reason why this happens,
            # but doing this doesn't affect the image...?
            return

        # get the average color
        avg_r, avg_g, avg_b = 0, 0, 0
        for r, g, b, _ in pixels:
            avg_r += r
            avg_g += g
            avg_b += b
        avg_r //= len(pixels)
        avg_g //= len(pixels)
        avg_b //= len(pixels)

        # set all pixels to that average color
        for j, i in pixels_from_square(x, y, h, w, height, width):
            index = get_index(i, j, width)
            alpha = img_data[index][3]
            self.temp.putpixel((i, j), (avg_r, avg_g, avg_b, alpha))

    # pixelates the image
    # factor = 1: image is one giant pixel (subject to aspect ratio)
    # factor = 0: image is normal
    def pixelate(self, factor):
        if factor == 0:
            self.temp = self.image

        width, height = self.image.size

        # scale factor between 0.3 and 0.7
        factor = factor * (0.7 - 0.3) + 0.3

        # math to work out the pixelation factor, feel free to make this prettier
        num_cols = int(max(round((1 - factor) * width), 1))
        square_w = round(width / num_cols)
        num_rows = int(max(round((1 - factor) * height), 1))
        square_h = round(height / num_rows)

        # padding in case not all pixels are covered by rounding
        if square_w * num_cols < width:
            num_cols += 1
        if square_h * num_rows < height:
            num_rows += 1

        # overwrite each square with the average color, one by one
        for row in range(num_rows):
            for col in range(num_cols):
                self.make_pixel(row, col, square_h, square_w)

    # inverts the colors on the image
    def invert(self):
        copy = self.temp.copy().convert('RGB')
        new = ImageOps.invert(copy)
        new.convert("RGBA")
        self.temp = new

    # converts colors to grayscale
    def grayscale(self):
        copy = self.temp.copy().convert('RGB')
        new = ImageOps.grayscale(copy)
        new.convert("RGBA")
        self.temp = new

    # returns true if edit state is at the beginning of the history, else false
    def is_original_image(self):
        return self.history_pos == 0

    # returns true if edit state is at the end of the history, else false
    def is_latest_image(self):
        return self.history_pos == (len(self.history) - 1)

# test = Picture("images/test_image.jpg")
# test.pixelate(.99)
# test.show()
# test.pixelate(0)
# test.show()
