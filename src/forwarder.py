"""
Message forwarder module - forwards messages to target chat using MS Graph API.
"""
from typing import Optional

from msgraph_beta import GraphServiceClient
from msgraph_beta.generated.chats.item.messages.forward_to_chat.forward_to_chat_post_request_body import ForwardToChatPostRequestBody
from msgraph_beta.generated.models.chat_message import ChatMessage
from msgraph_beta.generated.models.item_body import ItemBody


async def forward_message(
    graph_client: GraphServiceClient,
    source_chat_id: str,
    message_id: str,
    target_chat_id: str,
    additional_text: str = ""
) -> str:
    """
    Forward a message to the target chat.
    
    Uses MS Graph API beta endpoint: POST /chats/{chatId}/messages/forwardToChat
    
    Args:
        graph_client: Authenticated GraphServiceClient (beta)
        source_chat_id: ID of the chat containing the original message
        message_id: ID of the message to forward
        target_chat_id: ID of the target chat to forward to
        additional_text: Optional additional message text
        
    Returns:
        The ID of the forwarded message in the target chat
        
    Raises:
        Exception: If forwarding fails
    """
    # Build request body
    additional_message = None
    if additional_text:
        additional_message = ChatMessage(
            body=ItemBody(content=additional_text)
        )
    
    request_body = ForwardToChatPostRequestBody(
        target_chat_ids=[target_chat_id],
        message_ids=[message_id],
        additional_message=additional_message
    )
    
    # Call the API
    result = await graph_client.chats.by_chat_id(
        source_chat_id
    ).messages.forward_to_chat.post(request_body)
    
    # Extract the forwarded message ID from result
    if result and result.value and len(result.value) > 0:
        return result.value[0].forwarded_message_id
    
    raise Exception("Forward operation completed but no message ID returned")


class MessageForwarder:
    """
    Message forwarder class with additional utilities.
    """
    
    def __init__(self, graph_client: GraphServiceClient, target_chat_id: str):
        """
        Initialize message forwarder.
        
        Args:
            graph_client: Authenticated GraphServiceClient (beta)
            target_chat_id: Default target chat ID for forwarding
        """
        self.graph_client = graph_client
        self.target_chat_id = target_chat_id
    
    async def forward(
        self, 
        source_chat_id: str, 
        message_id: str,
        job_id: Optional[str] = None,
        additional_text: str = ""
    ) -> str:
        """
        Forward a message to the target chat.
        
        Args:
            source_chat_id: ID of the source chat
            message_id: ID of the message to forward
            job_id: Optional job ID (for logging)
            additional_text: Optional additional message text
            
        Returns:
            The forwarded message ID
        """
        result = await forward_message(
            self.graph_client,
            source_chat_id,
            message_id,
            self.target_chat_id,
            additional_text
        )
        
        print(f"Successfully forwarded message {message_id} (Job ID: {job_id or 'N/A'})")
        
        return result
