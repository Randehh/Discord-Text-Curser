from curse import rule_types, curse, create_rule_from_type
from enum import IntEnum
import conversation_utils
import file_utils
import user_metadata

class conversation_base():
	"""Template for all other conversations, must be inherited"""

	conversation_manager = None

	def __init__(self, user):
		self.user = user
		self.callback = self.no_callback_set
		self.parent_conversation = None

	async def start_conversation(self):
		conversation_base.conversation_manager.start_conversation(self)
	
	async def stop_conversation(self, child_callback_result = None):
		conversation_base.conversation_manager.stop_conversation(self.user)
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
		await self.user.send(message_to_send)
	
	async def on_receive_message(self, message):
		await self.callback(message)

	def set_next_callback(self, callback):
		self.callback = callback
	
	async def no_callback_set(self, message):
		await self.send_user_message("Whoops... something went wrong, exiting conversation.")
		await self.stop_conversation()

class conversation_main_menu(conversation_base):
	"""Contains logic for the main menu, flowing into different types of conversations from there"""
	
	class menu_options(IntEnum):
		CREATE_CURSE = 1
		EDIT_CURSE = 2
		REMOVE_CURSE = 3
		ENABLE_CURSE = 4
		DISABLE_CURSE = 5
		BROWSE_BY_USER = 6
		BROWSE_BY_SERVER = 7

	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		menu_options_string = conversation_utils.get_enum_options(conversation_main_menu.menu_options, { 0: "Curse management", 5: "Curse browsing"})
		message_to_send = "What would you like to do?\n" + menu_options_string + "Reply with the number."
		await self.send_user_message(message_to_send)
		self.set_next_callback(self.on_selection_received)
	
	async def on_selection_received(self, message):
		if await conversation_utils.is_string_int(message.content, self.user) == False:
			return
		
		selection = int(message.content)
		if selection == conversation_main_menu.menu_options.CREATE_CURSE:
			await self.switch_to_next_conversation(conversation_create_curse(self.user))
		elif selection == conversation_main_menu.menu_options.ENABLE_CURSE:
			await self.switch_to_next_conversation(conversation_enable_curse(self.user))
		elif selection == conversation_main_menu.menu_options.DISABLE_CURSE:
			user_metadata.set_curse_disabled(self.user)

class conversation_enable_curse(conversation_base):
	"""Enables a curse"""
	
	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		await self.send_user_message("Which curse would you like to activate?")
		self.set_next_callback(self.on_curse_name_received)
	
	async def on_curse_name_received(self, message):
		curse_name = message.content.lower().replace(" ", "_")
		user_metadata.set_curse_enabled(self.user, curse_name)

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
		if await conversation_utils.is_string_int(message.content, self.user) == False:
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
		if await conversation_utils.is_string_int(message.content, self.user) == False:
			return
		
		reply = int(message.content)
		if reply == conversation_util_yes_no_prompt.yes_no_prompt_options.YES:
			await self.stop_conversation(self.on_yes_selected)
		elif reply == conversation_util_yes_no_prompt.yes_no_prompt_options.NO:
			await self.stop_conversation(self.on_no_selected)
		else:
			await self.send_user_message(message.content + " is not a valid option.")