"""
Duplicate checker module - prevents forwarding the same message/job twice.
"""
import json
from typing import Optional

from .persistence import ForwardedHistoryPersistence


class DuplicateChecker:
    """
    Checks if a message or job ID has already been forwarded.
    
    Performs three levels of duplicate checking:
    1. Local record of forwarded message IDs
    2. Target chat messages with forwardedMessageReference
    3. Target chat messages mentioning the same job ID
    """
    
    def __init__(
        self, 
        graph_client, 
        target_chat_id: str, 
        persistence: ForwardedHistoryPersistence
    ):
        """
        Initialize duplicate checker.
        
        Args:
            graph_client: Authenticated GraphServiceClient
            target_chat_id: ID of the target push job chat group
            persistence: Forwarded history persistence instance
        """
        self.graph_client = graph_client
        self.target_chat_id = target_chat_id
        self.persistence = persistence
    
    async def is_duplicate(
        self, 
        message_id: str, 
        job_id: Optional[str]
    ) -> bool:
        """
        Check if a message or job has already been forwarded.
        
        Args:
            message_id: The original message ID
            job_id: The extracted job ID (may be None)
            
        Returns:
            True if this is a duplicate (should not forward)
        """
        # 1. Check local record
        if self.persistence.is_forwarded(message_id):
            return True
        
        # 2. Check if message was forwarded by others in target chat
        if await self._check_forwarded_in_target(message_id):
            return True
        
        # 3. Check if job ID is already mentioned in target chat
        if job_id and await self._check_job_id_mentioned(job_id):
            return True
        
        return False
    
    async def _check_forwarded_in_target(
        self, 
        original_message_id: str
    ) -> bool:
        """
        Check if the message was already forwarded to target chat by anyone.
        
        Args:
            original_message_id: The original message ID to check
            
        Returns:
            True if message was already forwarded
        """
        try:
            messages_response = await self.graph_client.chats.by_chat_id(
                self.target_chat_id
            ).messages.get()
            
            if not messages_response or not messages_response.value:
                return False
            
            for msg in messages_response.value:
                if msg.attachments:
                    for att in msg.attachments:
                        if att.content_type == "forwardedMessageReference":
                            try:
                                # Parse the attachment content
                                content = json.loads(att.content) if att.content else {}
                                if content.get("originalMessageId") == original_message_id:
                                    return True
                            except json.JSONDecodeError:
                                continue
            
            return False
            
        except Exception as e:
            print(f"Error checking forwarded messages: {e}")
            return False
    
    async def _check_job_id_mentioned(self, job_id: str) -> bool:
        """
        Check if job ID is already mentioned in target chat messages.
        
        This catches cases where someone manually typed the job ID
        instead of forwarding the original message.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            True if job ID is already mentioned
        """
        try:
            messages_response = await self.graph_client.chats.by_chat_id(
                self.target_chat_id
            ).messages.get()
            
            if not messages_response or not messages_response.value:
                return False
            
            job_id_lower = job_id.lower()
            
            for msg in messages_response.value:
                if msg.body and msg.body.content:
                    if job_id_lower in msg.body.content.lower():
                        return True
            
            return False
            
        except Exception as e:
            print(f"Error checking job ID mentions: {e}")
            return False
