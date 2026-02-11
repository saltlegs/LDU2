import time

from components.classes.confighandler import ConfigHandler

class InfractionTypes:
    NOTE   = 000
    WARN   = 100
    MUTE   = 200
    KICK   = 250
    BAN    = 300
    UNMUTE = 400
    UNBAN  = 500

def add_infraction(confighandler:ConfigHandler, user_id:int, infraction_type:int=InfractionTypes.NOTE, duration_seconds=-1, comment:str="no reason given") -> int:
    infractions:dict = confighandler.get_attribute("infractions", {})

    last_given_id:int = confighandler.get_attribute("last_given_id", -1)

    new_id = last_given_id + 1
    timestamp = time.time()

    infraction = [timestamp, user_id, infraction_type, duration_seconds, comment]

    infractions[new_id] = infraction

    confighandler.set_attribute("infractions", infractions)
    confighandler.set_attribute("last_given_id", new_id)

    return new_id

def get_infraction(confighandler:ConfigHandler, infraction_id:int) -> list | None:
    infractions_dict:dict = confighandler.get_attribute("infractions", {})
    
    return infractions_dict.get(infraction_id, None)
