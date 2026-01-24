"""
Microsoft Graph API client creation with Azure AD authentication.
"""
from azure.identity import InteractiveBrowserCredential, TokenCachePersistenceOptions
from msgraph_beta import GraphServiceClient


def create_graph_client(config: dict) -> GraphServiceClient:
    """
    Create an authenticated Graph API client.
    
    Uses InteractiveBrowserCredential for delegated permissions.
    First run will open browser for login, subsequent runs use cached token.
    
    Args:
        config: Configuration dictionary containing azure_ad settings
        
    Returns:
        Authenticated GraphServiceClient instance
    """
    # Enable token cache persistence for subsequent runs
    cache_options = TokenCachePersistenceOptions(
        name="teams_push_forwarder_cache",
        allow_unencrypted_storage=True  # Set to False in production with encryption
    )
    
    credential = InteractiveBrowserCredential(
        client_id=config["azure_ad"]["client_id"],
        tenant_id=config["azure_ad"]["tenant_id"],
        cache_persistence_options=cache_options
    )
    
    # Required scopes for reading chats and sending messages
    scopes = ["Chat.Read", "ChatMessage.Send"]
    
    return GraphServiceClient(credentials=credential, scopes=scopes)
