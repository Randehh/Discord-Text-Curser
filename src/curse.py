from enum import IntEnum
import json

class rule_types(IntEnum):
    NONE = 0
    REPLACE = 1
    INSERT = 2

def create_rule_from_type(rule_type):
    """Create a new curse rule by the given rule type.
    
    Parameters
    -----------
    rule_type
        A value of the enum rule_types"""

    new_rule = curse_rule()
    if rule_type == rule_types.REPLACE.value:
        new_rule = curse_rule_replace("", "")
    elif rule_type == rule_types.INSERT.value:
        new_rule = curse_rule_insert("", 0)
    
    return new_rule

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
        
        if new_rule.rule_type == rule_types.NONE.value:
            return
        
        new_rule.deserialize(rule_data["data"])
        self.rules.append(new_rule)

class curse_rule():
    """Represents a generic class cwhich can parse and modify a string.
    .. note::

        Should not be used separately, instead use one of the derived classes.
    """

    rule_type = rule_types.NONE.value
    
    def parse(self, text):
        raise NotImplementedError()

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self, data):
        raise NotImplementedError()

    async def request_parameters(self, conversation_data, all_params_set_callback):
        raise NotImplementedError()

class curse_rule_replace(curse_rule):
    """Parses text by executing a direct replace of character sequences."""

    def __init__(self, to_replace, replacement):
        self.rule_type = rule_types.REPLACE.value
        self.to_replace = to_replace
        self.replacement = replacement
    
    def parse(self, text):
        return text.replace(self.to_replace, self.replacement)
    
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
    
    async def request_parameters(self, conversation_data, all_params_set_callback):
        self.all_params_set_callback = all_params_set_callback
        await conversation_data["author"].send("What would you like to replace?")
        conversation_data["callback"] = self.on_get_param_to_replace
    
    async def on_get_param_to_replace(self, conversation_data, message):
        self.to_replace = message.content
        await conversation_data["author"].send("What would you like to replace ***" + self.to_replace + "*** with?")
        conversation_data["callback"] = self.on_get_param_replacement
    
    async def on_get_param_replacement(self, conversation_data, message):
        self.replacement = message.content
        await conversation_data["author"].send("Rule set: replace ***" + self.to_replace + "*** with ***" + self.replacement + "***")
        await self.all_params_set_callback(conversation_data, self)
        self.all_params_set_callback = None

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
    
    async def request_parameters(self, conversation_data, all_params_set_callback):
        self.all_params_set_callback = all_params_set_callback
        await conversation_data["author"].send("What would you like to insert?")
        conversation_data["callback"] = self.on_get_param_to_insert
    
    async def on_get_param_to_insert(self, conversation_data, message):
        self.to_insert = message.content
        await conversation_data["author"].send("After how many words would you like to insert ***" + self.to_insert + "***?")
        conversation_data["callback"] = self.on_get_param_frequency
    
    async def on_get_param_frequency(self, conversation_data, message):
        self.frequency = int(message.content)
        await conversation_data["author"].send("Rule set: insert ***" + self.to_insert + "*** after each ***" + str(self.frequency) + "***")
        await self.all_params_set_callback(conversation_data, self)
        self.all_params_set_callback = None