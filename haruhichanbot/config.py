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

        self.sql_infos = dict()
        self.sql_infos['username'] = parser.get("Credentials",
                                                "SqlUsername")
        self.sql_infos['password'] = parser.get("Credentials",
                                                "SqlPassword")
        self.sql_infos['host'] = parser.get("Credentials",
                                            "SqlHost")
        self.sql_infos['database'] = parser.get("Credentials",
                                                "SqlDatabase")
        self.sql_infos['port'] = parser.get("Credentials",
                                            "SqlPort")
        self.sql_infos['db_api'] = parser.get("Credentials",
                                              "SqlDbApi")


class ConfigDefaults():
    """Default configuration values"""
    config_file = "config/config.ini"
