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

def vote_down(curse_id, user_id):
    verify_curse_table(curse_id)    
    voting_table[curse_id]["downvotes"].add(user_id)
    voting_table[curse_id]["upvotes"].discard(user_id)

def verify_curse_table(curse_id):
    if not curse_id in voting_table:
        voting_table[curse_id] = {
            "upvotes": set(),
            "downvotes": set()
        }

def get_curse_scores(curse_id):
    verify_curse_table(curse_id)
    curse_votes = voting_table[curse_id]
    upvotes = len(curse_votes["upvotes"])
    downvotes = len(curse_votes["downvotes"])
    return {
        "total": upvotes - downvotes,
        "upvotes": upvotes,
        "downvotes": downvotes
    }

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
    file_utils.create_file_on_path(FILE_LOCATION + "/" + str(time.time()), json_data)

    #Check for limit
    files = file_utils.get_files_in_folder(FILE_LOCATION)
    if len(files) <= MAXIMUM_BACKUP_COUNT:
        return
    
    file_count_to_remove = len(files) - MAXIMUM_BACKUP_COUNT
    for i in range(file_count_to_remove):
        file_utils.delete_file_on_path(FILE_LOCATION + "/" + files[i])