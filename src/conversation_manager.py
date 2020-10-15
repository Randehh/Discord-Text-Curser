import time

class conversation_manager():
    """Handles all boilerplate events and handling for direct messages the bot receives."""

    def __init__(self):
        self.conversations = {}
    
    async def process_message(self, user, message):
        """Automatically called every time the bot receives a direct message."""

        if self.is_in_converation(user) == False:
            return
        
        conversation = self.conversations[user.id]
        await conversation.on_receive_message(message)
    
    def start_conversation(self, conversation):
        """Initializes a new conversation table and enables callbacks to be called."""
        
        self.conversations[conversation.user.id] = conversation
    
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