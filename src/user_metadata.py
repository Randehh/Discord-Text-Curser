from curse import curse
import json
import file_utils
import curse_utils
import time

FILE_LOCATION = "User_Data"
MAXIMUM_BACKUP_COUNT = 24

user_data = {}
curse_instances = {}

def verify_user_table(user_id):
	if not user_id in user_data:
		user_data[user_id] = {
			"enabled_curse": { "enabled": False },
			"favorite_curses": set()
		}

def get_curse_instance(user_id, curse_name):
	verify_user_table(user_id)

	curse_id = curse_utils.get_curse_id(user_id, curse_name)
	if curse_id in curse_instances:
		return curse_instances[curse_id]
	
	new_curse_instance = curse(curse_name)
	file_data = file_utils.read_file_for_user_id(user_id, curse_name + ".json")
	json_data = json.loads(file_data)
	new_curse_instance.create_from_json(json_data)
	curse_instances[curse_id] = new_curse_instance
	return new_curse_instance

# Enabled curses
def set_curse_enabled(user, owner_user_id, curse_name):
	verify_user_table(user.id)

	user_data[user.id]["enabled_curse"] = {
		"enabled": True,
		"curse_name": curse_name,
		"owner_user_id": owner_user_id
	}

def set_curse_disabled(user):
	verify_user_table(user.id)

	user_data[user.id]["enabled_curse"]["enabled"] = False

def is_curse_enabled(user):
	verify_user_table(user.id)

	return user_data[user.id]["enabled_curse"]["enabled"]

def get_enabled_curse(user):
	verify_user_table(user.id)

	if is_curse_enabled(user) == True:
		enabled_curse = user_data[user.id]["enabled_curse"]
		return get_curse_instance(enabled_curse["owner_user_id"], enabled_curse["curse_name"])
	return None

# Favorite curses
def get_favorite_curses(user):
	verify_user_table(user.id)

	if not "favorite_curses" in user_data[user.id]:
		return set()
	
	return user_data[user.id]["favorite_curses"]

def set_favorite_curse(user, curse_id):
	verify_user_table(user.id)

	if not "favorite_curses" in user_data[user.id]:
		user_data[user.id]["favorite_curses"] = set()
	
	user_data[user.id]["favorite_curses"].add(curse_id)

def remove_favorite_curse(user, curse_id):
	verify_user_table(user.id)

	if not "favorite_curses" in user_data[user.id]:
		return
	
	user_data[user.id]["favorite_curses"].discard(curse_id)

#File management
def load_latest():
	file_utils.create_folder_on_path(FILE_LOCATION)
	lastest_file = file_utils.get_latest_in_folder(FILE_LOCATION)
	if lastest_file:
		load_specific(lastest_file)

def load_specific(voting_file_name):
	file_utils.create_folder_on_path(FILE_LOCATION)
	file_path = FILE_LOCATION + "/" + voting_file_name
	file_data = file_utils.read_file_on_path(file_path)
	json_data = json.loads(file_data)
	
	loaded_object = {}
	for user_id in json_data:
		loaded_object[int(user_id)] = {
			"enabled_curse": json_data[user_id]["enabled_curse"],
			"favorite_curses": set(json_data[user_id]["favorite_curses"])
		}

	global user_data
	user_data = loaded_object

def save_backup():
	file_utils.create_folder_on_path(FILE_LOCATION)

	converted_data = {}
	for user_id in user_data:
		converted_data[user_id] = {
			"enabled_curse": user_data[user_id]["enabled_curse"],
			"favorite_curses": list(user_data[user_id]["favorite_curses"])
		}
	
	json_data = json.dumps(converted_data)
	file_utils.create_file_on_path(FILE_LOCATION + "/" + str(time.time()) + ".json", json_data)

	#Check for limit
	files = file_utils.get_files_in_folder(FILE_LOCATION)
	if len(files) <= MAXIMUM_BACKUP_COUNT:
		return
	
	file_count_to_remove = len(files) - MAXIMUM_BACKUP_COUNT
	for i in range(file_count_to_remove):
		file_utils.delete_file_on_path(FILE_LOCATION + "/" + files[i])