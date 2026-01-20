import discord
from discord.ext import commands
import os
import yaml
from pathlib import Path



ROOT_DIR = Path(__file__).parents[2]
DEFAULT_CONFIGS_DIR = ROOT_DIR / "components" / "resources" / "default_configs"

from components.function.logging import log
from components.function.savedata import set_guild_attribute, get_guild_attribute

COG_LABELS = []
COG_CONFIGS = {}

CONFIG_REGISTRY = {}

class TupleLoader(yaml.SafeLoader):
    pass

def tuple_constructor(loader, node):
    return tuple(loader.construct_sequence(node))

TupleLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SEQUENCE_TAG,
    tuple_constructor
)
def tuple_representer(dumper, data):
    return dumper.represent_list(data)

yaml.SafeDumper.add_representer(tuple, tuple_representer)

def register_config(label: str):
    COG_LABELS.append(label)    

def get_default_config(config_name: str):
    if not config_name in COG_LABELS:
        raise ValueError(f"config {config_name} is not registered")
    
    path = DEFAULT_CONFIGS_DIR / f"{config_name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"config file {config_name} is registered but has no file")
    with path.open("r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=TupleLoader) or {}
    return config

class ConfigHandler:

    """generic config handler for all guild-level configs"""

    def __init__(self, label: str, guild: discord.Guild):

        self.label = label
        self.guild = guild
        self.guild_id = guild.id
        self.guild_name = guild.name
        self.config = None

    def register_object(self):
        """registers the object in the config registry"""
        if self.label not in CONFIG_REGISTRY:
            CONFIG_REGISTRY[self.label] = {}
        CONFIG_REGISTRY[self.label][self.guild_id] = self

    def load_config(self):
        default_config = get_default_config(self.label)
        """loads the config for this guild."""
        config = get_guild_attribute(self.guild_id, self.label)
        if config is None:
            log(f"~1{self.guild_name} does not have attribute {self.label} config, using default settings...")
            config = default_config
        if isinstance(config, dict) and "colour" in config:
            colour = config["colour"]
            if isinstance(colour, list) and len(colour) == 3:
                config["colour"] = tuple(colour)
        self.default_config = default_config
        self.config = config

    def save_config(self):
        """saves the config for this guild."""
        set_guild_attribute(self.guild_id, key=self.label, value=self.config)
        log(f"~2saved levels config for {self.guild_name}")

    def get_attribute(self, attribute, fallback=None):
        """gets an attribute from the config, returns fallback if not found, default fallback is None"""
        if self.config is None:
            self.load_config()
        if attribute in self.config:
            try:
                return self.config[attribute]
            except Exception as e:
                log(f"~1error getting attribute {attribute} from config {self.label} for guild {self.guild_name}: {e}")
                return fallback
        else:
            if not fallback is None: # log only if fallback is provided
                #log(f"~1attribute {attribute} not found in config {self.label} for guild {self.guild_name}, returning fallback")
                # not logging now because its annoying me
                return fallback
            else:
                return fallback
    
    def get_nested_attribute(self, keys_dict_key, nested_key, fallback=None):
        """gets a nested attribute from a dict stored in the config. 
        For example: config[keys["levelup_message"]] where keys is a dict in the config."""
        if self.config is None:
            self.load_config()
        
        keys_dict = self.get_attribute(keys_dict_key, fallback={})
        if not isinstance(keys_dict, dict):
            log(f"~1{keys_dict_key} is not a dictionary in config {self.label} for guild {self.guild_name}")
            return fallback
            
        if nested_key in keys_dict:
            return keys_dict[nested_key]
        else:
            log(f"~1nested key {nested_key} not found in {keys_dict_key} for config {self.label} for guild {self.guild_name}, returning fallback")
            return fallback
        
    def set_attribute(self, attribute, value):
        """sets an attribute in the config. has no qualms about type validity, so check before calling."""
        if self.config is None:
            self.load_config()
        if attribute not in self.config: # ~3 is yellow (warning)
            log(f"~3attribute {attribute} not found in config {self.label}, it is being created.")
        self.config[attribute] = value
        self.save_config()