import file_utils
import time
import json

FILE_LOCATION = "Voting"
MAXIMUM_BACKUP_COUNT = 24

voting_table = {}

# Voting
def vote_up(curse_id, user_id):
    verify_curse_table(curse_id)    
    voting_table[curse_id]["upvotes"].add(user_id)
    voting_table[curse_id]["downvotes"].discard(user_id)
    update_vote_score(curse_id)

def vote_down(curse_id, user_id):
    verify_curse_table(curse_id)    
    voting_table[curse_id]["downvotes"].add(user_id)
    voting_table[curse_id]["upvotes"].discard(user_id)
    update_vote_score(curse_id)

def update_vote_score(curse_id):
    voting_table[curse_id]["total"] = len(voting_table[curse_id]["upvotes"]) - len(voting_table[curse_id]["downvotes"])

def verify_curse_table(curse_id):
    if not curse_id in voting_table:
        voting_table[curse_id] = {
            "upvotes": set(),
            "downvotes": set()
        }

def get_curse_scores(curse_id):
    verify_curse_table(curse_id)
    update_vote_score(curse_id)
    return voting_table[curse_id]

def get_highest_voted_curses(curse_count):
    current_count = 0
    curse_list = []
    for key in sorted(voting_table, key = lambda curse_id: voting_table[curse_id]["total"]):
        curse_list.append(key)
        current_count = current_count + 1
        if current_count == curse_count:
            return curse_list
    
    return curse_list

# File management
def load_latest():
    files = file_utils.get_files_in_folder(FILE_LOCATION)
    if len(files) == 0:
        return
    
    files.sort()
    load_specific(files[len(files) - 1])

def load_specific(voting_file_name):
    file_path = FILE_LOCATION + "/" + voting_file_name
    file_data = file_utils.read_file_on_path(file_path)
    json_data = json.loads(file_data)
    loaded_object = {}
    for curse_id in json_data:
        loaded_object[curse_id] = {
            "upvotes": set(json_data[curse_id]["upvotes"]),
            "downvotes": set(json_data[curse_id]["downvotes"])
        }
    
    global voting_table
    voting_table = loaded_object

def save_backup():
    # Convert set to list
    object_to_save = {}
    for curse_id in voting_table:
        object_to_save[curse_id] = {
            "upvotes": list(voting_table[curse_id]["upvotes"]),
            "downvotes": list(voting_table[curse_id]["downvotes"])
        }
    json_data = json.dumps(object_to_save)
    file_utils.create_file_on_path(FILE_LOCATION + "/" + str(time.time()) + ".json", json_data)

    #Check for limit
    files = file_utils.get_files_in_folder(FILE_LOCATION)
    if len(files) <= MAXIMUM_BACKUP_COUNT:
        return
    
    file_count_to_remove = len(files) - MAXIMUM_BACKUP_COUNT
    for i in range(file_count_to_remove):
        file_utils.delete_file_on_path(FILE_LOCATION + "/" + files[i])