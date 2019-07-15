import logging
import inspect
import random

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

    async def cmd_random(self, cmd_args):
        """
        Pick a random number between specified numbers (included)
        If no numbers are specified, pick a number between 0 and 1
        If one number is specified, pick a number between 0 and this number
        If two numbers are specified, pick a number between nb1 and nb2

        Usage:
            {command_prefix}random
            {command_prefix}random nb
            {command_prefix}random nb1 nb2
        """
        start = 0
        end = 1

        if len(cmd_args) == 1:
            try:
                end = int(cmd_args[0])
                if end <= start:
                    raise ValueError
            except ValueError:
                return "Invalid argument: please provide a strictly positive integer"

        elif len(cmd_args) == 2:
            try:
                nb1 = int(cmd_args[0])
                nb2 = int(cmd_args[0])
            except ValueError:
                return "Invalid argument: please provide an integer"
            if nb1 == nb2:
                return "Invalid argument: please use different numbers"
            # Set numbers so that start < end
            start = nb1 if nb1 < nb2 else nb2
            end = nb1 if nb1 > nb2 else nb2

        elif len(cmd_args) > 2:
            return "Invalid argument: please use at most 2 numbers"

        result = random.randint(start, end)
        return "random in [{0}, {1}] = {2}".format(start, end, result)

    async def cmd_coinflip(self):
        """
        Flip a coin and display the result (heads or tails)

        Usage:
            {command_prefix}coinflip
        """
        if random.randint(0, 1) == 0:
            return "Heads!"
        return "Tails!"
