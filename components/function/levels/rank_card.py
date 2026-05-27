from PIL import Image, ImageDraw, ImageChops
from datetime import datetime
import io

import components.function.levels.image_constants as C
import components.function.levels.basic as b
from components.function.logging import log
from components.function.levels.graphics import (
    truncate,
    get_max_chars,
    generate_user_unit,
    rounded_rect,
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


def generate_rank_card_image(guild_id: int, guild_name: str, leaderboard: list, user_requested: int, theme: str = "red", avatar=None) -> str:
    "returns the path of the rank card image"

    theme_palette = b.make_palette(C.PALETTES["black"])

    entry, lb_index = find_user_in_leaderboard(leaderboard, user_requested)
    if entry is None:
        log(f"~1user {user_requested} not found in leaderboard, can't generate rank card")
        return None

    surface = Image.new(
        size=(C.RANK_CARD_WIDTH, C.RANK_CARD_HEIGHT),
        mode="RGB",
        color=theme_palette["main"]
    )
    draw = ImageDraw.Draw(surface)

    avatar_offset = 0
    if avatar is not None:
        avatar_size = C.LB_ICON_RADIUS
        av_img = Image.open(io.BytesIO(avatar))
        av_img = av_img.resize((avatar_size, avatar_size), resample=Image.LANCZOS).convert("RGBA")
        rounded_mask = Image.new("L", (avatar_size, avatar_size), 0)
        rounded_rect(
            draw=ImageDraw.Draw(rounded_mask),
            box=(0, 0, avatar_size, avatar_size),
            radius=C.LB_ICON_CORNER_RADIUS,
            fill=255
        )
        av_alpha = av_img.split()[3]
        combined_mask = ImageChops.multiply(av_alpha, rounded_mask)
        surface.paste(av_img, (C.LB_TITLE_PADDING_L // 2, C.LB_TITLE_PADDING_U // 2), combined_mask)
        avatar_offset = avatar_size + C.LB_TITLE_PADDING_L // 2

    display_name = truncate(entry[0], get_max_chars(C.BODY, C.RANK_CARD_TITLE_WIDTH - avatar_offset))
    username_text = truncate(f"@{entry[1]}", get_max_chars(C.BODY_LIGHT, C.RANK_CARD_TITLE_WIDTH - avatar_offset))
    rank_text = f"#{lb_index + 1}" #/{len(leaderboard)}"
    guild_text = truncate(guild_name, get_max_chars(C.TINY_LIGHT, C.RANK_CARD_META_WIDTH))
    right_x = C.RANK_CARD_WIDTH - C.LB_TITLE_PADDING_L
    meta_line_step = C.TINY_LIGHT.getbbox("A")[3] + 7

    draw.text((C.LB_TITLE_PADDING_L + avatar_offset, C.LB_TITLE_PADDING_U), display_name, font=C.BODY, fill=theme_palette["text"], anchor="lt")
    draw.text((C.LB_TITLE_PADDING_L + avatar_offset, 97), username_text, font=C.BODY_LIGHT, fill=theme_palette["text"], anchor="lt")
    draw.text((right_x, C.LB_TITLE_PADDING_U), guild_text, font=C.TINY_LIGHT, fill=theme_palette["text"], anchor="rt")
    draw.text((right_x, C.LB_TITLE_PADDING_U + meta_line_step + 2), rank_text, font=C.TITLE_LIGHT, fill=theme_palette["text"], anchor="rt")

    rank_top_text = f"{entry[5]} points to next level"
    if len(leaderboard) == 1:
        rank_bottom_text = None
    elif lb_index == 0:
        next_entry = leaderboard[1]
        gap = entry[4] - next_entry[4]
        rank_bottom_text = f"{gap} points ahead of {next_entry[1]}"
    else:
        above_entry = leaderboard[lb_index - 1]
        gap = above_entry[4] - entry[4]
        rank_bottom_text = f"{gap} points behind {above_entry[1]}"

    user_unit, mask = generate_user_unit(entry, lb_index, theme_palette, rank_mode=True, leaderboard_size=len(leaderboard), rank_top_text=rank_top_text, rank_bottom_text=rank_bottom_text)

    unit_pos = (
        C.RANK_CARD_LEFT_PAD,
        C.LB_TITLEBAR_HEIGHT
    )

    surface.paste(
        im=user_unit,
        box=unit_pos,
        mask=mask
    )

    surface = surface.reduce(2)

    user_id = entry[2]

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = C.TEMP_IMAGE_PATH / f"{user_id}_{guild_id}_{timestamp}.png"

    C.TEMP_IMAGE_PATH.mkdir(parents=True, exist_ok=True)

    surface.save(savepath)
    return savepath
