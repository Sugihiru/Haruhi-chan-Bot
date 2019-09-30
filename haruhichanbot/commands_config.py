import json

from . import exceptions


class CommandsConfig():
    def __init__(self, json_cfg_file=None):
        if not json_cfg_file:
            json_cfg_file = CommandsConfigDefaults.json_cfg_file
        self.json_cfg_file = json_cfg_file

        with open(self.json_cfg_file, "r") as f:
            cfg_json = json.load(f)
        self.account_sources = cfg_json["account_sources"]
        self.roles = cfg_json["roles"]

    def get_account_source_infos(self, account_source):
        """
        Returns the real name and the informations of the account_source
        Also manages account sources aliases
        Raises exception.NoAccountSourceInfosException if no infos were found
        """
        for source, source_infos in self.account_sources.items():
            if account_source.lower() == source.lower():
                return (source, source_infos)
            if source_infos["aliases"]:
                for alias in source_infos["aliases"]:
                    if account_source.lower() == alias.lower():
                        return (source, source_infos)
        raise exceptions.NoAccountSourceInfosException()


class CommandsConfigDefaults():
    """Default configuration values"""
    json_cfg_file = "config/commands_settings.json"


if __name__ == '__main__':
    cfg = CommandsConfig()
    print(cfg.get_account_source_infos("al"))
    print(cfg.roles.keys())
