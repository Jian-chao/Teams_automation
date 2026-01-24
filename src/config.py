"""
Configuration management module.
Loads configuration from JSON file.
"""
import json
from pathlib import Path
from typing import Dict, Any


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON
    """
    path = Path(config_path)
    
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Please create a config.json file based on config.example.json"
        )
    
    with open(path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Validate required fields
    required_fields = [
        "target_push_chat_id",
        "poll_interval_seconds", 
        "my_display_name",
        "patterns",
        "azure_ad"
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")
    
    # Validate azure_ad sub-fields
    azure_ad_required = ["client_id", "tenant_id"]
    for field in azure_ad_required:
        if field not in config["azure_ad"]:
            raise ValueError(f"Missing required azure_ad field: {field}")
    
    return config
