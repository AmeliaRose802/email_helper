"""
Tests for error handling utilities and exception hierarchy.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from datetime import datetime

from backend.core.infrastructure.exceptions import (
    EmailHelperError,
    AIServiceUnavailableError,
    EmailNotFoundError,
    ValidationError,
    DatabaseConnectionError,
    RateLimitError
)
from backend.core.infrastructure.error_utils import (
    standardized_error_handler,
    safe_execute
)


class TestExceptionHierarchy:
    """Test custom exception classes."""
    
    def test_base_exception_creation(self):
        """Test creating base EmailHelperError."""
        error = EmailHelperError(
            message="Test error",
            details={'key': 'value'},
            user_message="User friendly message",
            recoverable=True
        )
        
        assert error.message == "Test error"
        assert error.details == {'key': 'value'}
        assert error.user_message == "User friendly message"
        assert error.recoverable is True
    
    def test_exception_to_dict(self):
        """Test exception serialization to dictionary."""
        error = EmailHelperError(
            message="Test error",
            details={'email_id': '123'},
            recoverable=True
        )
        
        error_dict = error.to_dict()
        
        assert error_dict['error_type'] == 'EmailHelperError'
        assert error_dict['message'] == 'Test error'
        assert error_dict['details'] == {'email_id': '123'}
        assert error_dict['recoverable'] is True
    
    def test_ai_service_unavailable_error(self):
        """Test AI service unavailable exception."""
        error = AIServiceUnavailableError()
        
        assert error.recoverable is True
        assert "temporarily unavailable" in error.user_message.lower()
    
    def test_email_not_found_error(self):
        """Test email not found exception."""
        error = EmailNotFoundError(
            message="Email abc123 not found",
            details={'email_id': 'abc123'}
        )
        
        assert error.user_message == "Email not found."
        assert error.details['email_id'] == 'abc123'
    
    def test_validation_error_with_field(self):
        """Test validation error with field specification."""
        error = ValidationError(
            message="Invalid email format",
            field="email_address"
        )
        
        assert error.details['field'] == 'email_address'
        assert "email_address" in error.user_message
    
    def test_rate_limit_error_with_retry_after(self):
        """Test rate limit error with retry_after."""
        error = RateLimitError(retry_after=60)
        
        assert error.recoverable is True
        assert error.details['retry_after'] == 60
        assert "60 seconds" in error.user_message


class TestStandardizedErrorHandler:
    """Test standardized error handling function."""
    
    def test_basic_error_handling(self):
        """Test basic error handling."""
        error = ValueError("Test error")
        result = standardized_error_handler(
            operation_name="Test Operation",
            error=error
        )
        
        assert result['success'] is False
        assert result['error'] == "Invalid data provided"
        assert result['details'] == "Test error"
        assert 'error_info' in result
        assert result['error_info']['operation'] == "Test Operation"
    
    def test_error_handling_with_context(self):
        """Test error handling with context."""
        error = Exception("Test error")
        context = {'user_id': '123', 'action': 'test'}
        
        result = standardized_error_handler(
            operation_name="Test Operation",
            error=error,
            context=context
        )
        
        assert result['error_info']['context'] == context
    
    def test_custom_user_message(self):
        """Test error handling with custom user message."""
        error = Exception("Technical error")
        user_message = "Something went wrong, please try again"
        
        result = standardized_error_handler(
            operation_name="Test Operation",
            error=error,
            user_message=user_message
        )
        
        assert result['error'] == user_message
    
    def test_email_helper_error_handling(self):
        """Test handling of EmailHelperError exceptions."""
        error = AIServiceUnavailableError()
        
        result = standardized_error_handler(
            operation_name="AI Classification",
            error=error
        )
        
        assert result['recoverable'] is True
        assert result['error'] == error.user_message


class TestSafeExecute:
    """Test safe_execute utility function."""
    
    def test_successful_execution(self):
        """Test safe execution with successful function."""
        def test_func(x, y):
            return x + y
        
        result = safe_execute(
            operation_name="Add Numbers",
            func=test_func,
            x=5,
            y=3
        )
        
        assert result == 8
    
    def test_failed_execution_with_fallback(self):
        """Test safe execution with error and fallback value."""
        def test_func():
            raise ValueError("Test error")
        
        result = safe_execute(
            operation_name="Test Operation",
            func=test_func,
            fallback_value="fallback"
        )
        
        assert result == "fallback"
    
    def test_failed_execution_with_raise(self):
        """Test safe execution with raise_on_error=True."""
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            safe_execute(
                operation_name="Test Operation",
                func=test_func,
                raise_on_error=True
            )


class TestWithErrorHandlingDecorator:
    """Test with_error_handling decorator."""
    
    def test_decorator_with_successful_function(self):
        """Test decorator with successful function execution."""
        @with_error_handling(operation_name="Test Operation")
        def test_func(x):
            return x * 2
        
        result = test_func(5)
        assert result == 10
    
    def test_decorator_with_error_and_fallback(self):
        """Test decorator with error and fallback value."""
        @with_error_handling(
            operation_name="Test Operation",
            fallback_value="fallback",
            raise_on_error=False
        )
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        assert result == "fallback"
    
    def test_decorator_with_error_and_raise(self):
        """Test decorator with raise_on_error=True."""
        @with_error_handling(operation_name="Test Operation", raise_on_error=True)
        def test_func():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            test_func()


class TestErrorBoundary:
    """Test error_boundary context manager."""
    
    def test_error_boundary_with_success(self):
        """Test error boundary with successful code."""
        result = None
        with error_boundary("Test Operation"):
            result = 42
        
        assert result == 42
    
    def test_error_boundary_with_error_and_raise(self):
        """Test error boundary with error and raise_on_error=True."""
        with pytest.raises(ValueError):
            with error_boundary("Test Operation", raise_on_error=True):
                raise ValueError("Test error")
    
    def test_error_boundary_with_error_and_suppress(self):
        """Test error boundary with error suppression."""
        result = "before"
        with error_boundary("Test Operation", raise_on_error=False):
            result = "during"
            raise ValueError("Test error")
        
        # Error was suppressed, variable was set before error
        assert result == "during"


class TestRetryOnError:
    """Test retry_on_error decorator."""
    
    def test_retry_success_on_first_attempt(self):
        """Test successful execution on first attempt."""
        call_count = 0
        
        @retry_on_error(max_retries=3)
        def test_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 1
    
    def test_retry_success_after_failures(self):
        """Test successful execution after some failures."""
        call_count = 0
        
        @retry_on_error(max_retries=3, delay_seconds=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Test error")
            return "success"
        
        result = test_func()
        assert result == "success"
        assert call_count == 3
    
    def test_retry_max_attempts_exceeded(self):
        """Test max retry attempts exceeded."""
        call_count = 0
        
        @retry_on_error(max_retries=2, delay_seconds=0.01)
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Test error")
        
        with pytest.raises(ConnectionError):
            test_func()
        
        assert call_count == 3  # Initial attempt + 2 retries
    
    def test_retry_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        call_count = 0
        
        @retry_on_error(max_retries=3, retry_on=(ConnectionError,))
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Non-retryable error")
        
        with pytest.raises(ValueError):
            test_func()
        
        assert call_count == 1  # No retries for ValueError


class TestErrorAggregator:
    """Test ErrorAggregator class."""
    
    def test_aggregator_initialization(self):
        """Test aggregator initialization."""
        aggregator = ErrorAggregator("Test Operation")
        
        assert aggregator.operation_context == "Test Operation"
        assert not aggregator.has_errors()
        assert aggregator.error_count() == 0
    
    def test_add_error(self):
        """Test adding errors to aggregator."""
        aggregator = ErrorAggregator("Test Operation")
        
        aggregator.add_error(ValueError("Error 1"))
        aggregator.add_error(ConnectionError("Error 2"))
        
        assert aggregator.has_errors()
        assert aggregator.error_count() == 2
    
    def test_get_report(self):
        """Test generating error report."""
        aggregator = ErrorAggregator("Batch Processing")
        
        aggregator.add_error(
            ValueError("Error 1"),
            context={'item_id': '1'}
        )
        aggregator.add_error(
            ConnectionError("Error 2"),
            context={'item_id': '2'}
        )
        
        report = aggregator.get_report()
        
        assert report['operation_context'] == "Batch Processing"
        assert report['total_errors'] == 2
        assert 'ValueError' in report['error_types']
        assert 'ConnectionError' in report['error_types']
        assert len(report['errors']) == 2
    
    def test_clear_errors(self):
        """Test clearing aggregated errors."""
        aggregator = ErrorAggregator("Test Operation")
        
        aggregator.add_error(ValueError("Error 1"))
        assert aggregator.has_errors()
        
        aggregator.clear()
        assert not aggregator.has_errors()
        assert aggregator.error_count() == 0


class TestGracefulDegradation:
    """Test graceful_degradation function."""
    
    def test_primary_function_success(self):
        """Test successful execution of primary function."""
        def primary():
            return "primary"
        
        def fallback():
            return "fallback"
        
        func = graceful_degradation(
            primary_func=primary,
            fallback_func=fallback
        )
        
        result = func()
        assert result == "primary"
    
    def test_fallback_function_used(self):
        """Test fallback function is used when primary fails."""
        def primary():
            raise ValueError("Primary failed")
        
        def fallback():
            return "fallback"
        
        func = graceful_degradation(
            primary_func=primary,
            fallback_func=fallback
        )
        
        result = func()
        assert result == "fallback"
    
    def test_fallback_value_used(self):
        """Test fallback value is used when both functions fail."""
        def primary():
            raise ValueError("Primary failed")
        
        def fallback():
            raise ValueError("Fallback failed")
        
        func = graceful_degradation(
            primary_func=primary,
            fallback_func=fallback,
            fallback_value="default"
        )
        
        result = func()
        assert result == "default"
    
    def test_error_raised_without_fallback(self):
        """Test error is raised when no fallback is available."""
        def primary():
            raise ValueError("Primary failed")
        
        func = graceful_degradation(primary_func=primary)
        
        with pytest.raises(ValueError):
            func()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
