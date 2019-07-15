import configparser


class Config():
    def __init__(self, config_file):
        if not config_file:
            config_file = ConfigDefaults.config_file
        self.config_file = config_file

        parser = configparser.ConfigParser()
        parser.read(config_file, encoding="utf-8")

        self.bot_token = parser.get("Credentials", "BotToken")
        self.command_prefix = parser.get(
            "Chat", "CommandPrefix")


class ConfigDefaults():
    """Default configuration values"""
    config_file = "config/config.ini"
