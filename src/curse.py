from enum import IntEnum
import json
import conversation_utils
import curse_utils
import random

class rule_types(IntEnum):
    INVALID = -1
    REPLACE = 1
    INSERT = 2
    REPLACE_WORD = 3
    INSERT_CHARACTER = 4

def create_rule_from_type(rule_type):
    """Create a new curse rule by the given rule type.
    
    Parameters
    -----------
    rule_type
        A value of the enum rule_types"""

    if rule_type == rule_types.REPLACE.value:
        return curse_rule_replace("", "")
    elif rule_type == rule_types.INSERT.value:
        return curse_rule_insert_word("", [0])
    elif rule_type == rule_types.INSERT_CHARACTER.value:
        return curse_rule_insert_character("", [0])
    elif rule_type == rule_types.REPLACE_WORD.value:
        return curse_rule_replace_word("", "")
    
    return None

class curse():
    """Represents a curse that can parse text according to rules given."""

    def __init__(self, name):
        self.name = name
        self.rules = []
    
    def parse(self, text):
        """Parse the given text through all rules in this curse."""

        for rule in self.rules:
            text = rule.parse(text)
        
        return text
    
    def get_rules_descriptions(self):
        to_return = "Rules in curse:\n"
        count = 1
        for rule in self.rules:
            to_return = to_return + str(count) + ": " + rule.get_description() + "\n"
            count = count + 1
        return to_return
    
    def get_json_string(self):
        """Serializes the entire curse into a json format string."""

        serialized_rules = []
        for rule in self.rules:
            serialized_rules.append(rule.serialize())
        
        return json.dumps(serialized_rules)
    
    def create_from_json(self, data):
        """Configures the curse by the given json."""

        for rule_data in data:
            self.add_rule_from_data(rule_data)
    
    def add_rule_from_data(self, rule_data):
        """Adds a curse rule from a serialized json file"""

        rule_type = rule_data["type"]
        new_rule = create_rule_from_type(rule_type)
        
        if new_rule.rule_type == rule_types.INVALID.value:
            return
        
        new_rule.deserialize(rule_data["data"])
        self.rules.append(new_rule)

class curse_rule():
    """Represents a generic class cwhich can parse and modify a string.
    .. note::

        Should not be used separately, instead use one of the derived classes.
    """

    rule_type = rule_types.INVALID.value
    
    def parse(self, text):
        raise NotImplementedError()

    def get_description(self):
        raise NotImplementedError()

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self, data):
        raise NotImplementedError()

    async def request_parameters(self, conversation, all_params_set_callback):
        self.request_parameters_data = {
            "conversation": conversation,
            "all_params_set_callback": all_params_set_callback
        }

class curse_rule_replace(curse_rule):
    """Parses text by executing a direct replace of character sequences."""

    def __init__(self, to_replace, replacement):
        self.rule_type = rule_types.REPLACE.value
        self.to_replace = to_replace
        self.replacement = replacement
    
    def parse(self, text):
        for to_replace_word in self.to_replace:
            text = conversation_utils.replace_word_with_random_word(text, to_replace_word, self.replacement)
        return text
    
    def get_description(self):
        return "Replace ***" + conversation_utils.get_list_to_string(self.to_replace) + "*** with ***" + conversation_utils.get_list_to_string(self.replacement) + "***"

    def serialize(self):
        return {
            "type": self.rule_type,
            "data": {
                "to_replace": self.to_replace,
                "replacement": self.replacement
            }
        }
    
    def deserialize(self, data):
        self.to_replace = data["to_replace"]
        self.replacement = data["replacement"]
    
    async def request_parameters(self, conversation, all_params_set_callback):
        await super().request_parameters(conversation, all_params_set_callback)
        await conversation.send_user_message("What would you like to replace? Multiple are allowed, where each new line is an entry.")
        conversation.set_next_callback(self.on_get_param_to_replace)
    
    async def on_get_param_to_replace(self, message):
        self.to_replace = message.content.split("\n")
        await self.request_parameters_data["conversation"].send_user_message("What would you like to replace ***" + conversation_utils.get_list_to_string(self.to_replace) + "*** with? Multiple are allowed, where each new line is an entry.")
        self.request_parameters_data["conversation"].set_next_callback(self.on_get_param_replacement)
    
    async def on_get_param_replacement(self, message):
        self.replacement = message.content.split("\n")
        await self.request_parameters_data["conversation"].send_user_message("Rule set: " + self.get_description())
        await self.request_parameters_data["all_params_set_callback"](self)
        self.request_parameters_data = None

class curse_rule_replace_word(curse_rule):
    """Parses text by replacing a word with another word."""

    def __init__(self, to_replace, replacement):
        self.rule_type = rule_types.REPLACE_WORD.value
        self.to_replace = to_replace
        self.replacement = replacement
    
    def parse(self, text):
        result = ""
        symbols_to_ignore = r'.,;(){}[]_*~'

        for word in text.split():
            striped_word = word.strip(symbols_to_ignore)
            if striped_word == self.to_replace:                    
                result = result + " " + word.replace(self.to_replace, self.replacement)
            else:
                result = result + " " + word
        return result
    
    def get_description(self):
        return "Replace the word ***" + self.to_replace + "*** with ***" + self.replacement + "***"

    def serialize(self):
        return {
            "type": self.rule_type,
            "data": {
                "to_replace": self.to_replace,
                "replacement": self.replacement
            }
        }
    
    def deserialize(self, data):
        self.to_replace = data["to_replace"]
        self.replacement = data["replacement"]
    
    async def request_parameters(self, conversation, all_params_set_callback):
        await super().request_parameters(conversation, all_params_set_callback)
        await conversation.send_user_message("What would you like to replace?")
        conversation.set_next_callback(self.on_get_param_to_replace)
    
    async def on_get_param_to_replace(self, message):
        if len(message.content.split()) != 1:
            await self.request_parameters_data["conversation"].send_user_message("Please give one word to replace.")
            return
        
        self.to_replace = message.content
        await self.request_parameters_data["conversation"].send_user_message("What would you like to replace ***" + self.to_replace + "*** with?")
        self.request_parameters_data["conversation"].set_next_callback(self.on_get_param_replacement)
    
    async def on_get_param_replacement(self, message):
        self.replacement = message.content
        await self.request_parameters_data["conversation"].send_user_message("Rule set: " + self.get_description())
        await self.request_parameters_data["all_params_set_callback"](self)
        self.request_parameters_data = None

class curse_rule_insert_base(curse_rule):
    def __init__(self, to_insert, frequency):
        self.to_insert = to_insert
        self.frequency = frequency
    
    def update_frequency(self):
        if len(self.frequency) == 1:
            self.next_frequency = self.frequency[0]
        else:
            self.next_frequency = random.randrange(self.frequency[0], self.frequency[1])
    
    def get_insert_type(self):
        raise NotImplementedError()

    def get_description(self):
        if len(self.frequency) == 1:
            return "Insert ***" + self.to_insert + "*** after each ***" + str(self.frequency[0]) + "*** " + self.get_insert_type()
        elif len(self.frequency) == 2:
            return "Insert ***" + self.to_insert + "*** between a range of ***" + str(self.frequency[0]) + " and " + str(self.frequency[1]) + "*** " + self.get_insert_type()

    def parse(self, text):
        self.new_text = ""
        self.count = 0
        self.update_frequency()

        def loop_update(self, to_add):
            self.new_text = self.new_text + to_add
            self.count = self.count + 1
            if self.count == self.next_frequency:
                self.new_text = self.new_text + self.to_insert
                self.count = 0
                self.update_frequency()
        
        self.insert_parse_loop(text, loop_update)
        return self.new_text
    
    def insert_parse_loop(self, text, callback):
        raise NotImplementedError()

    def serialize(self):
        return {
            "type": self.rule_type,
            "data": {
                "to_insert": self.to_insert,
                "frequency": self.frequency
            }
        }
    
    def deserialize(self, data):
        self.to_insert = data["to_insert"]
        self.frequency = data["frequency"]
    
    async def request_parameters(self, conversation, all_params_set_callback):
        await super().request_parameters(conversation, all_params_set_callback)
        await conversation.send_user_message("What would you like to insert?")
        conversation.set_next_callback(self.on_get_param_to_insert)
    
    async def on_get_param_to_insert(self, message):
        self.to_insert = message.content

        message_to_send = "After how many " + self.get_insert_type() + " would you like to insert ***" + self.to_insert + "***?\n"
        message_to_send = message_to_send + "For a range, seperate it by a comma as such: `2,5`."
        await self.request_parameters_data["conversation"].send_user_message(message_to_send)
        self.request_parameters_data["conversation"].set_next_callback(self.on_get_param_frequency)
    
    async def on_get_param_frequency(self, message):
        if "," in message.content:
            message_split = message.content.split(",")
            if len(message_split) != 2:
                await self.request_parameters_data["conversation"].send_user_message("Please provide the message in the following format: `2,5`.")
                return

            if await curse_utils.is_string_int(message_split[0], self.request_parameters_data["conversation"].user) == False:
                return

            if await curse_utils.is_string_int(message_split[1], self.request_parameters_data["conversation"].user) == False:
                return
            
            self.frequency = [int(message_split[0]), int(message_split[1])]

        else:
            if await curse_utils.is_string_int(message.content, self.request_parameters_data["conversation"].user) == False:
                return
            
            self.frequency = [int(message.content)]

        await self.request_parameters_data["conversation"].send_user_message("Rule set: " + self.get_description())
        await self.request_parameters_data["all_params_set_callback"](self)
        self.request_parameters_data = None

class curse_rule_insert_word(curse_rule_insert_base):
    """Parses text by inserting a character sequence every given amount of words."""

    def __init__(self, to_insert, frequency):
        super().__init__(to_insert, frequency)
        self.rule_type = rule_types.INSERT.value

    def get_insert_type(self):
        return "words"

    def insert_parse_loop(self, text, callback):
        text_split = text.split()
        for word in text_split:
            callback(self, word + " ")

class curse_rule_insert_character(curse_rule_insert_base):
    """Parses text by inserting a character sequence every given amount of characters."""

    def __init__(self, to_insert, frequency):
        super().__init__(to_insert, frequency)
        self.rule_type = rule_types.INSERT_CHARACTER.value
    
    def get_insert_type(self):
        return "characters"

    def insert_parse_loop(self, text, callback):
        for character in text:
            callback(self, character)