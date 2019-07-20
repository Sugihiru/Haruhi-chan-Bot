# Custom base class for exceptions and warnings
class HaruhiChanBotException(Exception):
    pass


class DuplicateDbEntryWarning(HaruhiChanBotException):
    pass
