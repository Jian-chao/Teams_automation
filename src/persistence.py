"""
Persistence modules for storing application state to files.
"""
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any


class PollStatePersistence:
    """
    Persistence for poll state - tracks last poll time for each chat.
    Stores data in JSON format for human readability.
    """
    
    def __init__(self, file_path: str = "poll_state.json"):
        """
        Initialize poll state persistence.
        
        Args:
            file_path: Path to the state file
        """
        self.file_path = Path(file_path)
        self._load()
    
    def _load(self) -> None:
        """Load state from file or initialize empty state."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {"chats": {}}
        else:
            self.data = {"chats": {}}
    
    def _save(self) -> None:
        """Save current state to file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def get_last_poll_time(self, chat_id: str) -> Optional[datetime]:
        """
        Get the last poll time for a specific chat.
        
        Args:
            chat_id: The chat ID to look up
            
        Returns:
            datetime of last poll, or None if never polled
        """
        if chat_id in self.data["chats"]:
            return datetime.fromisoformat(
                self.data["chats"][chat_id]["last_poll_time"]
            )
        return None
    
    def update_last_poll_time(self, chat_id: str, time: datetime) -> None:
        """
        Update the last poll time for a chat.
        
        Args:
            chat_id: The chat ID to update
            time: The new poll time
        """
        self.data["chats"][chat_id] = {
            "last_poll_time": time.isoformat()
        }
        self._save()


class ForwardedHistoryPersistence:
    """
    Persistence for forwarded message history.
    Tracks which messages have been forwarded to prevent duplicates.
    """
    
    def __init__(self, file_path: str = "forwarded_history.json"):
        """
        Initialize forwarded history persistence.
        
        Args:
            file_path: Path to the history file
        """
        self.file_path = Path(file_path)
        self._load()
    
    def _load(self) -> None:
        """Load history from file or initialize empty history."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except json.JSONDecodeError:
                self.data = {"forwarded_messages": {}, "forwarded_job_ids": []}
        else:
            self.data = {"forwarded_messages": {}, "forwarded_job_ids": []}
    
    def _save(self) -> None:
        """Save current history to file."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def is_forwarded(self, message_id: str) -> bool:
        """
        Check if a message has already been forwarded.
        
        Args:
            message_id: The original message ID
            
        Returns:
            True if message was already forwarded
        """
        return message_id in self.data["forwarded_messages"]
    
    def is_job_id_forwarded(self, job_id: str) -> bool:
        """
        Check if a job ID has already been forwarded.
        
        Args:
            job_id: The job ID to check
            
        Returns:
            True if job ID was already forwarded
        """
        return job_id.lower() in [j.lower() for j in self.data["forwarded_job_ids"]]
    
    def mark_forwarded(
        self, 
        message_id: str, 
        job_id: Optional[str], 
        forwarded_message_id: str
    ) -> None:
        """
        Mark a message as forwarded.
        
        Args:
            message_id: The original message ID
            job_id: The extracted job ID (may be None)
            forwarded_message_id: The new message ID in target chat
        """
        self.data["forwarded_messages"][message_id] = {
            "job_id": job_id,
            "forwarded_message_id": forwarded_message_id,
            "forwarded_at": datetime.now().isoformat()
        }
        if job_id and job_id not in self.data["forwarded_job_ids"]:
            self.data["forwarded_job_ids"].append(job_id)
        self._save()
    
    def get_all_forwarded_job_ids(self) -> list:
        """
        Get all forwarded job IDs.
        
        Returns:
            List of all job IDs that have been forwarded
        """
        return self.data["forwarded_job_ids"].copy()
