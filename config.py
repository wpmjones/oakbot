import yaml
import typing
from datetime import datetime, timedelta

with open("/home/tuba/config.yaml", "r") as file:
    settings = yaml.load(file)

with open("/home/tuba/emoji.yaml", "r") as file:
    emojis = yaml.load(file)


def color_pick(r, g, b):
    return (r*65536) + (g*256) + b


def logger(ctx,
           log_type: str = "INFO",
           cog: str = "main",
           args_dict: typing.Dict[str, str] = {},
           message: str = ""):
    """Custom logging for bot"""
    log_level = 10
    log_types = {"CRITICAL": 50,
                 "ERROR": 40,
                 "WARNING": 30,
                 "INFO": 20,
                 "DEBUG": 10,
                 "NOTSET": 0}
    if log_type in log_types:
        log_type = log_types[log_type]
    else:
        log_type = 20
    print(f"log type = {log_type}")
    if log_type >= log_level:
        date_fmt = "%Y-%m-%d %H:%M:%S"
        msg = f"{(datetime.now() - timedelta(hours=6)).strftime(date_fmt)} | {log_type} | "
        msg += f"{ctx.command} invoked by {ctx.author}"
        msg += f"\n- Channel: {ctx.channel}"
        if len(args_dict) != 0:
            args = "\n- Arguments:"
            for key, value in args_dict.items():
                args += f"\n  - {key}: {value}"
            msg += args
        if message != "":
            msg += f"\nMessage: {message}"
        print(msg)
        with open(f"{cog}.log", "a") as file:
            file.write(msg)

