from PIL import Image, ImageDraw, ImageFont
from math import ceil
import time
import os
import timeit
from pathlib import Path

try:
    from components.function.logging import log
except ImportError:
    log = print # fallback for logging if the import fails

TEMP_IMAGE_PATH = Path("./savedata/temp/")
ASSETS_PATH = Path("./assets/")
TYPES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../assets/type/')

# COLOURS

PALETTES = {
    "red": (220, 50, 70),
    "blue": (70, 110, 220),
    "green": (60, 180, 90),
    "pink": (255, 119, 158),
    "orange": (255, 140, 40),
    "black": (40, 40, 40),
}

# top3 is in index order for the sake of easy retrieval
TOP3 = {
    0: (218, 177, 99),  # gold
    1: (176, 167, 184), # silver
    2: (181, 103, 43)   # bronze
}

# LOADING FONTS

# be mindful of the file type if you are changing the font (ttf, otf, etc). 
# this script is designed for monospace fonts, and is not designed to
# support variable width typefaces!
FONT_TYPE = ".otf"

BIGNUMBER = ImageFont.truetype(f"{TYPES_PATH}typeface{FONT_TYPE}", 100)
MEDNUMBER = ImageFont.truetype(f"{TYPES_PATH}typeface{FONT_TYPE}", 86)
TITLE = ImageFont.truetype(f"{TYPES_PATH}typeface{FONT_TYPE}", 105)
BODY = ImageFont.truetype(f"{TYPES_PATH}typeface{FONT_TYPE}", 72)
BODY_LIGHT = ImageFont.truetype(f"{TYPES_PATH}light{FONT_TYPE}", 42)
TINY = ImageFont.truetype(f"{TYPES_PATH}typeface{FONT_TYPE}", 33)
TINY_LIGHT = ImageFont.truetype(f"{TYPES_PATH}light{FONT_TYPE}", 33)

# LEVEL CIRCLE CONSTANTS

C_HEIGHT, C_WIDTH = 165,165
C_OFFSET = 1            # padding around edge of circle to prevent clipping

# circle exp indicator arc constants

A_OFFSET = 12           # gap between edge of circle and edge of arc
A_THICKNESS = 12    
A_START = 0             # range of degrees to use for the exp indicator
A_END = 360             # 270 for example would use only 3 quarters for the indicator
A_START = A_START - 90  # rotate by -90 because PIL arc func starts at 3 o'clock for some reason

T_V_OFFSET = -8          # text vertical offset (positive = up)

# MAIN LEADERBOARD LAYOUT CONSTANTS

PADDING = C_OFFSET * 2
S_HEIGHT, S_WIDTH = C_HEIGHT + PADDING, C_WIDTH + PADDING # padding to prevent clipping
S_DIMS = (S_WIDTH, S_HEIGHT)
C_DIMS = (C_WIDTH, C_HEIGHT)

LB_WIDTH = 1800             # height is calculated dynamically based on amount of rows specified
LB_TITLEBAR_HEIGHT = 150    # height of titlebar at the top of image, only exists once
LB_TITLE_PADDING_U = 30
LB_TITLE_PADDING_L = 30
LB_ICON_RADIUS = LB_TITLEBAR_HEIGHT - LB_TITLE_PADDING_U
LB_TITLE_META_WIDTH = 345   # region reserved for date & page count
LB_TITLE_TEXT_WIDTH = LB_WIDTH - LB_TITLE_META_WIDTH

COLUMN_WIDTH = LB_WIDTH // 2    # column is half each of width
COLUMN_PADDING = (8, 4)         # edge, middle
LB_USER_UNIT_HEIGHT = 180
LB_USER_UNIT_WIDTH = COLUMN_WIDTH - (COLUMN_PADDING[0] + (COLUMN_PADDING[1] // 2))
# i.e. | 8 | user unit | 4 | 4 | user | 8 |
# uses full 8 of padding but for both shared in the middle
X_LEFT_COLUMN = COLUMN_PADDING[0]
X_RIGHT_COLUMN = COLUMN_WIDTH + COLUMN_PADDING[1] // 1

LB_C_PADDING = (LB_USER_UNIT_HEIGHT - C_HEIGHT) // 2


LB_USERNAME_V_PADDING = 0
LB_BOTTOM_V_PADDING = 30
LB_USER_TEXT_PAD = 15
X_LB_USER_TEXT = (LB_C_PADDING * 2) + C_WIDTH + LB_USER_TEXT_PAD
LB_USER_UNIT_TEXT_WIDTH = LB_USER_UNIT_WIDTH - ((LB_C_PADDING * 3) + C_WIDTH)

# i.e. | cpad | circle | cpad | text | cpad |

RANK_CARD_UNIT_WIDTH_EXTENDER = 250

RANK_CARD_TITLE_WIDTH = LB_TITLE_TEXT_WIDTH
RANK_CARD_META_WIDTH = LB_TITLE_META_WIDTH
RANK_CARD_HEIGHT = LB_TITLEBAR_HEIGHT + LB_USER_UNIT_HEIGHT + LB_BOTTOM_V_PADDING 
RANK_CARD_LEFT_PAD = RANK_CARD_HEIGHT - LB_TITLEBAR_HEIGHT - LB_USER_UNIT_HEIGHT
RANK_CARD_WIDTH = LB_USER_UNIT_WIDTH + (2*RANK_CARD_LEFT_PAD) + (RANK_CARD_UNIT_WIDTH_EXTENDER)