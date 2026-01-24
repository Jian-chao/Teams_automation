"""
Tests for duplicate checker module.
"""
import pytest
import json
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch

from src.persistence import ForwardedHistoryPersistence
from src.duplicate_checker import DuplicateChecker


class TestForwardedHistoryPersistence:
    """Tests for ForwardedHistoryPersistence class."""
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for persistence."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    def test_initial_state(self, temp_file):
        """Test initial empty state."""
        persistence = ForwardedHistoryPersistence(temp_file)
        
        assert persistence.is_forwarded("msg-1") is False
        assert persistence.is_job_id_forwarded("job-1") is False
    
    def test_mark_forwarded(self, temp_file):
        """Test marking a message as forwarded."""
        persistence = ForwardedHistoryPersistence(temp_file)
        
        persistence.mark_forwarded("msg-1", "job-123", "fwd-msg-1")
        
        assert persistence.is_forwarded("msg-1") is True
        assert persistence.is_job_id_forwarded("job-123") is True
    
    def test_persistence_across_instances(self, temp_file):
        """Test data persists across instances."""
        # First instance
        p1 = ForwardedHistoryPersistence(temp_file)
        p1.mark_forwarded("msg-2", "job-456", "fwd-msg-2")
        
        # Second instance
        p2 = ForwardedHistoryPersistence(temp_file)
        
        assert p2.is_forwarded("msg-2") is True
        assert p2.is_job_id_forwarded("job-456") is True
    
    def test_case_insensitive_job_id(self, temp_file):
        """Test job ID matching is case insensitive."""
        persistence = ForwardedHistoryPersistence(temp_file)
        
        persistence.mark_forwarded("msg-3", "JOB-ABC", "fwd-msg-3")
        
        assert persistence.is_job_id_forwarded("job-abc") is True
        assert persistence.is_job_id_forwarded("JOB-ABC") is True
        assert persistence.is_job_id_forwarded("Job-Abc") is True
    
    def test_none_job_id(self, temp_file):
        """Test handling None job ID."""
        persistence = ForwardedHistoryPersistence(temp_file)
        
        persistence.mark_forwarded("msg-4", None, "fwd-msg-4")
        
        assert persistence.is_forwarded("msg-4") is True
        # Should not add None to job_ids list
        assert len(persistence.data["forwarded_job_ids"]) == 0
    
    def test_get_all_job_ids(self, temp_file):
        """Test getting all forwarded job IDs."""
        persistence = ForwardedHistoryPersistence(temp_file)
        
        persistence.mark_forwarded("msg-5", "job-1", "fwd-1")
        persistence.mark_forwarded("msg-6", "job-2", "fwd-2")
        persistence.mark_forwarded("msg-7", "job-3", "fwd-3")
        
        job_ids = persistence.get_all_forwarded_job_ids()
        
        assert len(job_ids) == 3
        assert "job-1" in job_ids
        assert "job-2" in job_ids
        assert "job-3" in job_ids


class TestDuplicateChecker:
    """Tests for DuplicateChecker class."""
    
    @pytest.fixture
    def mock_graph_client(self):
        """Create a mock Graph client."""
        return MagicMock()
    
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for persistence."""
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def checker(self, mock_graph_client, temp_file):
        """Create a DuplicateChecker instance."""
        persistence = ForwardedHistoryPersistence(temp_file)
        return DuplicateChecker(
            mock_graph_client,
            "target-chat-id",
            persistence
        )
    
    @pytest.mark.asyncio
    async def test_not_duplicate_new_message(self, checker, mock_graph_client):
        """Test new message is not a duplicate."""
        # Mock empty target chat
        mock_response = MagicMock()
        mock_response.value = []
        mock_graph_client.chats.by_chat_id.return_value.messages.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await checker.is_duplicate("new-msg-1", "new-job-1")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_duplicate_local_record(self, checker):
        """Test message in local record is duplicate."""
        # Mark as forwarded locally
        checker.persistence.mark_forwarded("msg-local", "job-local", "fwd-local")
        
        result = await checker.is_duplicate("msg-local", "job-local")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_duplicate_forwarded_by_others(self, checker, mock_graph_client):
        """Test message forwarded by others is duplicate."""
        # Mock target chat with forwarded message
        mock_attachment = MagicMock()
        mock_attachment.content_type = "forwardedMessageReference"
        mock_attachment.content = json.dumps({"originalMessageId": "msg-other"})
        
        mock_message = MagicMock()
        mock_message.attachments = [mock_attachment]
        
        mock_response = MagicMock()
        mock_response.value = [mock_message]
        
        mock_graph_client.chats.by_chat_id.return_value.messages.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await checker.is_duplicate("msg-other", "job-other")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_duplicate_job_id_mentioned(self, checker, mock_graph_client):
        """Test job ID mentioned in target chat is duplicate."""
        # Mock target chat with message mentioning job ID
        mock_body = MagicMock()
        mock_body.content = "I already pushed job-mentioned yesterday"
        
        mock_message = MagicMock()
        mock_message.body = mock_body
        mock_message.attachments = None
        
        mock_response = MagicMock()
        mock_response.value = [mock_message]
        
        mock_graph_client.chats.by_chat_id.return_value.messages.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await checker.is_duplicate("new-msg", "job-mentioned")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_job_id_case_insensitive(self, checker, mock_graph_client):
        """Test job ID matching is case insensitive."""
        mock_body = MagicMock()
        mock_body.content = "Already pushed JOB-UPPER"
        
        mock_message = MagicMock()
        mock_message.body = mock_body
        mock_message.attachments = None
        
        mock_response = MagicMock()
        mock_response.value = [mock_message]
        
        mock_graph_client.chats.by_chat_id.return_value.messages.get = AsyncMock(
            return_value=mock_response
        )
        
        result = await checker.is_duplicate("new-msg", "job-upper")
        
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
