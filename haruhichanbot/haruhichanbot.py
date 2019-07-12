import logging

import discord

from .config import Config


class HaruhiChanBot(discord.Client):
    def __init__(self, config_file=None):
        super().__init__()
        self.config = Config(config_file)

    def run(self):
        super().run(self.config.bot_token)

    async def on_ready(self):
        logger = logging.getLogger("haruhichanbot")
        logger.info("HaruhiChanBot successfully connected.")
