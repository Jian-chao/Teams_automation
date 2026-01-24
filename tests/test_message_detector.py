"""
Tests for message detector module.
"""
import pytest
from src.message_detector import RegexMessageDetector, DetectionResult


class TestRegexMessageDetector:
    """Tests for RegexMessageDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create detector with default patterns."""
        patterns = [
            r"(?i)(?:please\s+)?(?:help\s+)?(?:to\s+)?push\s+['\"]?([\w-]+)['\"]?",
            r"(?i)push\s+(?:job\s+)?['\"]?([\w-]+)['\"]?",
            r"(?i)幫忙\s*push\s+([\w-]+)",
        ]
        return RegexMessageDetector(patterns)
    
    def test_simple_push_request(self, detector):
        """Test simple 'push jobid' pattern."""
        result = detector.detect("Please push job-123", [])
        
        assert result.is_push_request is True
        assert result.job_id == "job-123"
        assert result.has_attachment is False
    
    def test_push_with_quotes(self, detector):
        """Test push with quoted job ID."""
        result = detector.detect("help to push 'ABC-456'", [])
        
        assert result.is_push_request is True
        assert result.job_id == "ABC-456"
    
    def test_push_with_mention(self, detector):
        """Test push request with @mention."""
        result = detector.detect("Hi @Grant, please help to push myJob123", [])
        
        assert result.is_push_request is True
        assert result.job_id == "myJob123"
    
    def test_chinese_push_request(self, detector):
        """Test Chinese push request pattern."""
        result = detector.detect("幫忙 push testJob", [])
        
        assert result.is_push_request is True
        assert result.job_id == "testJob"
    
    def test_with_attachment(self, detector):
        """Test detection with attachments."""
        attachments = [{"id": "att1", "name": "screenshot.png"}]
        result = detector.detect("push job-789", attachments)
        
        assert result.is_push_request is True
        assert result.job_id == "job-789"
        assert result.has_attachment is True
    
    def test_no_match(self, detector):
        """Test message that doesn't match any pattern."""
        result = detector.detect("Hello, how are you?", [])
        
        assert result.is_push_request is False
        assert result.job_id is None
    
    def test_empty_message(self, detector):
        """Test empty message."""
        result = detector.detect("", [])
        
        assert result.is_push_request is False
    
    def test_none_message(self, detector):
        """Test None message."""
        result = detector.detect(None, [])
        
        assert result.is_push_request is False
    
    def test_case_insensitive(self, detector):
        """Test case insensitivity."""
        result = detector.detect("PUSH JOB-UPPER", [])
        
        assert result.is_push_request is True
        assert result.job_id == "JOB-UPPER"
    
    def test_add_pattern(self, detector):
        """Test adding pattern at runtime."""
        # This pattern won't match initially
        result = detector.detect("prioritize task-999", [])
        assert result.is_push_request is False
        
        # Add new pattern
        success = detector.add_pattern(r"(?i)prioritize\s+([\w-]+)")
        assert success is True
        
        # Now it should match
        result = detector.detect("prioritize task-999", [])
        assert result.is_push_request is True
        assert result.job_id == "task-999"
    
    def test_get_patterns(self, detector):
        """Test getting all patterns."""
        patterns = detector.get_patterns()
        
        assert len(patterns) == 3
        assert all(isinstance(p, str) for p in patterns)
    
    def test_invalid_pattern(self):
        """Test handling of invalid regex pattern."""
        # Should not raise, just skip invalid pattern
        detector = RegexMessageDetector([
            r"(?i)push\s+([\w-]+)",
            r"[invalid regex",  # Invalid pattern
        ])
        
        # Should still work with valid pattern
        result = detector.detect("push valid-job", [])
        assert result.is_push_request is True


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""
    
    def test_default_values(self):
        """Test default values."""
        result = DetectionResult(is_push_request=True)
        
        assert result.is_push_request is True
        assert result.job_id is None
        assert result.has_attachment is False
        assert result.confidence == 1.0
    
    def test_all_values(self):
        """Test with all values set."""
        result = DetectionResult(
            is_push_request=True,
            job_id="test-123",
            has_attachment=True,
            confidence=0.95
        )
        
        assert result.is_push_request is True
        assert result.job_id == "test-123"
        assert result.has_attachment is True
        assert result.confidence == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
