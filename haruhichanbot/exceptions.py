# Custom base class for exceptions and warnings
class HaruhiChanBotException(Exception):
    pass


class DuplicateDbEntryWarning(HaruhiChanBotException):
    pass


class NoAccountSourceInfosException(HaruhiChanBotException):
    pass


class AccountSourceNotFoundException(HaruhiChanBotException):
    def __init__(self, account_source, msg=None):
        self.msg = (f"Game/Website `{account_source}` not found.\n" +
                    "See help for a list of available game/websites")
        if msg:
            self.msg = msg
        super().__init__(self, self.msg)
        self.account_source = account_source

    def __str__(self):
        return self.msg


class AccountHasNoServerWarning(HaruhiChanBotException):
    def __init__(self, msg=None):
        super().__init__(self, msg)
        self.msg = ("Warning: this game/website doesn't have any servers.\n" +
                    "Please relaunch the command without specifying a server")
        if msg:
            self.msg = msg

    def __str__(self):
        return self.msg


class AccountServerRequiredException(HaruhiChanBotException):
    def __init__(self, msg=None):
        super().__init__(self, msg)
        self.msg = "You need to enter a server for this game/website."
        if msg:
            self.msg = msg

    def __str__(self):
        return self.msg


class InvalidAccountServerException(HaruhiChanBotException):
    def __init__(self, input_acc_server, account_source, account_servers,
                 msg=None):
        self.input_acc_server = input_acc_server
        self.account_source = account_source
        self.account_servers = account_servers

        self.msg = ("Server `{serv}` doesn't exist for `{src}`.\n" +
                    "List of servers for `{src}`: `{servers}`")
        self.msg = self.msg.format(serv=self.input_acc_server,
                                   src=self.account_source,
                                   servers=self.account_servers)
        if msg:
            self.msg = msg

    def __str__(self):
        return self.msg
