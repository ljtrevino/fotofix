# fotofix

## Running the program
This project uses Python 3

After you cd into the fotofix folder, run the following command:  
- `$ python main.py`

If you have particular photo you wish to edit you can instead run the command:
- `$ python main.py <filepath>`

If you do not have kivy installed or updated to version 1.11.1, you can run:  
- `$ python -m pip install --upgrade pip wheel setuptools`  
- `$ python -m pip install docutils pygments pypiwin32 kivy.deps.sdl2 kivy.deps.glew --extra-index-url https://kivy.org/downloads/packages/simple/`  
- `$ python -m pip install kivy==1.11.1`  

If you do not have PIL or Numpy installed, you can run:
- `$ python -m pip install pillow` 
- `$ python -m pip install numpy` 

## Running the speech module
Follow the instructions for setting up google cloud authentication credentials here (specifically, under the heading Setting the environment variable): https://cloud.google.com/docs/authentication/getting-started

If you do not have the following libraries installed, you can run:  
- `$ python -m pip install --upgrade google-cloud-speech`  
- `$ python -m pip install --upgrade google-cloud-texttospeech`
- `$ python -m pip install pyaudio`
- `$ python -m pip install playsound`  

## Table of Contents

```
├── audio                       # contains mp3 files with audio feedback the system can give to the user 
├── common                      # includes all the common library code
├── fonts                       # includes all custom font ttf files
├── icons                       # includes png icons for all editing modes as well as icons for settings and toggling between screens
├── images                      # folder for all images to edit; when photos are saved after editing, they are saved to this folder
│
├── speech                  
│   └── fotofix-1586226519938-cf3c6c3749e7.json
│                               # contains key credentials that allow for interaction with Google's Speech APIs
│
├── stickers                    # includes pngs for each of the six stickers that are available when using sticker mode
│
├── commands.py                 # contains all keywords associated with the system and its different edit modes
│
├── graphics.py                 # contains classes for Slider, StickerBar, IconBar, and Overlay
│                                 UI elements which are used in photo_editor.py
│
├── hand.py                     # contains logic pertaining to the leap sensor, hand movements and gestures,
│                                 and the visual cursors that appear on screen to display hand locations
│
├── main.py                     # runs the actual program and initializes 3 screens: the home screen (home.py),
│                                 the photo editor screen (photo_editor.py), and the settings screen (settings.py)
│
├── photo_editor.py             # contains the logic for the photo editing screen.  Allows users to crop, rotate, adjust
│                                 contrast/brightness/saturations/sharpness, add stickers, invert colors, undo, redo, etc.
│
├── picture.py                  # contains the logic to directly edit the image
│
├── settings.py                 # contains the logic for the settings screen which enables the user to toggle between light/dark
│                                 modes, turn on/off written instructions, and adjust variables like gesture smoothness, voice deltas,
│                                 and the threshold for transparency mode
│
└── speech.py                   # contains the setup and logic for speech recognition and audio feedback
```
