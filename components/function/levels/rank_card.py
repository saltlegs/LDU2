from PIL import Image, ImageDraw
from datetime import datetime

import components.function.levels.image_constants as C
import components.function.levels.basic as b
from components.function.logging import log
from components.function.levels.graphics import (
    truncate,
    get_max_chars,
    generate_user_unit,
)


# entry format:
# 0 DISPLAY NAME,       1 USER NAME,
# 2 UUID,               3 LEVEL,
# 4 TOTAL POINTS,       5 POINTS TO NEXT LEVEL,
# 6 PROGRESS,           7 USER THEME


def find_user_in_leaderboard(leaderboard, user_id):
    """returns the entry and index of the user in the leaderboard, or (None, -1) if not found"""
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

    if entry[7] is not None:
        theme_palette = b.make_palette(entry[7])

    surface = Image.new(
        size=(C.RANK_CARD_WIDTH, C.RANK_CARD_HEIGHT),
        mode="RGB",
        color=theme_palette["main"]
    )
    draw = ImageDraw.Draw(surface)

    title_text = entry[1]  # username
    title_font = C.TITLE
    title_max_chars = get_max_chars(title_font, C.RANK_CARD_TITLE_WIDTH)

    title_text = truncate(
        text=title_text,
        max_chars=title_max_chars
    )

    draw.text(
        xy=(
            C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U
        ),
        text=title_text,
        font=title_font,
        fill=theme_palette["text"]
    )

    user_unit, mask = generate_user_unit(entry, lb_index, theme_palette, rank_mode=True)

    unit_pos = (
        C.RANK_CARD_LEFT_PAD,
        C.LB_TITLEBAR_HEIGHT
    )

    surface.paste(
        im=user_unit,
        box=unit_pos,
        mask=mask
    )

    surface = surface.reduce(3)  # box average downsample — clean supersampling for integer scale factors

    user_id = entry[2]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = C.TEMP_IMAGE_PATH / f"{user_id}_{guild_id}_{timestamp}.png"

    C.TEMP_IMAGE_PATH.mkdir(parents=True, exist_ok=True)

    surface.save(savepath)
    return savepath
