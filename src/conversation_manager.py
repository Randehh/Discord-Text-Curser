import time

class conversation_manager():
    """Handles all boilerplate events and handling for direct messages the bot receives."""

    def __init__(self):
        self.conversations = {}
    
    async def process_message(self, user, message):
        """Automatically called every time the bot receives a direct message."""

        if self.is_in_converation(user) == False:
            return
        
        conversation_data = self.conversations[user.id]
        callback = conversation_data["callback"]
        await callback(conversation_data, message)
    
    def set_callback_for_user(self, user, callback):
        """Updates a callback for a conversation which will be called when a user sends the bot a direct message."""

        if self.is_in_converation(user) == False:
            return
        
        conversation_data = self.conversations[user.id]
        conversation_data["callback"] = callback
    
    def start_conversation(self, user, callback):
        """Initializes a new conversation table and enables callbacks to be called."""

        if self.is_in_converation(user) == True:
            return
        
        self.conversations[user.id] = {}
        self.conversations[user.id]["author"] = user
        self.set_callback_for_user(user, callback)
        return self.conversations[user.id]
    
    def stop_conversation(self, user):
        """Stops callbacks from being called and deletes conversation data."""

        if self.is_in_converation(user):
            del self.conversations[user.id]
    
    def is_in_converation(self, user):
        """Returns a bool whether the user is in conversation with the bot or not."""

        if user.id in self.conversations:
            return True
        else:
            return False