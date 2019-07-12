import logging

import argparse

from haruhichanbot import HaruhiChanBot


def init_loggers():
    discord_logger = logging.getLogger("haruhichanbot")
    discord_logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    discord_logger.addHandler(ch)


def parse_args():
    parser = argparse.ArgumentParser(
        description="A simple Discord bot for small servers of otakus")
    parser.add_argument("--config", dest="cfg_file",
                        default=None,
                        help="path to the configuration file to use")
    args = parser.parse_args()
    return args


def main():
    init_loggers()
    args = parse_args()
    bot = HaruhiChanBot(args.cfg_file)
    bot.run()


if __name__ == '__main__':
    main()
