import time

class conversation_manager():
    def __init__(self):
        self.conversations = {}
    
    async def process_message(self, user, message):
        if self.is_in_converation(user) == False:
            return
        
        conversation_data = self.conversations[user.id]
        callback = conversation_data["callback"]
        await callback(conversation_data, message)
    
    def set_callback_for_user(self, user, callback):
        if self.is_in_converation(user) == False:
            return
        
        conversation_data = self.conversations[user.id]
        conversation_data["callback"] = callback
    
    def start_conversation(self, user, callback):
        if self.is_in_converation(user) == True:
            return
        
        self.conversations[user.id] = {}
        self.conversations[user.id]["author"] = user
        self.set_callback_for_user(user, callback)
        return self.conversations[user.id]
    
    def stop_conversation(self, user):
        if self.is_in_converation(user):
            del self.conversations[user.id]
    
    def is_in_converation(self, user):
        if user.id in self.conversations:
            return True
        else:
            return False