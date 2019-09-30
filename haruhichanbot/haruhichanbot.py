import logging
import inspect
import random
import textwrap

import discord

from .config import Config
from .commands_config import CommandsConfig
from . import db_manager
from . import exceptions


class HaruhiChanBot(discord.Client):
    def __init__(self, config_file=None,
                 command_config_file=None):
        super().__init__()
        self.config = Config(config_file)
        self.cmd_cfg = CommandsConfig(
            command_config_file)
        db_manager.init_session(self.config)

    def run(self):
        super().run(self.config.bot_token)

    def _prettify_docstring(self, docstring):
        """
        Returns a docstring with clean indentation and
        proper replacement of strings like {command_prefix}
        """
        pretty_docstring = textwrap.dedent(docstring)
        pretty_docstring = pretty_docstring.replace("{command_prefix}",
                                                    self.config.command_prefix)
        return pretty_docstring

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
        if params.pop('user_id', None):
            handler_kwargs['user_id'] = message.author.id
        if params.pop('user', None):
            handler_kwargs['user'] = message.author
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

        help_msg = ["```", "HaruhiChanBot commands:"]
        for cmd_name, cmd_method in commands:
            # Gets the first relevant line of the docstring of the method
            doc = cmd_method.__doc__.split('\n')[1].strip()
            help_msg.append("\t- {prefix}{cmd_name}: {desc}".format(
                prefix=self.config.command_prefix,
                cmd_name=cmd_name[4:],
                desc=doc))
        help_msg.append("```")
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

    async def cmd_register_account(self, user_id, cmd_args):
        """
        Register a game or website account and link it to your profile on this server

        Usage:
            {command_prefix}register_account game_or_website [server] name_or_id
            Ex: {command_prefix}register_account azurlane sandy 123123123
        """
        async def help(self):
            msg = "```{0}```\n{1}".format(
                self._prettify_docstring(self.cmd_register_account.__doc__),
                await self.get_register_accounts_infos())
            return msg

        if len(cmd_args) == 1 and cmd_args[0] == "help":
            return await help(self)
        if len(cmd_args) <= 1 or len(cmd_args) > 3:
            return "Invalid number of arguments.\n" + await help(self)

        input_acc_server = cmd_args[1].lower() if len(cmd_args) == 3 else None

        try:
            acc_source, acc_server = \
                self.check_and_get_account_source_and_server(cmd_args[0],
                                                             input_acc_server)
        except exceptions.AccountSourceNotFoundException as e:
            return (f"Game/Website `{e.account_source}` not found.\n" +
                    "See help for a list of available game/websites")
        except exceptions.AccountHasNoServerWarning:
            return ("Warning: this game/website doesn't have any servers.\n" +
                    "Please relaunch the command without specifying a server")
        except exceptions.AccountServerRequiredException:
            return "You need to enter a server for this game/website."
        except exceptions.InvalidAccountServerException as e:
            msg = ("Server `{serv}` doesn't exist for `{src}`.\n" +
                   "List of servers for `{src}`: `{servers}`")
            return msg.format(serv=e.input_acc_server,
                              src=e.account_source,
                              servers=e.account_servers)

        account_name = cmd_args[-1]
        try:
            db_manager.insert_user_account(
                discord_user_id=user_id,
                account_source=acc_source,
                account_server=acc_server,
                account_name=account_name)
        except exceptions.DuplicateDbEntryWarning:
            return "Account already registered."
        except Exception as e:
            logger = logging.getLogger("haruhichanbot")
            logger.error("Exception in cmd_register_account\n" +
                         "Msg={0}\nArgs={1}".format(e, cmd_args))
            return "An unknown error happened, please contact administrator."

        msg = f"Account on `{acc_source}`"
        if acc_server:
            msg += f"(server: `{acc_server}`) "
        return msg + " successfully added."

    async def get_register_accounts_infos(self):
        """
        Returns a human-readable string of all games & website,
        their aliases and their servers if applicable.
        """
        msg = list()
        msg.append("```Game/Website (aliases): Servers")

        for source, source_infos in (self.cmd_cfg.account_sources.items()):
            if source_infos["servers"]:
                servs = ", ".join(source_infos["servers"])
            else:
                servs = "N/A"
            if source_infos["aliases"]:
                aliases = ", ".join(source_infos["aliases"])
                msg.append("\t- {src} ({aliases}): {servs}".format(
                    src=source, aliases=aliases, servs=servs))
            else:
                msg.append("\t- {src}: {servs}".format(
                    src=source, servs=servs))
        msg.append("```")
        return "\n".join(msg)

    def check_and_get_account_source_and_server(self, input_acc_source,
                                                input_acc_server=None,
                                                allow_empty_serv=False):
        """
        Checks if the input account source and server are valid
        and returns their true name
        """
        try:
            # Get the real name of the source from the potential alias
            # Also get the infos concerning the source
            acc_source, source_infos = self.cmd_cfg.get_account_source_infos(
                input_acc_source)
        except exceptions.NoAccountSourceInfosException:
            raise exceptions.AccountSourceNotFoundException(input_acc_source)

        if source_infos["servers"] is None and input_acc_server:
            raise exceptions.AccountHasNoServerWarning()
        if (source_infos["servers"] and not input_acc_server and
                not allow_empty_serv):
            raise exceptions.AccountServerRequiredException()

        account_server = None
        if input_acc_server:
            account_server = input_acc_server.lower()
            if (account_server not in
                    [x.lower() for x in source_infos["servers"]]):
                acc_servers = ", ".join(source_infos["servers"])
                raise exceptions.InvalidAccountServerException(
                    input_acc_server, acc_source, acc_servers)

        return acc_source, account_server

    async def cmd_list_self_accounts(self, user_id):
        """
        Lists account that belongs to your profile on this server

        Usage:
            {command_prefix}list_self_accounts
        """

        accounts = db_manager.get_accounts_for_user(user_id)
        if not accounts:
            return "You have no accounts registered on this server."

        msg = list()
        msg.append("Your accounts:```")
        for account in accounts:
            if not account.account_server:
                msg.append(f"{account.account_source}: {account.account_name}")
            else:
                msg.append(f"{account.account_source}" +
                           f" (server: {account.account_server}): " +
                           account.account_name)

        msg.append("```")
        return "\n".join(msg)

    async def cmd_list_accounts(self, user_id, cmd_args):
        """
        Lists account for a specific source and optionally server

        Usage:
            {command_prefix}list_accounts acc_source [acc_server]
            Ex: {command_prefix}list_accounts azurlane sandy
        """

        async def help(self):
            msg = "```{0}```\n{1}".format(
                self._prettify_docstring(self.cmd_list_accounts.__doc__),
                await self.get_register_accounts_infos())
            return msg

        if len(cmd_args) == 1 and cmd_args[0] == "help":
            return await help(self)
        if len(cmd_args) < 1 or len(cmd_args) > 2:
            return "Invalid number of arguments.\n" + await help(self)

        input_acc_server = cmd_args[1].lower() if len(cmd_args) == 2 else None
        try:
            acc_source, acc_server = \
                self.check_and_get_account_source_and_server(
                    cmd_args[0], input_acc_server, allow_empty_serv=True)
        except exceptions.AccountSourceNotFoundException as e:
            return (f"Game/Website `{e.account_source}` not found.\n" +
                    "See help for a list of available game/websites")
        except exceptions.AccountHasNoServerWarning:
            return ("Warning: this game/website doesn't have any servers.\n" +
                    "Please relaunch the command without specifying a server")
        except exceptions.InvalidAccountServerException as e:
            msg = ("Server `{serv}` doesn't exist for `{src}`.\n" +
                   "List of servers for `{src}`: `{servers}`")
            return msg.format(serv=e.input_acc_server,
                              src=e.account_source,
                              servers=e.account_servers)

        accounts = db_manager.get_accounts_for_source_and_server(
            account_source=acc_source,
            account_server=acc_server)

        if not accounts:
            msg = f"No accounts for {acc_source}"
            if len(cmd_args) == 2:
                msg += f" in server {acc_server}"
            return msg

        users_cache = dict()
        msg = list()
        msg.append(f"Accounts for {acc_source}:```")
        prev_server = None
        for account in accounts:
            if account.discord_user_id not in users_cache:
                users_cache[account.discord_user_id] = await self.fetch_user(
                    account.discord_user_id)
            if account.account_server != prev_server:
                msg.append(f"--- Server {account.account_server} ---")
                prev_server = account.account_server
            msg.append("{discord_user}: {acc}".format(
                discord_user=users_cache[account.discord_user_id],
                acc=account.account_name))

        msg.append("```")
        return "\n".join(msg)

    async def cmd_remove_all_accounts(self, user_id, cmd_args):
        """
        Removes all accounts linked to your profile from the game/website/server you entered

        Usage:
            {command_prefix}remove_all_accounts acc_source [acc_server]
            Ex: {command_prefix}remove_all_accounts azurlane sandy
        """
        async def help(self):
            msg = "```{0}```\n{1}".format(
                self._prettify_docstring(self.cmd_remove_all_accounts.__doc__),
                await self.get_register_accounts_infos())
            return msg

        if len(cmd_args) < 1 or len(cmd_args) > 2:
            return "Invalid number of arguments.\n" + await help(self)

        input_acc_server = cmd_args[1].lower() if len(cmd_args) == 2 else None

        try:
            acc_source, acc_server = \
                self.check_and_get_account_source_and_server(cmd_args[0],
                                                             input_acc_server)
        except exceptions.AccountSourceNotFoundException as e:
            return (f"Game/Website `{e.account_source}` not found.\n" +
                    "See help for a list of available game/websites")
        except exceptions.AccountHasNoServerWarning:
            return ("Warning: this game/website doesn't have any servers.\n" +
                    "Please relaunch the command without specifying a server")
        except exceptions.AccountServerRequiredException:
            return "You need to enter a server for this game/website."
        except exceptions.InvalidAccountServerException as e:
            msg = ("Server `{serv}` doesn't exist for `{src}`.\n" +
                   "List of servers for `{src}`: `{servers}`")
            return msg.format(serv=e.input_acc_server,
                              src=e.account_source,
                              servers=e.account_servers)

        nb_removed = db_manager.remove_server_accounts_for_user(
            discord_user_id=user_id,
            account_source=acc_source,
            account_server=acc_server)
        return f"{nb_removed} account(s) successfully deleted."

    async def cmd_remove_account(self, user_id, cmd_args):
        """
        Removes one specific account linked to your profile.

        Usage:
            {command_prefix}remove_accounts acc_source [acc_server] acc_name
            Ex: {command_prefix}remove_all_accounts azurlane sandy yourname
        """
        async def help(self):
            msg = "```{0}```".format(
                self._prettify_docstring(self.cmd_remove_account.__doc__))
            return msg

        if len(cmd_args) < 2 or len(cmd_args) > 3:
            return "Invalid number of arguments.\n" + await help(self)

        input_acc_server = cmd_args[1].lower() if len(cmd_args) == 3 else None

        try:
            acc_source, acc_server = \
                self.check_and_get_account_source_and_server(cmd_args[0],
                                                             input_acc_server)
        except exceptions.AccountSourceNotFoundException as e:
            return (f"Game/Website `{e.account_source}` not found.\n" +
                    "See help for a list of available game/websites")
        except exceptions.AccountHasNoServerWarning:
            return ("Warning: this game/website doesn't have any servers.\n" +
                    "Please relaunch the command without specifying a server")
        except exceptions.AccountServerRequiredException:
            return "You need to enter a server for this game/website."
        except exceptions.InvalidAccountServerException as e:
            msg = ("Server `{serv}` doesn't exist for `{src}`.\n" +
                   "List of servers for `{src}`: `{servers}`")
            return msg.format(serv=e.input_acc_server,
                              src=e.account_source,
                              servers=e.account_servers)

        nb_removed = db_manager.remove_account(
            discord_user_id=user_id,
            account_source=acc_source,
            account_server=acc_server,
            account_name=cmd_args[-1])
        if nb_removed == 1:
            return "Account successfully deleted."
        return "No account with this name found."

    async def cmd_add_role(self, user, cmd_args):
        """
        Adds a new role to your profile on this server

        Usage:
            {command_prefix}add_role new_role
            Ex: {command_prefix}add_role azurlane
        """
        async def help(self):
            msg = "```{0}```\n{1}".format(
                self._prettify_docstring(self.cmd_add_role.__doc__),
                await self.get_assignable_roles())
            return msg

        if len(cmd_args) != 1:
            return "Invalid number of arguments.\n" + await help(self)
        if cmd_args[0] == "help":
            return await help(self)

        if cmd_args[0] not in self.cmd_cfg.roles:
            return "Unknown role `{role}`.{assignable_roles}\n".format(
                role=cmd_args[0],
                assignable_roles=await self.get_assignable_roles())

        role = self.get_role_from_guild(user.guild, cmd_args[0])

        if role in user.roles:
            return "Role already assigned."
        try:
            await user.add_roles(role)
        except discord.Forbidden:
            return "Invalid bot permissions. Please contact administrator."
        except Exception as e:
            logger = logging.getLogger("haruhichanbot")
            logger.error("Exception in cmd_add_role\n" +
                         "Msg={0}\nArgs={1}".format(e, cmd_args))
            return "An unknown error happened, please contact administrator."
        return "Role `{0}` successfully added!".format(cmd_args[0])

    async def get_assignable_roles(self):
        """
        Returns a human-readable string of every assignable role
        with their description.
        """
        msg = list()
        msg.append("```Roles:")
        for role, role_desc in self.cmd_cfg.roles.items():
            msg.append("\t- {role} ({title}) - {desc}".format(
                role=role, title=role_desc["title"],
                desc=role_desc["description"]))
        msg.append("```")
        return "\n".join(msg)

    def get_role_from_guild(self, guild, role_name):
        """
        Returns the Discord Role object from the guild and the role's name
        Also caches the value
        """
        role_desc = self.cmd_cfg.roles[role_name]
        if "cached_discord_role" not in role_desc:
            role = guild.get_role(role_desc["id"])
            if not role:
                logger = logging.getLogger("haruhichanbot")
                logger.error(
                    f"An invalid role {role_name} is in " +
                    "the commands settings file.")
                return (f"Invalid role `{role_name}`." +
                        " Please contact administrator.")
            role_desc["cached_discord_role"] = role
        return role_desc["cached_discord_role"]

    async def cmd_remove_role(self, user, cmd_args):
        """
        Removes a role from your profile on this server

        Usage:
            {command_prefix}remove_role new_role
            Ex: {command_prefix}remove_role azurlane
        """
        async def help(self):
            msg = "```{0}```\n{1}".format(
                self._prettify_docstring(self.cmd_remove_role.__doc__),
                await self.get_assignable_roles())
            return msg

        if len(cmd_args) != 1:
            return "Invalid number of arguments.\n" + await help(self)
        if cmd_args[0] == "help":
            return await help(self)

        if cmd_args[0] not in self.cmd_cfg.roles:
            return "Unknown role `{role}`.{assignable_roles}\n".format(
                role=cmd_args[0],
                assignable_roles=await self.get_assignable_roles())

        role = self.get_role_from_guild(user.guild, cmd_args[0])

        if role not in user.roles:
            return "This role is not assigned to your profile."
        try:
            await user.remove_roles(role)
        except discord.Forbidden:
            return "Invalid bot permissions. Please contact administrator."
        except Exception as e:
            logger = logging.getLogger("haruhichanbot")
            logger.error("Exception in cmd_remove_role\n" +
                         "Msg={0}\nArgs={1}".format(e, cmd_args))
            return "An unknown error happened, please contact administrator."
        return "Role `{0}` successfully removed!".format(cmd_args[0])
