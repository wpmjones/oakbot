import yaml

with open("config.yaml", "r") as file:
    settings = yaml.load(file, Loader=yaml.CLoader)

with open("emoji.yaml", "r") as file:
    emojis = yaml.load(file, Loader=yaml.CLoader)


def color_pick(r, g, b):
    return int.from_bytes([r, g, b], byteorder='big')

