from enum import IntEnum
import json

class rule_types(IntEnum):
    UNKNOWN = 0
    REPLACE = 1
    INSERT = 2

class custom_curse():
    def __init__(self):
        self.rules = []
    
    def parse(self, text):
        for rule in self.rules:
            text = rule.parse(text)
        
        return text
    
    def get_json_string(self):
        serialized_rules = []
        for rule in self.rules:
            serialized_rules.append(rule.serialize())
        
        return json.dumps(serialized_rules)
    
    def create_from_json(self, data):
        for rule_data in data:
            self.add_rule_from_data(rule_data)
    
    def add_rule_from_data(self, rule_data):
        rule_type = rule_data["type"]
        new_rule = custom_curse_rule()
        if rule_type == rule_types.REPLACE.value:
            new_rule = custom_curse_rule_replace("", "")
        elif rule_type == rule_types.INSERT.value:
            new_rule = custom_curse_rule_insert("", 0)
        
        if new_rule.rule_type == rule_types.UNKNOWN.value:
            return
        
        new_rule.deserialize(rule_data["data"])
        self.rules.append(new_rule)

class custom_curse_rule():
    rule_type = rule_types.UNKNOWN.value
    
    def parse(self, text):
        raise NotImplementedError()

    def serialize(self):
        raise NotImplementedError()

    def deserialize(self, data):
        raise NotImplementedError()

class custom_curse_rule_replace(custom_curse_rule):
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

class custom_curse_rule_insert(custom_curse_rule):
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