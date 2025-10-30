"""AI Client Interface and Implementations.

This module provides an abstraction layer for AI service providers,
enabling easy mocking, testing, and swapping of AI backends.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AIClient(ABC):
    """Abstract interface for AI service clients.
    
    This interface abstracts the underlying AI service provider (Azure OpenAI,
    OpenAI, mock, etc.) to enable testing without real API calls and make it
    easy to swap implementations.
    """
    
    @abstractmethod
    def execute_prompt(
        self, 
        prompt_path: str, 
        inputs: Dict[str, Any],
        require_json: bool = False
    ) -> Any:
        """Execute a prompt template with given inputs.
        
        Args:
            prompt_path: Path to the prompt template file
            inputs: Dictionary of input variables for the template
            require_json: Whether to enforce JSON response format
            
        Returns:
            AI response - type depends on prompt template (dict, str, etc.)
            
        Raises:
            RuntimeError: If prompt execution fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI client is available and configured.
        
        Returns:
            True if client can be used, False otherwise
        """
        pass


class MockAIClient(AIClient):
    """Mock AI client for testing without real API calls.
    
    This client returns predefined responses based on the prompt file
    and inputs, allowing for fast offline testing.
    """
    
    def __init__(self, responses: Optional[Dict[str, Any]] = None):
        """Initialize mock client with optional predefined responses.
        
        Args:
            responses: Optional dictionary mapping prompt names to responses
        """
        self.responses = responses or {}
        self.call_history = []
        
    def execute_prompt(
        self, 
        prompt_path: str, 
        inputs: Dict[str, Any],
        require_json: bool = False
    ) -> Any:
        """Return mock response based on prompt file.
        
        Records call history for test verification.
        """
        # Record call for testing
        self.call_history.append({
            'prompt_path': prompt_path,
            'inputs': inputs,
            'require_json': require_json
        })
        
        # Extract prompt name from path (handle both / and \ path separators)
        import os
        prompt_name = os.path.basename(prompt_path).replace('.prompty', '')
        
        # Return predefined response if available
        if prompt_name in self.responses:
            return self.responses[prompt_name]
        
        # Return default mock responses based on prompt type
        if 'classifier' in prompt_name or 'classification' in prompt_name:
            return {
                'category': 'work_relevant',
                'confidence': 0.8,
                'explanation': 'Mock classification',
                'alternatives': []
            }
        elif 'action' in prompt_name:
            return {
                'due_date': 'No specific deadline',
                'action_required': 'Review email',
                'explanation': 'Mock action extraction',
                'relevance': 'Work related',
                'links': []
            }
        elif 'summary' in prompt_name:
            return "Mock email summary"
        elif 'holistic' in prompt_name or 'dedup' in prompt_name:
            return {
                'truly_relevant_actions': [],
                'superseded_actions': [],
                'duplicate_groups': [],
                'expired_items': []
            }
        else:
            return {'result': 'Mock response'}
    
    def is_available(self) -> bool:
        """Mock client is always available."""
        return True
    
    def get_call_count(self, prompt_name: Optional[str] = None) -> int:
        """Get number of times a prompt was called.
        
        Args:
            prompt_name: Optional prompt name to filter by
            
        Returns:
            Call count
        """
        if prompt_name is None:
            return len(self.call_history)
        return sum(1 for call in self.call_history 
                  if prompt_name in call['prompt_path'])
    
    def reset_history(self):
        """Clear call history."""
        self.call_history = []


class AzureOpenAIClient(AIClient):
    """Azure OpenAI client implementation.
    
    This client uses Azure OpenAI services via the prompty library
    to execute prompt templates.
    """
    
    def __init__(self, azure_config=None):
        """Initialize Azure OpenAI client with configuration.
        
        Args:
            azure_config: Optional AzureConfig instance. If None, loads from environment.
        """
        if azure_config is None:
            from azure_config import get_azure_config
            self.azure_config = get_azure_config()
        else:
            self.azure_config = azure_config
        
        self._available = None
    
    def execute_prompt(
        self, 
        prompt_path: str, 
        inputs: Dict[str, Any],
        require_json: bool = False
    ) -> Any:
        """Execute prompt using Azure OpenAI via prompty library.
        
        Args:
            prompt_path: Path to the .prompty template file
            inputs: Dictionary of input variables
            require_json: Whether to enforce JSON response format
            
        Returns:
            AI response from Azure OpenAI
            
        Raises:
            RuntimeError: If execution fails
        """
        import os
        import json
        
        logger.debug(f"[Azure AI Client] Executing {prompt_path}")
        
        try:
            # Try promptflow.core first
            from promptflow.core import Prompty
            logger.info(f"[Azure AI Client] Using promptflow.core for {prompt_path}")
            model_config = self.azure_config.get_promptflow_config()
            prompty_instance = Prompty.load(prompt_path, model={'configuration': model_config})
            result = prompty_instance(**inputs)
            logger.info(f"[Azure AI Client] [OK] {prompt_path} completed")
            return result
            
        except ImportError:
            try:
                # Fall back to prompty library
                import prompty
                import prompty.azure
                
                logger.info(f"[Azure AI Client] Using prompty library for {prompt_path}")
                
                p = prompty.load(prompt_path)
                p.model.configuration["azure_endpoint"] = self.azure_config.endpoint
                p.model.configuration["azure_deployment"] = self.azure_config.deployment  
                p.model.configuration["api_version"] = self.azure_config.api_version
                
                # Enforce JSON format if required
                if require_json:
                    if not hasattr(p.model, 'parameters'):
                        p.model.parameters = {}
                    p.model.parameters["response_format"] = {"type": "json_object"}
                    logger.info(f"[Azure AI Client] Enforcing JSON format")
                
                # Set up authentication
                if self.azure_config.use_azure_credential():
                    from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                    token_provider = get_bearer_token_provider(
                        DefaultAzureCredential(), 
                        "https://cognitiveservices.azure.com/.default"
                    )
                    p.model.configuration["azure_ad_token_provider"] = token_provider
                    if "api_key" in p.model.configuration:
                        del p.model.configuration["api_key"]
                else:
                    p.model.configuration["api_key"] = self.azure_config.get_api_key()
                
                result = prompty.run(p, inputs=inputs)
                
                # Log response type for diagnostics
                if isinstance(result, str):
                    try:
                        json.loads(result)
                        logger.info(f"[Azure AI Client] [OK] Returned JSON string")
                    except:
                        logger.warning(f"[Azure AI Client] [WARN] Returned plain text")
                elif isinstance(result, dict):
                    logger.info(f"[Azure AI Client] [OK] Returned dict")
                
                return result
                
            except ImportError as e:
                logger.error(f"[Azure AI Client] Prompty library not available: {e}")
                raise RuntimeError(f"Prompty library unavailable: {e}")
                
        except Exception as e:
            # Check for content filter errors
            error_str = str(e).lower()
            is_content_filter = any(phrase in error_str for phrase in [
                'content_filter', 'content management policy', 'responsibleaipolicyviolation',
                'jailbreak', 'filtered', 'badrequeesterror'
            ])
            
            if is_content_filter:
                logger.warning(f"[Azure AI Client] Content filter blocked: {str(e)[:200]}")
                raise RuntimeError(f"Content filter violation: {str(e)[:200]}")
            else:
                logger.error(f"[Azure AI Client] Execution failed: {type(e).__name__}: {str(e)[:200]}")
                raise RuntimeError(f"Prompt execution failed: {e}")
    
    def is_available(self) -> bool:
        """Check if Azure OpenAI is configured and available."""
        if self._available is not None:
            return self._available
        
        try:
            # Check if we have required configuration
            has_config = (
                self.azure_config is not None and
                hasattr(self.azure_config, 'endpoint') and
                hasattr(self.azure_config, 'deployment')
            )
            
            if not has_config:
                self._available = False
                return False
            
            # Check if prompty libraries are available
            try:
                import prompty
                self._available = True
                return True
            except ImportError:
                try:
                    from promptflow.core import Prompty
                    self._available = True
                    return True
                except ImportError:
                    logger.warning("[Azure AI Client] Prompty libraries not available")
                    self._available = False
                    return False
                    
        except Exception as e:
            logger.warning(f"[Azure AI Client] Availability check failed: {e}")
            self._available = False
            return False
