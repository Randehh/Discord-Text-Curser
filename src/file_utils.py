import os

class file_utils():
	def get_user_folder(self, user):
		return "Custom_Curses/" + str(user.id)
		
	def create_folder_for_user(self, user):
		rootFolder = self.get_user_folder(user)
		if not os.path.exists(rootFolder):
			os.makedirs(rootFolder)
	
	def create_file_for_user(self, user, file_name, content):
		self.create_folder_for_user(user)
		
		fileNameWithFolder = self.get_user_folder(user) + "/" + file_name
		with open(fileNameWithFolder, 'w') as f:
			f.write(content)
	
	def read_file_for_user(self, user, file_name):
		fileNameWithFolder = self.get_user_folder(user) + "/" + file_name
		if not os.path.exists(fileNameWithFolder):
			return ""
		
		with open(fileNameWithFolder, 'r') as f:
			file_read_data = f.read()
			return file_read_data