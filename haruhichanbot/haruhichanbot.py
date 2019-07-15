import logging
import inspect

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

    async def on_message(self, message):
        await self.wait_until_ready()

        if message.author == self.user:
            return

        message_content = message.content.strip()
        if not message_content.startswith(self.config.command_prefix):
            return

        command, *args = message_content.split()
        command = command[len(self.config.command_prefix):].lower()

        try:
            handler = getattr(self, "cmd_" + command)
        except AttributeError:
            logger = logging.getLogger("haruhichanbot")
            logger.debug("Invalid command: {0}\nOriginal message: {1}".format(
                command, message_content))
            await message.channel.send(
                "Invalid command, see {0}help for a list of commands".format(
                    self.config.command_prefix))
            return

        params = inspect.signature(handler).parameters.copy()

        handler_kwargs = {}
        if params.pop('cmd_args', None):
            handler_kwargs['cmd_args'] = args

        response = await handler(**handler_kwargs)
        if response:
            await message.channel.send(response)

    async def cmd_help(self):
        """
        Prints a help message.

        Usage:
            {command_prefix}help
        """
        commands = inspect.getmembers(self, predicate=inspect.ismethod)
        commands = [cmd for cmd in commands if cmd[0].startswith("cmd_")]

        help_msg = ["HaruhiChanBot commands:"]
        for cmd_name, cmd_method in commands:
            # Gets the first relevant line of the docstring of the method
            doc = cmd_method.__doc__.split('\n')[1].strip()
            help_msg.append("\t- {prefix}{cmd_name}: {desc}".format(
                prefix=self.config.command_prefix,
                cmd_name=cmd_name[4:],
                desc=doc))
        return '\n'.join(help_msg)
