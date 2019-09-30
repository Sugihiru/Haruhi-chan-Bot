# Custom base class for exceptions and warnings
class HaruhiChanBotException(Exception):
    pass


class DuplicateDbEntryWarning(HaruhiChanBotException):
    pass


class NoAccountSourceInfosException(HaruhiChanBotException):
    pass


class AccountSourceNotFoundException(HaruhiChanBotException):
    def __init__(self, account_source):
        self.account_source = account_source


class AccountHasNoServerWarning(HaruhiChanBotException):
    pass


class AccountServerRequiredException(HaruhiChanBotException):
    pass


class InvalidAccountServerException(HaruhiChanBotException):
    def __init__(self, input_acc_server, account_source, account_servers):
        self.input_acc_server = input_acc_server
        self.account_source = account_source
        self.account_servers = account_servers
