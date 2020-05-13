import sys, os
sys.path.insert(0, os.path.abspath('..'))

from common.core import BaseWidget, run, lookup
from common.screen import ScreenManager, Screen

from kivy.core.window import Window

import photo_editor
from settings import Settings
from home import Homepage

# Makes window open full screen
Window.fullscreen = 'auto'

sm = ScreenManager()
sm.add_screen(Homepage(name='home'))
sm.add_screen(photo_editor.PhotoEditor(name='photo_editor', sm=sm ))
sm.add_screen(Settings(name='settings'))

if __name__ == "__main__":
    if (len(sys.argv) >= 2): # ['main.py', 'filepath', '...']
        _, filepath = sys.argv[:2]
        photo_editor.filepath = filepath
        sm.switch_to('photo_editor')
    else:
        sm.switch_to('home')

    run(sm)
