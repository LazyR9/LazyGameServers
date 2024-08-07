import importlib
from typing import Any

CURRENT_VERSION = 1

_module_cache = {}

def upgrade(manager: 'app.management.manager.ServerManager', config_dict: dict[str, Any]):
    """
    Attempts to upgrade the server manager to the latest format version.
    
    `config_dict` is a dictionary containing the loaded config, this will be edited in place during the upgrade,
    where it will then be used to populate the `Config` class.

    :param manager: The ServerManager that should be upgraded
    :param config_dict: The current config as a dictionary
    :raises ValueError: When the config version is newer than the current version
    :raises ModuleNotFoundError: An update script could not be found, i.e. upgrade_v1_to_v2.py
    """
    config_version = config_dict["version"]

    # if not isinstance(config_version, int):
    #     raise TypeError("Version is not a valid int!")
    # Config is already on current version, do nothing
    if config_version == CURRENT_VERSION:
        return
    # Config has a new version, we don't support automatic downgrades
    if config_version > CURRENT_VERSION:
        raise ValueError("Config is a newer version!")
    for upgrade_version in range(config_version, CURRENT_VERSION):
        module_name = f"upgrade_v{upgrade_version}_to_v{upgrade_version+1}"
        if module_name not in _module_cache:
            try:
                _module_cache[module_name] = importlib.import_module(f"app.management.upgrades.{module_name}")
            except ModuleNotFoundError as error:
                raise ModuleNotFoundError(f"Can't find a {module_name}.py file in upgrades, please create it to handle upgrades!") from error
        module = _module_cache[module_name]
        module.upgrade(manager, config_dict)
        config_dict["version"] += 1

# circular imports strike once again
import app.management.manager