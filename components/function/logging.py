import datetime
import sys
import os
from pathlib import Path

from components.shared_instances import logged_amount

COLOURS = {
    "1": "\033[31m",      # red
    "2": "\033[32m",      # green
    "3": "\033[33m",      # yellow
    "4": "\033[34m",      # blue
    "5": "\033[35m",      # magenta
    "6": "\033[36m",      # cyan
    "7": "\033[37m",      # white
}
# ~r is reset code

COLOUR_ROTATION = ["7", "6"] # console will cycle through these colours when printing text

def log(message):
    global logged_amount
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    file_timestamp = Path("logs") / datetime.datetime.now().strftime("%d_%m_%Y.txt")
    file_timestamp.parent.mkdir(parents=True, exist_ok=True)
    reset_colour = COLOUR_ROTATION[logged_amount % len(COLOUR_ROTATION)]

    new_message = []
    new_message_plain = []

    colour_assign_mode = False
    for char in message:
        if colour_assign_mode:
            if char in COLOURS:
                new_message.append(COLOURS[char])
            elif char == "r":
                new_message.append(COLOURS[reset_colour])
            colour_assign_mode = False
            continue
        if char == "~":
            colour_assign_mode = True
            continue
        else:
            new_message.append(char)
            new_message_plain.append(char)
    new_message = "".join(new_message)
    new_message_plain = "".join(new_message_plain)


    file_timestamp.touch()
    with file_timestamp.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {new_message_plain}\n")

    out = f"{COLOURS[reset_colour]}[{timestamp}] {new_message}{COLOURS[reset_colour]}\n"
    try:
        sys.stdout.buffer.write(out.encode("utf-8"))
        sys.stdout.buffer.flush()
    except Exception:
        try:
            print(out, end="")
        except UnicodeEncodeError:
            sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
            sys.stdout.buffer.flush()
    logged_amount += 1

    