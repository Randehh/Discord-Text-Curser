import os

class file_utils():
	def get_user_folder(self, user):
		"""Gets the root folder for a user."""

		return "Curses/" + str(user.id)
		
	def create_folder_for_user(self, user):
		"""Creates a personal folder for the given user if it does not exist."""

		rootFolder = self.get_user_folder(user)
		if not os.path.exists(rootFolder):
			os.makedirs(rootFolder)
	
	def create_file_for_user(self, user, file_name, content):
		"""Creates a new file with the given name for a user."""

		self.create_folder_for_user(user)
		
		fileNameWithFolder = self.get_user_folder(user) + "/" + file_name
		with open(fileNameWithFolder, 'w') as f:
			f.write(content)
	
	def read_file_for_user(self, user, file_name):
		"""Get the contents of the given file the user owns."""

		fileNameWithFolder = self.get_user_folder(user) + "/" + file_name
		if not os.path.exists(fileNameWithFolder):
			return ""
		
		with open(fileNameWithFolder, 'r') as f:
			file_read_data = f.read()
			return file_read_data