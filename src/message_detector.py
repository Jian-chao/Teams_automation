"""
Message detector module with replaceable interface for future LLM integration.
"""
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class DetectionResult:
    """
    Result of message detection.
    
    Attributes:
        is_push_request: Whether the message is a push job request
        job_id: Extracted job ID (may be None if not found)
        has_attachment: Whether the message has attachments/screenshots
        confidence: Confidence score (1.0 for regex, varies for LLM)
    """
    is_push_request: bool
    job_id: Optional[str] = None
    has_attachment: bool = False
    confidence: float = 1.0


class MessageDetectorInterface(ABC):
    """
    Abstract interface for message detection.
    
    Implement this interface to create custom detectors.
    Can be replaced with LLM-based detector in the future.
    """
    
    @abstractmethod
    def detect(self, message_content: str, attachments: list) -> DetectionResult:
        """
        Detect if a message is a push job request.
        
        Args:
            message_content: The text content of the message
            attachments: List of message attachments
            
        Returns:
            DetectionResult with detection outcome
        """
        pass


class RegexMessageDetector(MessageDetectorInterface):
    """
    Regex-based message detector.
    
    Uses configurable regex patterns to identify push job requests
    and extract job IDs.
    """
    
    def __init__(self, patterns: List[str]):
        """
        Initialize with regex patterns.
        
        Args:
            patterns: List of regex pattern strings.
                     Each pattern should have a capture group for job ID.
        """
        self.patterns = []
        for p in patterns:
            try:
                self.patterns.append(re.compile(p))
            except re.error as e:
                print(f"Warning: Invalid regex pattern '{p}': {e}")
    
    def detect(self, message_content: str, attachments: list) -> DetectionResult:
        """
        Detect push request using regex patterns.
        
        Tries each pattern in order until a match is found.
        
        Args:
            message_content: The text content of the message
            attachments: List of message attachments
            
        Returns:
            DetectionResult with detection outcome
        """
        if not message_content:
            return DetectionResult(is_push_request=False)
        
        # Try each pattern
        for pattern in self.patterns:
            match = pattern.search(message_content)
            if match:
                # Extract job ID from first capture group if exists
                job_id = None
                if match.groups():
                    job_id = match.group(1)
                
                return DetectionResult(
                    is_push_request=True,
                    job_id=job_id,
                    has_attachment=len(attachments) > 0 if attachments else False,
                    confidence=1.0
                )
        
        return DetectionResult(is_push_request=False)
    
    def add_pattern(self, pattern: str) -> bool:
        """
        Add a new pattern at runtime.
        
        Args:
            pattern: Regex pattern string
            
        Returns:
            True if pattern was added successfully
        """
        try:
            self.patterns.append(re.compile(pattern))
            return True
        except re.error:
            return False
    
    def get_patterns(self) -> List[str]:
        """
        Get all current patterns.
        
        Returns:
            List of pattern strings
        """
        return [p.pattern for p in self.patterns]


class LLMMessageDetector(MessageDetectorInterface):
    """
    LLM-based message detector (placeholder for future implementation).
    
    This class provides the interface for LLM-based detection.
    Implement the detect method with your LLM of choice.
    """
    
    def __init__(self, llm_client=None, system_prompt: str = None):
        """
        Initialize LLM detector.
        
        Args:
            llm_client: LLM client instance (e.g., OpenAI, Azure OpenAI)
            system_prompt: Custom system prompt for the LLM
        """
        self.llm_client = llm_client
        self.system_prompt = system_prompt or self._default_prompt()
    
    def _default_prompt(self) -> str:
        """Get default system prompt for push detection."""
        return """You are a message analyzer. 
Determine if the message is asking someone to push/prioritize a job.
If yes, extract the job ID if mentioned.
Respond in JSON format: {"is_push_request": true/false, "job_id": "extracted_id_or_null"}"""
    
    def detect(self, message_content: str, attachments: list) -> DetectionResult:
        """
        Detect push request using LLM.
        
        Args:
            message_content: The text content of the message
            attachments: List of message attachments
            
        Returns:
            DetectionResult with detection outcome
            
        Raises:
            NotImplementedError: LLM implementation pending
        """
        # TODO: Implement LLM-based detection
        # Example implementation:
        # response = self.llm_client.chat.completions.create(
        #     messages=[
        #         {"role": "system", "content": self.system_prompt},
        #         {"role": "user", "content": message_content}
        #     ]
        # )
        # result = json.loads(response.choices[0].message.content)
        # return DetectionResult(
        #     is_push_request=result["is_push_request"],
        #     job_id=result.get("job_id"),
        #     has_attachment=len(attachments) > 0,
        #     confidence=0.9
        # )
        raise NotImplementedError(
            "LLM detector not implemented. "
            "Please implement with your preferred LLM client."
        )
