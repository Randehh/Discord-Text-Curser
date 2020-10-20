from curse import curse
import json
import file_utils
import curse_utils

enabled_curses = {}
curse_instances = {}

def get_curse_instance(user_id, curse_name):
    curse_id = curse_utils.get_curse_id(user_id, curse_name)
    if curse_id in curse_instances:
        return curse_instances[curse_id]
    
    new_curse_instance = curse(curse_name)
    file_data = file_utils.read_file_for_user_id(user_id, curse_name + ".json")
    json_data = json.loads(file_data)
    new_curse_instance.create_from_json(json_data)
    curse_instances[curse_id] = new_curse_instance
    return new_curse_instance

def set_curse_enabled(user, owner_user_id, curse_name):
    enabled_curses[user.id] = {
        "curse_name": curse_name,
        "owner_user_id": owner_user_id
    }

def set_curse_disabled(user):
    del enabled_curses[user.id]

def is_curse_enabled(user):
    return user.id in enabled_curses

def get_enabled_curse(user):
    if is_curse_enabled(user) == True:
        return get_curse_instance(enabled_curses[user.id]["owner_user_id"], enabled_curses[user.id]["curse_name"])
    return None