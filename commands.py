edit_modes = {
    'crop',
    'sticker',
    'zoom',
    'rotate',
    'contrast',
    'brightness',
    'sharpness',
    'saturation',
    'transparent',
    'pixelate',
    'invert',
    'grayscale',
}

# Synonyms
commands = {
    'brightness' : 'brightness',
    'darkness' : 'brightness',
    'contrast' : 'contrast',

    'crop' : 'crop',
    'cropping' : 'crop',

    'zoom' : 'zoom',
    'pan' : 'zoom',

    'transparent' : 'transparent',
    'transparency' : 'transparent',

    'sticker': 'sticker',

    'undo': 'undo',
    'redo': 'redo',

    'save': 'save',

    'saturation': 'saturation',
    'saturate': 'saturation',

    'sharpness' : 'sharpness',
    'sharp' : 'sharpness',

    'pixelate' : 'pixelate',
    'pixel' : 'pixelate',
    'pixelize' : 'pixelate',

    'invert' : 'invert',
    'invert color' : 'invert',
    'invert colors' : 'invert',

    'grayscale' : 'grayscale',
    'gray' : 'grayscale',
    'black and white' : 'grayscale',

    'rotate' : 'rotate',
}

# Keywords to exit program
terminator = {
    'goodbye',
}

###################################################
##    Commands associated with each edit mode    ##
###################################################

slider_commands = {
    'up': 'up',
    'increase': 'up',
    'raise': 'up',
    'enhance': 'up',

    'down': 'down',
    'decrease': 'down',
    'lessen': 'down',
    'lower': 'down',
    'reduce': 'down',

    # 'more': '',
    # 'less': '',
}

stickers = {
    'balloons': 'balloons',
    'cool': 'cool',
    'flower': 'flower',
    'heart': 'heart',
    'smile': 'smile',
    'star': 'star',
}

transparent_commands = {
    'apply' : 'apply',
    'here' : 'apply',
}

zoom_commands = {
    'in': 'in',
    'out': 'out',

    # 'more': '',
    # 'less': '',
}

actions = {
    'brightness': slider_commands,
    'contrast': slider_commands,
    'pixelate' : slider_commands,
    'saturation': slider_commands,
    'sharpness': slider_commands,
    'sticker': stickers,
    'transparent': transparent_commands,
    'zoom': zoom_commands,
}

all_words = [commands, slider_commands, stickers, transparent_commands, zoom_commands]