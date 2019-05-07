import yaml

with open("/home/tuba/config.yaml", "r") as file:
    settings = yaml.load(file, Loader=yaml.CLoader)

with open("/home/tuba/emoji.yaml", "r") as file:
    emojis = yaml.load(file, Loader=yaml.CLoader)


def color_pick(r, g, b):
    return (r*65536) + (g*256) + b

