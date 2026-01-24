"""
Message monitor module - fetches new messages from chats based on chat type.
"""
from datetime import datetime, timezone
from typing import List, Tuple, Any

from .chat_fetcher import ChatInfo, ChatType
from .persistence import PollStatePersistence


class MessageMonitor:
    """
    Monitors chats for new messages.
    
    Filters messages based on chat type:
    - oneOnOne: All new messages since last poll
    - group: Only new messages with @mention of the user
    """
    
    def __init__(
        self, 
        graph_client, 
        my_display_name: str, 
        persistence: PollStatePersistence
    ):
        """
        Initialize message monitor.
        
        Args:
            graph_client: Authenticated GraphServiceClient
            my_display_name: Display name of the current user (for @mention detection)
            persistence: Poll state persistence instance
        """
        self.graph_client = graph_client
        self.my_display_name = my_display_name
        self.persistence = persistence
    
    async def get_new_messages(self, chat: ChatInfo) -> List[Tuple[str, Any]]:
        """
        Get new messages from a chat based on its type.
        
        For oneOnOne chats: Returns all new messages
        For group chats: Returns only messages that @mention the user
        
        Args:
            chat: ChatInfo object describing the chat
            
        Returns:
            List of tuples (chat_id, message_object)
        """
        last_poll_time = self.persistence.get_last_poll_time(chat.chat_id)
        
        try:
            # Fetch messages from the chat
            messages_response = await self.graph_client.chats.by_chat_id(
                chat.chat_id
            ).messages.get()
            
            if not messages_response or not messages_response.value:
                return []
            
            new_messages = []
            
            for msg in messages_response.value:
                # Skip system messages
                if not msg.body or not msg.body.content:
                    continue
                
                # Skip messages from self
                if self._is_from_self(msg):
                    continue
                
                # Check if message is newer than last poll
                msg_time = msg.created_date_time
                if last_poll_time and msg_time:
                    # Convert to timezone-aware for comparison
                    if msg_time.tzinfo is None:
                        msg_time = msg_time.replace(tzinfo=timezone.utc)
                    if last_poll_time.tzinfo is None:
                        last_poll_time = last_poll_time.replace(tzinfo=timezone.utc)
                    
                    if msg_time <= last_poll_time:
                        continue
                
                # Filter based on chat type
                if chat.chat_type == ChatType.ONE_ON_ONE:
                    # One-on-one: include all new messages
                    new_messages.append((chat.chat_id, msg))
                elif chat.chat_type == ChatType.GROUP:
                    # Group: only include messages that mention the user
                    if self._is_mentioned(msg):
                        new_messages.append((chat.chat_id, msg))
                # Skip meeting chats for now
            
            # Update poll time after processing
            self.persistence.update_last_poll_time(chat.chat_id, datetime.now(timezone.utc))
            
            return new_messages
            
        except Exception as e:
            print(f"Error fetching messages from chat {chat.chat_id}: {e}")
            return []
    
    def _is_from_self(self, message) -> bool:
        """
        Check if message is from the current user.
        
        Args:
            message: Message object
            
        Returns:
            True if message is from self
        """
        try:
            if message.from_:
                if message.from_.user:
                    display_name = message.from_.user.display_name
                    if display_name and display_name == self.my_display_name:
                        return True
        except AttributeError:
            pass
        return False
    
    def _is_mentioned(self, message) -> bool:
        """
        Check if message @mentions the current user.
        
        Args:
            message: Message object
            
        Returns:
            True if user is mentioned
        """
        try:
            if message.mentions:
                for mention in message.mentions:
                    if mention.mentioned and mention.mentioned.user:
                        mentioned_name = mention.mentioned.user.display_name
                        if mentioned_name == self.my_display_name:
                            return True
        except AttributeError:
            pass
        return False
