from curse import rule_types, curse, create_rule_from_type
from enum import IntEnum
import conversation_utils
import file_utils
import user_metadata
import time
import curse_vote_database
import curse_utils

class conversation_base():
	"""Template for all other conversations, must be inherited"""

	conversation_manager = None

	def __init__(self, user):
		self.user = user
		self.callback = self.no_callback_set
		self.parent_conversation = None
		self.last_update_time = time.time()

	async def start_conversation(self):
		conversation_base.conversation_manager.start_conversation(self)
	
	async def stop_conversation(self, child_callback_result = None):
		conversation_base.conversation_manager.stop_conversation(self.user.id)
		if self.parent_conversation:
			conversation_base.conversation_manager.start_conversation(self.parent_conversation)
			if child_callback_result: await child_callback_result()
	
	async def switch_to_next_conversation(self, next_conversation):
		await self.stop_conversation()
		await next_conversation.start_conversation()
	
	async def start_nested_conversation(self, next_conversation):
		next_conversation.parent_conversation = self
		await next_conversation.start_conversation()

	async def send_user_message(self, message_to_send):
		self.last_update_time = time.time()
		await self.user.send(message_to_send)
	
	async def on_receive_message(self, message):
		self.last_update_time = time.time()
		await self.callback(message)

	def set_next_callback(self, callback):
		self.callback = callback
	
	async def no_callback_set(self, message):
		await self.send_user_message("Whoops... something went wrong, exiting conversation.")
		await self.stop_conversation()

class conversation_main_menu(conversation_base):
	"""Contains logic for the main menu, flowing into different types of conversations from there"""
	
	class menu_options(IntEnum):
		BROWSE_OWN = 1				# Done
		BROWSE_FAVORITES = 2		# Done
		BROWSE_POPULAR = 3			# Done
		BROWSE_BY_USER = 4			# Done
		BROWSE_BY_SERVER = 5		# Not implemented
		CREATE_CURSE = 6			# Done
		DISABLE_ACTIVE_CURSE = 7	# Done

	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		menu_options_string = conversation_utils.get_enum_options(conversation_main_menu.menu_options, { 0: "Curse browsing", 4: "Curse management"})
		message_to_send = "What would you like to do?\n" + menu_options_string + "Reply with the number."
		await self.send_user_message(message_to_send)
		self.set_next_callback(self.on_selection_received)
	
	async def on_selection_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return
		
		selection = int(message.content)
		if selection == conversation_main_menu.menu_options.CREATE_CURSE:
			await self.switch_to_next_conversation(conversation_create_curse(self.user))

		elif selection == conversation_main_menu.menu_options.DISABLE_ACTIVE_CURSE:
			await self.switch_to_next_conversation(conversation_disable_active_curse(self.user))

		elif selection == conversation_main_menu.menu_options.BROWSE_POPULAR:
			await self.switch_to_next_conversation(conversation_browse_by_popular(self.user))

		elif selection == conversation_main_menu.menu_options.BROWSE_BY_USER:
			await self.switch_to_next_conversation(conversation_browse_by_user(self.user))

		elif selection == conversation_main_menu.menu_options.BROWSE_OWN:
			await self.switch_to_next_conversation(conversation_util_show_user_curses(self.user, self.user.id))
		
		elif selection == conversation_main_menu.menu_options.BROWSE_FAVORITES:
			await self.switch_to_next_conversation(conversation_browse_favorite_curses(self.user))

# ==================================================================================
# =	Curse management
# ==================================================================================
class conversation_disable_active_curse(conversation_base):
	"""Disables the active curse"""
	
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()

		message_to_send = ""
		if not user_metadata.is_curse_enabled(self.user):
			message_to_send = "You have no curse enabled."
		else:
			user_metadata.set_curse_disabled(self.user)
			message_to_send = "Curse disabled."
		
		await self.send_user_message(message_to_send)
		await self.stop_conversation()
	
	async def on_curse_name_received(self, message):
		curse_name = message.content.lower().replace(" ", "_")
		user_metadata.set_curse_enabled(self.user, self.user.id, curse_name)

		message_to_send = "Curse activated: ***" + curse_name + "***"
		await self.user.send(message_to_send)
		await self.stop_conversation()

class conversation_create_curse(conversation_base):
	"""Creates a curse, then flows into `conversation_add_curse_rule`"""
	
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		await self.send_user_message("Let's start creating a new curse.\n\nWhat would you like to name your curse?")
		self.set_next_callback(self.on_curse_name_received)
	
	async def on_curse_name_received(self, message):
		curse_name = message.content.lower().replace(" ", "_")
		new_curse = curse(curse_name)

		message_to_send = "Creating new curse called: ***" + curse_name + "***\n\n"
		await self.user.send(message_to_send)
		await self.switch_to_next_conversation(conversation_add_curse_rule(self.user, new_curse))

class conversation_use_curse(conversation_base):
	"""Use a given curse and convert a message"""
	
	def __init__(self, user, curse):
		super().__init__(user)
		self.curse = curse

	async def start_conversation(self):
		await super().start_conversation()
		await self.send_user_message("What would you like to ***" + self.curse.name + "***-ify?")
		self.set_next_callback(self.on_curse_message_received)
	
	async def on_curse_message_received(self, message):
		await self.user.send(self.curse.parse(message.content))
		await self.stop_conversation()

class conversation_add_curse_rule(conversation_base):
	"""Starts a loop for adding rules to a given curse"""
	
	def __init__(self, user, curse):
		super().__init__(user)
		self.curse = curse

	async def start_conversation(self):
		await super().start_conversation()
		await self.start_new_rule_flow()

	async def start_new_rule_flow(self):
		rule_options = conversation_utils.get_enum_options(rule_types)
		message_to_send = "What type of rule would you like to add?\n" + rule_options + "Reply with the number."

		author = self.user
		await author.send(message_to_send)

		self.set_next_callback(self.on_curse_rule_received)

	async def on_curse_rule_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return

		new_rule = create_rule_from_type(int(message.content))
		if not new_rule:
			await self.user.send("Input `" + message.content + "` is not a valid option.")
			return

		await new_rule.request_parameters(self, self.on_curse_rule_params_set)

	async def on_curse_rule_params_set(self, new_rule):
		self.curse.rules.append(new_rule)

		curse_description = self.curse.get_rules_descriptions()
		yes_no_prompt_conversation = conversation_util_yes_no_prompt(
			self.user,
			curse_description + "\nWould you like to add another rule?",
			self.on_add_rule_yes,
			self.on_add_rule_no)
		await self.start_nested_conversation(yes_no_prompt_conversation)

	async def on_add_rule_yes(self):
		await self.start_new_rule_flow()

	async def on_add_rule_no(self):
		curse = self.curse
		file_utils.create_file_for_user(self.user, curse.name + ".json", curse.get_json_string())
		await self.send_user_message("New curse ***" + curse.name + "*** is saved.")
		await self.switch_to_next_conversation(conversation_main_menu(self.user))

# ==================================================================================
# =	Browsing
# ==================================================================================
class conversation_browse_by_popular(conversation_base):
	"""Browse a list of the most popular curses"""
	
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		await self.switch_to_next_conversation(conversation_util_show_curses(self.user, curse_vote_database.get_highest_voted_curses(10)))

class conversation_browse_by_user(conversation_base):
	"""Browse a list of user's curses"""
	
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		await self.send_user_message("Enter the ID of the user you'd like to browse.")
		self.set_next_callback(self.on_user_message_received)
	
	async def on_user_message_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return
		
		await self.switch_to_next_conversation(conversation_util_show_user_curses(self.user, int(message.content)))

class conversation_browse_favorite_curses(conversation_base):
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		await self.switch_to_next_conversation(conversation_util_show_curses(self.user, user_metadata.get_favorite_curses(self.user)))

# ==================================================================================
# =	Utilities
# ==================================================================================
class conversation_util_yes_no_prompt(conversation_base):
	"""Sends a yes/no prompt and calls a callback when an option is selected"""
	
	class yes_no_prompt_options(IntEnum):
		YES = 1
		NO = 2

	def __init__(self, user, message, on_yes_selected, on_no_selected):
		super().__init__(user)
		self.message = message
		self.on_yes_selected = on_yes_selected
		self.on_no_selected = on_no_selected

	async def start_conversation(self):
		await super().start_conversation()
		await self.send_user_message(self.message + "\n" + conversation_utils.get_enum_options(self.yes_no_prompt_options))
		self.set_next_callback(self.on_answer_received)
	
	async def on_answer_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return
		
		reply = int(message.content)
		if reply == conversation_util_yes_no_prompt.yes_no_prompt_options.YES:
			await self.stop_conversation(self.on_yes_selected)
		elif reply == conversation_util_yes_no_prompt.yes_no_prompt_options.NO:
			await self.stop_conversation(self.on_no_selected)
		else:
			await self.send_user_message(message.content + " is not a valid option.")

class conversation_util_show_user_curses(conversation_base):
	class curse_options(IntEnum):
		USE_CURSE = 1
		EDIT_CURSE = 2,
		DELETE_CURSE = 3,


	def __init__(self, user, user_id):
		super().__init__(user)
		self.browsing_user_id = user_id
	
	async def start_conversation(self):
		await super().start_conversation()
		
		files_for_user = file_utils.get_files_for_user_id(self.browsing_user_id)
		if len(files_for_user) <= 0:
			await self.user.send("User with ID `" + str(self.browsing_user_id) + "` does not have any curses.")
			await self.stop_conversation()
			return
		
		curse_id_list = []
		for file_name in files_for_user:
			curse_id_list.append(curse_utils.get_curse_id(self.browsing_user_id, file_name.replace(".json", "")))
		
		await self.switch_to_next_conversation(conversation_util_show_curses(self.user, curse_id_list))

class conversation_util_show_curses(conversation_base):
	class curse_options(IntEnum):
		USE_CURSE = 1
		EDIT_CURSE = 2,
		DELETE_CURSE = 3,


	def __init__(self, user, curse_id_list):
		super().__init__(user)
		self.curse_metadata = []
		self.curse_list = []
		for curse_id in curse_id_list:
			user_id = curse_utils.get_user_from_curse_id(curse_id)
			curse_name = curse_utils.get_name_from_curse_id(curse_id)
			self.curse_metadata.append({
				"user_id": user_id,
				"curse_id": curse_id
			})
			self.curse_list.append(user_metadata.get_curse_instance(user_id, curse_name))
	
	async def start_conversation(self):
		await super().start_conversation()
		
		self.display_names = []
		self.curse_names = []
		for curse_instance in self.curse_list:
			self.curse_names.append(curse_instance.name)
			self.display_names.append(curse_instance.name.replace("_", " ").title())
		
		await self.send_user_message("Which curse would you like to interact with?\n" + conversation_utils.get_list_options(self.display_names))
		self.set_next_callback(self.on_curse_message_received)

	async def on_curse_message_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return

		curse_choice = int(message.content) - 1
		self.selected_curse_data = {
			"instance": self.curse_list[curse_choice],
			"name": self.curse_names[curse_choice],
			"display_name": self.display_names[curse_choice],
			"user_id": self.curse_metadata[curse_choice]["user_id"],
			"curse_id": self.curse_metadata[curse_choice]["curse_id"],
		}

		self.curse_scores = curse_vote_database.get_curse_scores(self.selected_curse_data["curse_id"])
		message_to_send = "Selected: ***" + self.selected_curse_data["display_name"] + "***\n"
		message_to_send = message_to_send + "Score: " + str(self.curse_scores["total"]) + " (" + str(len(self.curse_scores["upvotes"])) + "/" + str(len(self.curse_scores["downvotes"])) + ")\n"

		options_list = [ "Use curse",				# 1 - DONE
						"Show details",				# 2 - DONE
						"Curse message" ] 			# 3 - DONE
		
		if self.selected_curse_data["user_id"] == self.user.id:
			options_list.append("Edit curse") 		# 4 - NOT IMPLEMENTED
			options_list.append("Delete curse") 	# 5 - DONE
		
		else:
			options_list.append("Mark as favorite") # 4 - DONE
			options_list.append("Vote up") 			# 5 - DONE
			options_list.append("Vote down") 		# 6 - DONE
		
		message_to_send = message_to_send + conversation_utils.get_list_options(options_list)
		await self.user.send(message_to_send)
		self.set_next_callback(self.on_curse_option_received)
	
	async def on_curse_option_received(self, message):
		if await curse_utils.is_string_int(message.content, self.user) == False:
			return
		
		curse_choice = int(message.content)
		if curse_choice == 1: # Enable curse
			user_metadata.set_curse_enabled(self.user, self.selected_curse_data["user_id"], self.selected_curse_data["name"])
			await self.user.send("Enabled curse `" + self.selected_curse_data["display_name"] + "`")
			await self.stop_conversation()
			return
		
		elif curse_choice == 2: # Show details
			curse_description = self.selected_curse_data["instance"].get_rules_descriptions()
			await self.user.send("Details for curse ***" + self.selected_curse_data["display_name"] + "***\n\n" + curse_description)
			await self.stop_conversation()
			return

		elif curse_choice == 3: # Use curse
			await self.switch_to_next_conversation(conversation_use_curse(self.user, self.selected_curse_data["instance"]))
			return
		
		if self.selected_curse_data["user_id"] == self.user.id:
			if curse_choice == 5:
				file_utils.delete_file_for_user(self.user, self.selected_curse_data["name"] + ".json")
				await self.user.send("Curse removed.")
				await self.stop_conversation()
				return
		
		else:
			if curse_choice == 4:
				user_metadata.set_favorite_curse(self.user, self.selected_curse_data["curse_id"])
				await self.user.send("Set curse as favorite!")
				await self.stop_conversation()
				return

			elif curse_choice == 5:
				curse_vote_database.vote_up(self.selected_curse_data["curse_id"], self.user.id)
				await self.user.send("Voted up!")
				await self.stop_conversation()
				return
			
			elif curse_choice == 6:
				curse_vote_database.vote_down(self.selected_curse_data["curse_id"], self.user.id)
				await self.user.send("Voted down!")
				await self.stop_conversation()
				return