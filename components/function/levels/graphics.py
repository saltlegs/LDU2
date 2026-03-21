from PIL import Image, ImageDraw

import components.function.levels.image_constants as C
from components.classes.bounds import Bounds
from components.function.logging import log


# entry format:
# 0 DISPLAY NAME,       1 USER NAME,
# 2 UUID,               3 LEVEL,
# 4 TOTAL POINTS,       5 POINTS TO NEXT LEVEL,
# 6 PROGRESS,           7 USER THEME


def truncate(text, max_chars, ellipsis="…"):
    if len(text) <= max_chars:
        return text
    if max_chars <= len(ellipsis):
        return ellipsis[:max_chars]
    return text[:max_chars - len(ellipsis)] + ellipsis


def rounded_rect(draw, box, radius, fill=None, border_width=0, border=None):
    x0, y0, x1, y1 = box

    # clamp to max radius
    max_radius = min((x1 - x0) // 2, (y1 - y0) // 2)
    radius = min(radius, max_radius)

    def _draw_filled(x0, y0, x1, y1, r, color):
        draw.pieslice([x0, y0, x0 + 2*r, y0 + 2*r], 180, 270, fill=color)        # top-left
        draw.pieslice([x1 - 2*r, y0, x1, y0 + 2*r], 270, 360, fill=color)        # top-right
        draw.pieslice([x0, y1 - 2*r, x0 + 2*r, y1], 90, 180, fill=color)         # bottom-left
        draw.pieslice([x1 - 2*r, y1 - 2*r, x1, y1], 0, 90, fill=color)           # bottom-right
        draw.rectangle([x0, y0 + r, x1, y1 - r], fill=color)                     # vertical rect
        draw.rectangle([x0 + r, y0, x1 - r, y1], fill=color)                     # horizontal rect

    if border is not None and border_width > 0:
        # draw outer shape in border colour then inner shape in fill colour
        _draw_filled(x0, y0, x1, y1, radius, border)
        if fill is not None:
            inner_r = max(0, radius - border_width)
            _draw_filled(
                x0 + border_width, y0 + border_width,
                x1 - border_width, y1 - border_width,
                inner_r, fill
            )
    elif fill is not None:
        _draw_filled(x0, y0, x1, y1, radius, fill)


def get_max_chars(font, width):
    single_char_width = font.getlength("X")
    return int(width // single_char_width)


def generate_progress_circle(entry, lb_index, theme):

    if lb_index in C.TOP3:
        user_theme_colour = tuple(entry[7]) if entry[7] is not None else None
        text_colour = user_theme_colour if user_theme_colour is not None else C.TOP3[lb_index]
        # use the user's theme colour if set, otherwise fall back to gold/silver/bronze
    else:
        text_colour = theme["text"]
        # get the text colour for requested theme

    chars = len(str(entry[3]))  # level (4th element)
    if chars == 1:
        font = C.BIGNUMBER
    elif chars == 2:
        font = C.MEDNUMBER
    elif chars > 2:
        font = C.SMALLNUMBER
    # the font size should respect the width of the circle
    # hope and pray to god that nobody ever gets a 4 digit level

    surface = Image.new("RGBA", C.S_DIMS)
    # dimensions specified in image_constants
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
        text=f"{entry[3]}",  # level (4th element)
        font=font,
        fill=text_colour,
        anchor="mm"
    )

    return surface, surface.split()[3]  # return mask


def generate_user_unit(entry, lb_index: int, theme: tuple, rank_mode=False):
    log(f"generating user unit for {entry[1]}")

    theme_palette = theme
    if entry[7] is not None:
        border_colour = tuple(entry[7])
    elif lb_index in C.TOP3:
        border_colour = C.TOP3[lb_index]
    else:
        border_colour = None

    width = C.LB_USER_UNIT_WIDTH
    width = width + C.RANK_CARD_UNIT_WIDTH_EXTENDER if rank_mode == True else width

    surface = Image.new("RGBA", (width+1, C.LB_USER_UNIT_HEIGHT+1))  # little buffer makes look nice
    draw = ImageDraw.Draw(surface)
    surf_bounds = Bounds((0, 0, width, C.LB_USER_UNIT_HEIGHT))

    user_name = entry[1]
    total_points = entry[4]
    points_to_next_level = entry[5]

    level_circle, level_circle_mask = generate_progress_circle(entry, lb_index, theme_palette)

    rounded_rect(
        draw=draw,
        box=surf_bounds.bounds,
        radius=C.LB_USER_UNIT_CORNER_RADIUS,
        fill=theme_palette["dark"],
        border_width=C.LB_USER_UNIT_BORDER_WIDTH if border_colour is not None else C.LB_USER_UNIT_BORDER_WIDTH_THIN,
        border=border_colour if border_colour is not None else (*theme_palette["text"], 80)
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

    return surface, surface.split()[3]  # return mask
