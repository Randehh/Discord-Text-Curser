from enum import IntEnum
import json
import conversation_utils

class rule_types(IntEnum):
    INVALID = -1
    REPLACE = 1
    INSERT = 2
    REPLACE_WORD = 3

def create_rule_from_type(rule_type):
    """Create a new curse rule by the given rule type.
    
    Parameters
    -----------
    rule_type
        A value of the enum rule_types"""

    if rule_type == rule_types.REPLACE.value:
        return curse_rule_replace("", "")
    elif rule_type == rule_types.INSERT.value:
        return curse_rule_insert("", 0)
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

class curse_rule_insert(curse_rule):
    """Parses text by inserting a character sequence every given amount of words."""

    def __init__(self, to_insert, frequency):
        self.rule_type = rule_types.INSERT.value
        self.to_insert = to_insert
        self.frequency = frequency
    
    def parse(self, text):
        new_text = ""
        count = 0
        text_split = text.split()
        for word in text_split:
            new_text = new_text + word + " "
            count = count + 1
            if count == self.frequency:
                new_text = new_text + self.to_insert + " "
                count = 0
        
        return new_text
    
    def get_description(self):
        return "Insert ***" + self.to_insert + "*** after each ***" + str(self.frequency) + "*** words"
    
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
        await self.request_parameters_data["conversation"].send_user_message("After how many words would you like to insert ***" + self.to_insert + "***?")
        self.request_parameters_data["conversation"].set_next_callback(self.on_get_param_frequency)
    
    async def on_get_param_frequency(self, message):
        if await conversation_utils.is_string_int(message.content, self.request_parameters_data["conversation"].user) == False:
            return
        
        self.frequency = int(message.content)
        await self.request_parameters_data["conversation"].send_user_message("Rule set: " + self.get_description())
        await self.request_parameters_data["all_params_set_callback"](self)
        self.request_parameters_data = None