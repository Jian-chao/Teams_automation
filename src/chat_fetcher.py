"""
Chat fetcher module - dynamically retrieves all user chats.
"""
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class ChatType(Enum):
    """Types of Teams chats."""
    ONE_ON_ONE = "oneOnOne"
    GROUP = "group"
    MEETING = "meeting"


@dataclass
class ChatInfo:
    """Information about a chat."""
    chat_id: str
    chat_type: ChatType
    topic: Optional[str] = None  # Group name (None for oneOnOne)


class ChatFetcher:
    """
    Fetches all chats for the authenticated user.
    """
    
    def __init__(self, graph_client):
        """
        Initialize chat fetcher.
        
        Args:
            graph_client: Authenticated GraphServiceClient
        """
        self.graph_client = graph_client
    
    async def get_all_chats(self) -> List[ChatInfo]:
        """
        Retrieve all chats for the current user.
        
        Returns:
            List of ChatInfo objects
        """
        result = await self.graph_client.me.chats.get()
        
        chats = []
        if result and result.value:
            for chat in result.value:
                # Map chat type string to enum
                chat_type_str = chat.chat_type if hasattr(chat, 'chat_type') else None
                
                if chat_type_str == "oneOnOne":
                    chat_type = ChatType.ONE_ON_ONE
                elif chat_type_str == "group":
                    chat_type = ChatType.GROUP
                elif chat_type_str == "meeting":
                    chat_type = ChatType.MEETING
                else:
                    # Default to group for unknown types
                    chat_type = ChatType.GROUP
                
                chats.append(ChatInfo(
                    chat_id=chat.id,
                    chat_type=chat_type,
                    topic=chat.topic if hasattr(chat, 'topic') else None
                ))
        
        return chats
    
    async def get_chats_by_type(self, chat_type: ChatType) -> List[ChatInfo]:
        """
        Get chats filtered by type.
        
        Args:
            chat_type: The type of chats to retrieve
            
        Returns:
            List of ChatInfo objects of the specified type
        """
        all_chats = await self.get_all_chats()
        return [c for c in all_chats if c.chat_type == chat_type]
