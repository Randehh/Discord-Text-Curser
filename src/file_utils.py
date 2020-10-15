import os
import logging

def get_user_folder(user):
	"""Gets the root folder for a user."""
	return get_user_id_folder(user.id)

def get_user_id_folder(user_id):
	"""Gets the root folder for a user."""
	return "Curses/" + str(user_id)
	
def create_folder_for_user(user):
	"""Creates a personal folder for the given user if it does not exist."""
	rootFolder = get_user_folder(user)
	if not os.path.exists(rootFolder):
		os.makedirs(rootFolder)

def create_file_for_user(user, file_name, content):
	"""Creates a new file with the given name for a user."""
	create_folder_for_user(user)
	
	fileNameWithFolder = get_user_folder(user) + "/" + file_name
	with open(fileNameWithFolder, 'w') as f:
		f.write(content)

def read_file_for_user(user, file_name):
	"""Get the contents of the given file the user owns."""
	fileNameWithFolder = get_user_folder(user) + "/" + file_name
	return read_file_on_path(fileNameWithFolder)

def read_file_for_user_id(user_id, file_name):
	fileNameWithFolder = get_user_id_folder(user_id) + "/" + file_name
	return read_file_on_path(fileNameWithFolder)

def read_file_on_path(path):
	if not os.path.exists(path):
		return ""
	
	with open(path, 'r') as f:
		file_read_data = f.read()
		return file_read_data

def get_files_for_user_id(user_id):
	return os.listdir(get_user_id_folder(user_id))

def delete_file_for_user(user, file):
	rootFolder = get_user_folder(user)
	delete_file(rootFolder + "/" + file)

def delete_file(file_path):
	if not os.path.exists(file_path):
		return False
	else:
		os.remove(file_path)
		return True