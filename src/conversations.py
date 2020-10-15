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

	async def start_conversation(self):
		conversation_base.conversation_manager.start_conversation(self)
	
	def stop_conversation(self):
		conversation_base.conversation_manager.stop_conversation(self.user)
	
	async def switch_to_next_conversation(self, next_conversation):
		self.stop_conversation()
		await next_conversation.start_conversation()

	async def send_user_message(self, message_to_send):
		await self.user.send(message_to_send)
	
	async def on_receive_message(self, message):
		await self.callback(message)

	def set_next_callback(self, callback):
		self.callback = callback
	
	async def no_callback_set(self, message):
		await self.send_user_message("Whoops... something went wrong, exiting conversation.")
		self.stop_conversation()

	def get_enum_options(self, enum):
		message = "```"
		for enum_value in enum:
			pretty_enum_name = enum_value.name.replace("_", " ").title()
			message = message + str(enum_value.value) + ":\t" + pretty_enum_name + "\n"
		return message + "```"

class conversation_main_menu(conversation_base):
	"""Contains logic for the main menu, flowing into different types of conversations from there"""
	
	class menu_options(IntEnum):
		CREATE_CURSE = 0
		EDIT_CURSE = 1
		REMOVE_CURSE = 2
		ENABLE_CURSE = 3
		DISABLE_CURSE = 4

	def __init__(self, user):
		super().__init__(user)

	async def start_conversation(self):
		await super().start_conversation()
		menu_options_string = self.get_enum_options(conversation_main_menu.menu_options)
		message_to_send = "What would you like to do?\n" + menu_options_string + "Reply with the number."
		await self.send_user_message(message_to_send)
		self.set_next_callback(self.on_selection_received)
	
	async def on_selection_received(self, message):
		if await conversation_utils.is_string_int(message.content, self.user) == False:
			return
		
		selection = int(message.content)
		if selection == conversation_main_menu.menu_options.ENABLE_CURSE:
			await self.switch_to_next_conversation(conversation_enable_curse(self.user))

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
		self.stop_conversation()
		

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
		rule_options = self.get_enum_options(rule_types)
		message_to_send = "What type of rule would you like to add?\n" + rule_options + "Reply with the number."

		author = self.user
		await author.send(message_to_send)

		self.set_next_callback(self.on_curse_rule_received)

	async def on_curse_rule_received(self, message):
		new_rule = create_rule_from_type(int(message.content))
		await new_rule.request_parameters(self, self.on_curse_rule_params_set)

	async def on_curse_rule_params_set(self, new_rule):
		self.curse.rules.append(new_rule)

		author = self.user
		curse_description = self.curse.get_rules_descriptions()
		await author.send(curse_description + "\nWould you like to add another rule?\nReply \"yes\" or \"no\"")

		self.set_next_callback(self.on_curse_another_rule)

	async def on_curse_another_rule(self, message):
		message_content = message.content.lower().strip()
		author = self.user

		if message_content == "yes":
			await self.start_new_rule_flow()
		elif message_content == "no":
			curse = self.curse
			file_utils.create_file_for_user(self.user, curse.name + ".json", curse.get_json_string())
			await self.send_user_message("New curse ***" + curse.name + "*** is saved.\nUse \"??curse_use " + curse.name + " <message to curse>\" to use the curse.")
			self.stop_conversation()
		else:
			await author.send("Response is not valid.\nReply \"YES\" or \"NO\"")