import yaml
from datetime import datetime, timedelta

with open("/home/tuba/config.yaml", "r") as f:
    settings = yaml.load(f)

with open("/home/tuba/emoji.yaml", "r") as f:
    emojis = yaml.load(f)


def color_pick(r, g, b):
    return (r*65536) + (g*256) + b


def bot_log(command, request, author, channel, err_flag=0):
    msg = f"{str(datetime.now() - timedelta(hours=6))[:16]} - "
    if err_flag == 0:
        msg += f"Printing {command} for {request}. Requested by {author} in {channel}."
    else:
        msg += f"ERROR: User provided an incorrect argument for {command}. Argument provided: {request}. Requested by {author} in {channel}."
    return msg
