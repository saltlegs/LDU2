from PIL import Image, ImageDraw, ImageFont, ImageChops
import math
import pathlib
import random
from datetime import datetime
import io

import components.shared_instances as shared
import components.function.levels.image_constants as C
import components.function.levels.basic as b
from components.classes.bounds import Bounds
from components.function.logging import log


# dear PIL...
# i HATE YOU
# but you make this possible
# happy valentines 21th june 2025

def truncate(text, max_chars, ellipsis="…"):
    if len(text) <= max_chars:
        return text
    if max_chars <= len(ellipsis):
        return ellipsis[:max_chars]
    return text[:max_chars - len(ellipsis)] + ellipsis

def rounded_rect(draw, box, radius, fill):
    x0, y0, x1, y1 = box

    # corner circles
    draw.pieslice([x0, y0, x0 + 2*radius, y0 + 2*radius], 180, 270, fill=fill)  # top-left
    draw.pieslice([x1 - 2*radius, y0, x1, y0 + 2*radius], 270, 360, fill=fill)  # top-right
    draw.pieslice([x0, y1 - 2*radius, x0 + 2*radius, y1], 90, 180, fill=fill)   # bottom-left
    draw.pieslice([x1 - 2*radius, y1 - 2*radius, x1, y1], 0, 90, fill=fill)     # bottom-right

    # vertical rectangle
    draw.rectangle([x0, y0 + radius, x1, y1 - radius], fill=fill)

    # horizontal rectangle
    draw.rectangle([x0 + radius, y0, x1 - radius, y1], fill=fill)

def get_max_chars(font, width):
    single_char_width = font.getlength("X")
    return int(width // single_char_width)


def get_page(leaderboard, max_rows=5, page_requested=1) -> tuple[list, bool]:
    """bool is whether or not we have too few entries to fill up a single page"""

    # return a "page" from the leaderboard
    # page 1 - index 0-9
    # page 2 - index 10-19
    # page 3 - index 20-29
    # and so on.. depending on params.
    # where n is page requested and x is max rows, y is max entries (2x)
    # n = 3
    # y = 10
    # lower = y * (n - 1) = 20
    # upper = lower + y = 30 (BUT this is ok since slicing is upper exclusive)

    max_entries = max_rows * 2

    if len(leaderboard) < max_entries:
        # not enough entries to have more than 1 page
        return leaderboard, list(range(len(leaderboard))), 1
    
    lower_bound = max_entries * (page_requested - 1)    # y * (n - 1)
    upper_bound = lower_bound + max_entries             # l + y

    # no need to check if there is actually enough pages.
    # we will check beforehand, and slicing does not raise
    # if we go OOB anyway.

    return leaderboard[lower_bound:upper_bound], list(range(lower_bound,upper_bound)), int(math.ceil(len(leaderboard) / max_entries))
    
# base resolution is 600 x 360
# we will render at 1800 x 1080 and then scale down because PIL will not do anti aliasing :(

# entry format: 0 DISPLAY NAME, 1 USER NAME, 2 UUID, 3 LEVEL, 4 TOTAL POINTS, 5 POINTS TO NEXT LEVEL, 6 PROGRESS, 7 USER THEME

def generate_progress_circle(entry, lb_index, theme):

    if lb_index in C.TOP3:
        text_colour = C.TOP3[lb_index]  
        # get the "reward colour" (gold, silver, bronze) for top 3 users
    else:
        text_colour = theme["text"] 
        # get the text colour for requested theme

    chars = len(str(entry[3])) # level (4th element)
    log(f"debug: {chars}")
    if chars == 1:
        font = C.BIGNUMBER
    elif chars == 2:
        font = C.MEDNUMBER
    elif chars > 2:
        font = C.SMALLNUMBER
    # the font size should respect the width of the circle
    # hope and pray to god that nobody ever gets a 4 digit level

    surface = Image.new("RGBA", C.S_DIMS) 
    # dimensions specied in image_constants
    draw = ImageDraw.Draw(surface)
    draw.ellipse(
        (
            C.C_OFFSET,
            C.C_OFFSET,
            C.C_OFFSET + C.C_WIDTH, 
            C.C_OFFSET + C.C_HEIGHT
        ),
        fill=theme["circle"]
    )
    draw.arc(
        (
            C.A_OFFSET,
            C.A_OFFSET,
            C.S_WIDTH - C.A_OFFSET,
            C.S_HEIGHT - C.A_OFFSET
        ),
        start=C.A_START,
        end=C.A_START + C.A_END * entry[6],
        fill=text_colour,
        width=C.A_THICKNESS
    )
    midpoint = (C.C_WIDTH // 2, C.C_HEIGHT // 2)
    draw.text(
        xy=(
            midpoint[0],
            midpoint[1] - C.T_V_OFFSET 
            # inverted because up is down in PIL apparently
        ),
        text=f"{entry[3]}", # level (4th element)
        font=font,
        fill=text_colour,
        anchor="mm"
    )

    return surface, surface.split()[3] # return mask

def generate_user_unit(entry, lb_index: int, theme: tuple, rank_mode=False):
    # entry format: 
    # 0 DISPLAY NAME,       1 USER NAME, 
    # 2 UUID,               3 LEVEL, 
    # 4 TOTAL POINTS,       5 POINTS TO NEXT LEVEL, 
    # 6 PROGRESS,           7 USER THEME
    log(f"generating user unit for {entry[1]}")

    if True: #entry[7] is None:
        theme_palette = theme 
    else:
        theme_palette = b.make_palette(entry[7])


    width = C.LB_USER_UNIT_WIDTH
    width = width + C.RANK_CARD_UNIT_WIDTH_EXTENDER if rank_mode == True else width

    surface = Image.new("RGBA", (width, C.LB_USER_UNIT_HEIGHT))
    draw = ImageDraw.Draw(surface)
    surf_bounds = Bounds((0,0,width,C.LB_USER_UNIT_HEIGHT))

    user_name = entry[1]
    level = entry[3]
    total_points = entry[4]
    points_to_next_level = entry[5]
    user_theme = entry[7]


    level_circle, level_circle_mask = generate_progress_circle(entry, lb_index, theme_palette)


    rounded_rect(
        draw=draw,
        box=surf_bounds.bounds,
        radius=32,
        fill=theme_palette["dark"]
    )

    circle_topleft = (C.LB_C_PADDING, C.LB_C_PADDING)

    surface.paste(level_circle, circle_topleft, level_circle_mask)

    top_text = f"{user_name}" if not rank_mode else f"{total_points} points"
    top_font = C.BODY
    top_max_chars = get_max_chars(top_font, C.LB_USER_UNIT_TEXT_WIDTH)

    top_text = truncate(
        text=top_text,
        max_chars=top_max_chars
    )

    draw.text(
        (C.X_LB_USER_TEXT, surf_bounds.vmiddle - C.LB_USERNAME_V_PADDING),
        text=top_text,
        fill=theme_palette["text"],
        font=top_font,
        anchor="lb"
    )

    bottom_text = f"{points_to_next_level} points to next level"
    # if rank mode, we want to show the points to next level in brackets
    bottom_font = C.BODY_LIGHT
    bottom_max_chars = get_max_chars(bottom_font, C.LB_USER_UNIT_TEXT_WIDTH)

    bottom_text = truncate(
        text=bottom_text,
        max_chars=bottom_max_chars
    )

    draw.text(
        (C.X_LB_USER_TEXT, surf_bounds.vmiddle + C.LB_BOTTOM_V_PADDING),
        text=bottom_text,
        fill=theme_palette["text"],
        font=bottom_font,
        anchor="la"
    )

    return surface, surface.split()[3] # return mask


def generate_leaderboard_image(guild_id: int, guild_name: str, leaderboard: list, max_rows: int, page_requested: int, theme: str = "red", icon=None) -> str:
    "returns the path of the leaderboard image"

    debug = False

    if debug:
        for i in range(30):
            dummy_entry = [
                f"user{i+1}",       # DISPLAY NAME
                f"user{i+1}",       # USER NAME
                f"uuid-{i+1:03}",   # UUID
                i + 1,              # LEVEL
                (i + 1) * 100,      # TOTAL POINTS
                (i + 1) * 50,       # POINTS TO NEXT LEVEL
                (i + 1) / 30,       # PROGRESS (0.0 to 1.0)
                None,
            ]
            leaderboard.append(dummy_entry)
            

    log(f"generating leaderboard image for {guild_name}")


    # guild_id: int, 
    # leaderboard: list, 
    # max_rows: int, 
    # page_requested: int, 
    # theme: str = "red"

    max_rows = min(max_rows, 15) # don't go insane with the rows

    if theme is None: # if no server theme selected then pick random from presets
        theme = random.choice(list(C.PALETTES.values()))

    theme_palette = b.make_palette(theme)

    lb_page_data, lb_indexes, total_pages = get_page(leaderboard, max_rows, page_requested)

    image_height = C.LB_TITLEBAR_HEIGHT + (C.LB_USER_UNIT_HEIGHT + (C.COLUMN_PADDING[0]//2)) * max_rows

    surface = Image.new(
        mode="RGB",
        size=(
            C.LB_WIDTH,
            image_height
        ),
        color=theme_palette["main"]
    )
    draw = ImageDraw.Draw(surface)

    icon_offset = 0
    g_icon = icon
    if g_icon is not None:
        icon_offset = C.LB_ICON_RADIUS
        icon = Image.open(io.BytesIO(g_icon))
        icon = icon.resize((
            C.LB_ICON_RADIUS,
            C.LB_ICON_RADIUS),
            resample=Image.LANCZOS
        ).convert("RGBA")

        # create rounded rect mask for the outer shape
        rounded_mask = Image.new("L", (C.LB_ICON_RADIUS, C.LB_ICON_RADIUS), 0)
        rounded_rect(
            draw=ImageDraw.Draw(rounded_mask),
            box=(0, 0, C.LB_ICON_RADIUS, C.LB_ICON_RADIUS),
            radius=20,
            fill=255
        )

        # combine the icon's own alpha with the rounded mask so both transparency and the rounded corners are respected when pasting
        icon_alpha = icon.split()[3]
        combined_mask = ImageChops.multiply(icon_alpha, rounded_mask)

        surface.paste(icon, (C.LB_TITLE_PADDING_L//2, C.LB_TITLE_PADDING_U//2), combined_mask)

    title_text = guild_name
    title_font = C.TITLE
    title_max_chars = get_max_chars(title_font, C.LB_TITLE_TEXT_WIDTH - icon_offset)

    title_text = truncate(
        text=title_text,
        max_chars=title_max_chars
    )

    draw.text(
        xy = (
            C.LB_TITLE_PADDING_L + icon_offset,
            C.LB_TITLE_PADDING_U
        ),
        text=title_text,
        font=title_font,
        fill=theme_palette["text"]
    )

    meta_text_top = f"{datetime.now().strftime('%d %m %y')}" 
    meta_text_middle = f"page {page_requested} / {total_pages}"
    meta_text_bottom = f"c-ldu {shared.version}"
    meta_text_font = C.TINY_LIGHT
    meta_text_max_chars = get_max_chars(meta_text_font, C.LB_TITLE_META_WIDTH)
    meta_text_top = truncate(
        text=meta_text_top,
        max_chars=meta_text_max_chars
    )
    meta_text_bottom = truncate(
        text=meta_text_bottom,
        max_chars=meta_text_max_chars
    )
    
    draw.text(
        xy = (
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U
        ),
        align = "right",
        text = f"{meta_text_top}",
        font = meta_text_font,
        fill = theme_palette["text"],
        anchor="rt"
    )

    draw.text(
        xy = (
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U + meta_text_font.getbbox(meta_text_top)[3] + 5
        ),
        align = "right",
        text = f"{meta_text_middle}",
        font = meta_text_font,
        fill = theme_palette["text"],
        anchor="rt"
    )  

    draw.text(
        xy = (
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U + (meta_text_font.getbbox(meta_text_top)[3] + 5) * 2
        ),
        align = "right",
        text = f"{meta_text_bottom}",
        font = meta_text_font,
        fill = theme_palette["text"],
        anchor="rt"
    )


    # user unit loop

    for i, entry in enumerate(lb_page_data):
        ypos = C.LB_TITLEBAR_HEIGHT + ((C.LB_USER_UNIT_HEIGHT + C.COLUMN_PADDING[0]//2) * (i % max_rows))
        xpos = C.X_LEFT_COLUMN if i < max_rows else C.X_RIGHT_COLUMN

        user_unit, mask = generate_user_unit(
            entry=entry,
            lb_index=lb_indexes[i],
            theme=theme_palette
        )
        surface.paste(user_unit, (xpos, ypos), mask)

    surface = surface.resize(
        (
            C.LB_WIDTH // 2,
            image_height // 2
        ),
        resample=Image.LANCZOS
    )

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = C.TEMP_IMAGE_PATH / f"{guild_id}_{timestamp}.png"

    C.TEMP_IMAGE_PATH.mkdir(parents=True, exist_ok=True) # make the temp directory if it doesn't exist

    surface.save(savepath)
    return savepath

    # entry format: 
    # 0 DISPLAY NAME,       1 USER NAME, 
    # 2 UUID,               3 LEVEL, 
    # 4 TOTAL POINTS,       5 POINTS TO NEXT LEVEL, 
    # 6 PROGRESS,           7 USER THEME

def find_user_in_leaderboard(leaderboard, user_id):
    """returns the index of the user in the leaderboard, or -1 if not found"""
    for i, entry in enumerate(leaderboard):
        if entry[2] == user_id:
            return entry, i
    return None, -1


def generate_rank_card_image(guild_id: int, guild_name: str, leaderboard: list, user_requested: int, theme: str = "red") -> str:
    "returns the path of the rank card image"
    

    # accept both string and tuple themes
    if isinstance(theme, str):
        if theme not in C.PALETTES:
            theme = "red"
        theme_palette = b.make_palette(C.PALETTES[theme])
    elif isinstance(theme, tuple) and len(theme) == 3:
        theme_palette = b.make_palette(theme)
    else:
        theme_palette = b.make_palette((220, 50, 70))  # fallback to red



    entry, lb_index = find_user_in_leaderboard(leaderboard, user_requested)
    if entry is None:
        log(f"~1user {user_requested} not found in leaderboard, can't generate rank card")
        return None
    
    if not entry[7] is None:
        theme_palette = b.make_palette(entry[7])

    surface = Image.new(
        size=(C.RANK_CARD_WIDTH, C.RANK_CARD_HEIGHT),
        mode="RGB",
        color=theme_palette["main"]
    )
    draw = ImageDraw.Draw(surface)

    title_text = entry[1] # username
    title_font = C.TITLE
    title_max_chars = get_max_chars(title_font, C.RANK_CARD_TITLE_WIDTH)

    title_text = truncate(
        text=title_text,
        max_chars=title_max_chars
    )

    draw.text(
        xy = (
            C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U
        ),
        text=title_text,
        font=title_font,
        fill=theme_palette["text"]
    )

    user_unit,mask = generate_user_unit(entry, lb_index, theme_palette, rank_mode=True)

    unit_pos = (
        C.RANK_CARD_LEFT_PAD,
        C.LB_TITLEBAR_HEIGHT
    )

    surface.paste(
        im=user_unit,
        box=unit_pos,
        mask=mask
    )

    surface = surface.resize(
        (
            C.RANK_CARD_WIDTH // 3,
            C.RANK_CARD_HEIGHT // 3
        ),
        resample=Image.LANCZOS
    )

    user_id = entry[2]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = C.TEMP_IMAGE_PATH / f"{user_id}_{guild_id}_{timestamp}.png"

    C.TEMP_IMAGE_PATH.mkdir(parents=True, exist_ok=True) # make the temp directory if it doesn't exist

    surface.save(savepath)
    return savepath