import time

MAXIMUM_CONVERSATION_LIFETIME = 600     # 10 minutes

class conversation_manager():
    """Handles all boilerplate events and handling for direct messages the bot receives."""

    def __init__(self):
        self.conversations = {}
    
    async def process_message(self, user_id, message):
        """Automatically called every time the bot receives a direct message."""

        if self.is_in_converation(user_id) == False:
            return False
        
        conversation = self.conversations[user_id]
        await conversation.on_receive_message(message)
        return True
    
    def start_conversation(self, conversation):
        """Initializes a new conversation table and enables callbacks to be called."""
        
        self.conversations[conversation.user.id] = conversation
    
    def stop_conversation(self, user_id):
        """Stops callbacks from being called and deletes conversation data."""

        if self.is_in_converation(user_id):
            del self.conversations[user_id]
    
    def is_in_converation(self, user_id):
        """Returns a bool whether the user is in conversation with the bot or not."""

        if user_id in self.conversations:
            return True
        else:
            return False
    
    async def attempt_close_conversations(self):
        current_time = time.time()
        conversations_to_close = []
        for conversation_user_id in self.conversations:
            conversation = self.conversations[conversation_user_id]
            if current_time - conversation.last_update_time >= MAXIMUM_CONVERSATION_LIFETIME:
                conversations_to_close.append(conversation_user_id)
        
        for conversation_id in conversations_to_close:
            conversation = self.conversations[conversation_id]
            await conversation.send_user_message("No activity detected - stopping conversation.")
            self.stop_conversation(conversation_id)