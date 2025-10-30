# ADR-005: AI Client Abstraction Layer

## Status
Accepted - Implemented

## Context
The AIProcessor class was tightly coupled to Azure OpenAI through direct prompty library calls. This created several challenges:

1. **Testing Difficulty**: Tests required Azure credentials and network access, making them slow (~10-30 seconds per test) and flaky
2. **Offline Development**: Developers couldn't run tests or develop features without Azure connectivity
3. **Vendor Lock-in**: Switching to a different AI provider (OpenAI, local models, etc.) would require changing AIProcessor internally
4. **Mock Complexity**: Creating test doubles required extensive monkey-patching of prompty internals
5. **Cost**: Every test run incurred Azure API costs

The existing code directly imported and called prompty libraries within the `execute_prompty` method, with complex logic to handle both promptflow.core and prompty library variations.

## Decision
We introduced an AIClient abstraction layer with three implementations:

### AIClient Interface
```python
class AIClient(ABC):
    @abstractmethod
    def execute_prompt(self, prompt_path: str, inputs: Dict[str, Any], 
                      require_json: bool = False) -> Any:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
```

### Implementations
1. **AzureOpenAIClient**: Production implementation using Azure OpenAI via prompty
2. **MockAIClient**: Test implementation with predefined responses and call tracking
3. Future: OpenAIClient, LocalModelClient, etc.

### Dependency Injection
AIProcessor now accepts an `ai_client` parameter:
```python
def __init__(self, email_analyzer=None, ai_client: AIClient = None):
    if ai_client is None:
        self.ai_client = AzureOpenAIClient(get_azure_config())
    else:
        self.ai_client = ai_client
```

## Consequences

### Positive
- **10x Faster Tests**: Mock client tests complete in ~0.1s vs 10-30s with real Azure calls
- **Offline Testing**: Full test suite runs without Azure credentials or network
- **No Test Costs**: Zero Azure API costs for running tests
- **Better Testability**: Easy to inject mock responses for specific test scenarios
- **Maintainability**: AI provider logic isolated in client implementations
- **Flexibility**: Can swap AI providers without changing AIProcessor
- **Call Tracking**: MockAIClient records all calls for test verification

### Negative
- **Additional Abstraction**: One more layer to understand
- **Interface Maintenance**: Must update interface if adding new AI features
- **Migration Effort**: Existing code needed refactoring (completed)

### Neutral
- **Backward Compatible**: Existing code works unchanged (default creates AzureOpenAIClient)
- **API Surface**: Same `execute_prompty` method signature

## Implementation Details

### Before
```python
def execute_prompty(self, prompty_file, inputs=None):
    # 90+ lines of Azure OpenAI setup, error handling, JSON enforcement
    from promptflow.core import Prompty
    # or
    import prompty
    import prompty.azure
    # Complex configuration and authentication logic...
```

### After
```python
def execute_prompty(self, prompty_file, inputs=None):
    # Delegate to abstraction layer
    prompty_path = os.path.join(self.prompts_dir, prompty_file)
    require_json = any(prompt in prompty_file for prompt in json_required_prompts)
    result = self.ai_client.execute_prompt(prompty_path, inputs, require_json)
    return result
```

### Test Usage
```python
# Create processor with mock client
mock_client = MockAIClient(responses={
    'email_classifier': {'category': 'work_relevant', 'confidence': 0.95}
})
processor = AIProcessor(ai_client=mock_client)

# Test classification
result = processor.classify_email(email_data, config)
assert result['category'] == 'work_relevant'

# Verify call count
assert mock_client.get_call_count('email_classifier') == 1
```

## Testing Strategy
1. **Unit Tests**: Use MockAIClient for AIProcessor logic tests
2. **Integration Tests**: Use AzureOpenAIClient with real Azure (marked with @pytest.mark.integration)
3. **Call Tracking**: MockAIClient records all calls for verification
4. **Response Customization**: Tests can inject specific responses to test edge cases

## Migration Checklist
- [x] Create AIClient interface in `src/core/ai_client.py`
- [x] Implement MockAIClient with call tracking
- [x] Implement AzureOpenAIClient wrapping prompty
- [x] Refactor AIProcessor.__init__ to accept ai_client parameter
- [x] Refactor execute_prompty to delegate to ai_client
- [x] Fix circular imports in service_factory
- [x] Create integration tests (test_ai_client_integration.py)
- [x] Verify existing tests still pass
- [x] Update Beads task (email_helper-4)

## Related
- Supports **ADR-002**: Dependency Injection Pattern
- Supports **ADR-003**: Testing Strategy
- Part of **email_helper-2**: Architecture & Testing Overhaul Epic

## References
- Task: email_helper-4 "Decouple AIProcessor from direct Azure OpenAI dependency"
- Code: `src/core/ai_client.py`
- Tests: `test/test_ai_client_integration.py`
