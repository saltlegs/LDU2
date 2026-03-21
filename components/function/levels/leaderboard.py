from PIL import Image, ImageDraw, ImageChops
import math
import random
import io
from datetime import datetime

import components.shared_instances as shared
import components.function.levels.image_constants as C
import components.function.levels.basic as b
from components.function.logging import log
from components.function.levels.graphics import (
    truncate,
    get_max_chars,
    rounded_rect,
    generate_user_unit,
)


LD_DEBUG = False
if LD_DEBUG:
    log("~3==================================================")
    log("~3WARN: LD_DEBUG is TRUE, turn off before deploying!")
    log("~3==================================================")


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

    return leaderboard[lower_bound:upper_bound], list(range(lower_bound, upper_bound)), int(math.ceil(len(leaderboard) / max_entries))


def generate_leaderboard_image(guild_id: int, guild_name: str, leaderboard: list, max_rows: int, page_requested: int, theme: str = "red", icon=None) -> str:
    "returns the path of the leaderboard image"

    if LD_DEBUG:
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

    max_rows = min(max_rows, 15)  # don't go insane with the rows

    if theme is None:  # if no server theme selected then pick random from presets
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
            radius=C.LB_ICON_CORNER_RADIUS,
            fill=255
        )

        # combine the icon's own alpha with the rounded mask so both transparency
        # and the rounded corners are respected when pasting
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
        xy=(
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
    meta_text_top = truncate(text=meta_text_top, max_chars=meta_text_max_chars)
    meta_text_bottom = truncate(text=meta_text_bottom, max_chars=meta_text_max_chars)

    draw.text(
        xy=(
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U
        ),
        align="right",
        text=f"{meta_text_top}",
        font=meta_text_font,
        fill=theme_palette["text"],
        anchor="rt"
    )

    draw.text(
        xy=(
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U + meta_text_font.getbbox(meta_text_top)[3] + 5
        ),
        align="right",
        text=f"{meta_text_middle}",
        font=meta_text_font,
        fill=theme_palette["text"],
        anchor="rt"
    )

    draw.text(
        xy=(
            C.LB_WIDTH - C.LB_TITLE_PADDING_L,
            C.LB_TITLE_PADDING_U + (meta_text_font.getbbox(meta_text_top)[3] + 5) * 2
        ),
        align="right",
        text=f"{meta_text_bottom}",
        font=meta_text_font,
        fill=theme_palette["text"],
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

    surface = surface.reduce(2)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    savepath = C.TEMP_IMAGE_PATH / f"{guild_id}_{timestamp}.png"

    C.TEMP_IMAGE_PATH.mkdir(parents=True, exist_ok=True)

    surface.save(savepath)
    return savepath
