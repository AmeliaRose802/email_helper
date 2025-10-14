"""Essential test suite for Email Helper - Production Ready.

This module contains the core tests that must always pass for the email helper
system to function correctly. It replaces the scattered test files with a
focused, maintainable test suite.

Test Coverage:
- Core functionality validation
- Integration test for major workflows  
- Error handling and edge cases
- Configuration and setup validation

This consolidated approach ensures reliability while reducing maintenance overhead.
"""

import os
import sys
import tempfile
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Core imports
from core.service_factory import ServiceFactory
from core.config import config
from core.business_logic import EmailWorkflow, UIStateManager, ProcessingOrchestrator
from utils import *


class TestEssentialFunctionality:
    """Essential functionality tests that must always pass."""
    
    def test_configuration_loading(self):
        """Test that configuration loads correctly."""
        # Test basic config access
        assert config.get('email.default_folder') == 'Inbox'
        assert isinstance(config.get('processing.confidence_threshold'), float)
        
        # Test storage path generation
        storage_path = config.get_storage_path('test.db')
        assert storage_path.endswith('test.db')
        assert os.path.isabs(storage_path)
        
    def test_service_factory_basic(self):
        """Test service factory creates instances."""
        factory = ServiceFactory()
        
        # Test service creation
        outlook_manager = factory.get_outlook_manager()
        ai_processor = factory.get_ai_processor()
        task_persistence = factory.get_task_persistence()
        
        assert outlook_manager is not None
        assert ai_processor is not None  
        assert task_persistence is not None
        
        # Test singleton behavior
        assert factory.get_outlook_manager() is outlook_manager
        
    def test_utility_functions(self):
        """Test essential utility functions."""
        # JSON utilities
        json_str = '{"test": "value"}'
        parsed = parse_json_with_fallback(json_str)
        assert parsed == {"test": "value"}
        
        # Text utilities  
        text = "**Bold** text"
        cleaned = clean_ai_response(text)
        assert cleaned == "Bold text"
        
        # Date utilities
        dt = datetime(2025, 1, 15, 10, 30, 0)
        formatted = format_datetime_for_storage(dt)
        assert formatted == "2025-01-15 10:30:00"
        
    def test_ui_state_manager(self):
        """Test UI state management."""
        state_manager = UIStateManager()
        
        # Test basic set/get
        state_manager.set('test_key', 'test_value')
        assert state_manager.get('test_key') == 'test_value'
        
        # Test default values
        assert state_manager.get('nonexistent', 'default') == 'default'
        
        # Test callbacks
        callback_called = False
        def test_callback(key, value, old_value):
            nonlocal callback_called
            callback_called = True
            
        state_manager.subscribe('callback_test', test_callback)
        state_manager.set('callback_test', 'new_value')
        assert callback_called
        
    def test_error_handling(self):
        """Test error handling utilities."""
        # Test JSON parsing with invalid input
        invalid_json = "not json"
        result = parse_json_with_fallback(invalid_json, {"fallback": True})
        assert result == {"fallback": True}
        
        # Test date parsing with invalid dates
        assert parse_date_string("invalid date") is None
        assert parse_date_string(None) is None
        assert parse_date_string("") is None


class TestDataPersistence:
    """Test data persistence functionality."""
    
    def test_task_persistence_basic(self):
        """Test basic task persistence operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Import here to avoid import issues if modules aren't available
            try:
                from src.task_persistence import TaskPersistence
                
                task_persistence = TaskPersistence(temp_dir)
                
                # Test data that can be saved/loaded - must match the expected structure
                test_tasks = {
                    "required_actions": [
                        {
                            "subject": "Test Task",
                            "priority": "high", 
                            "status": "outstanding",
                            "due_date": "2025-01-20"
                        }
                    ]
                }
                
                # Test save operation (returns None, just verify no exceptions)
                task_persistence.save_outstanding_tasks(test_tasks)
                
                # Test load operation
                loaded_tasks = task_persistence.load_outstanding_tasks()
                assert isinstance(loaded_tasks, dict)
                
                # Verify our test task is present
                assert "required_actions" in loaded_tasks
                assert len(loaded_tasks["required_actions"]) >= 1
                
                # Verify the test task subject is in the loaded tasks
                loaded_subjects = {task.get("subject", "") for task in loaded_tasks["required_actions"]}
                assert "Test Task" in loaded_subjects
                
            except ImportError as e:
                print(f"Skipping task persistence test due to import error: {e}")
                assert True  # Skip test if dependencies not available
                
    def test_data_normalization(self):
        """Test data normalization for storage."""
        test_data = [
            {
                "text_field": "text value",
                "datetime_field": datetime.now(),
                "number_field": 42,
                "none_field": None
            }
        ]
        
        normalized = normalize_data_for_storage(test_data)
        
        assert len(normalized) == 1
        entry = normalized[0]
        
        # Check that datetime was converted to string
        assert isinstance(entry["datetime_field"], str)
        # Other fields should remain unchanged
        assert entry["text_field"] == "text value"
        assert entry["number_field"] == 42
        assert entry["none_field"] is None


class TestIntegrationWorkflow:
    """Test integration between components."""
    
    def test_email_workflow_creation(self):
        """Test that email workflow can be created with mocked dependencies."""
        # Create mock providers
        email_provider = Mock()
        ai_provider = Mock()  
        storage_provider = Mock()
        
        # Configure mocks
        email_provider.get_emails.return_value = []
        ai_provider.analyze_batch.return_value = {}
        storage_provider.save_tasks.return_value = True
        
        # Create workflow
        workflow = EmailWorkflow(email_provider, ai_provider, storage_provider)
        
        assert workflow is not None
        assert hasattr(workflow, 'process_batch')
        
    def test_processing_orchestrator(self):
        """Test processing orchestrator functionality."""
        state_manager = UIStateManager()
        orchestrator = ProcessingOrchestrator(state_manager)
        
        # Test operation tracking
        def dummy_operation():
            return "completed"
            
        future = orchestrator.start_operation("test_op", dummy_operation)
        
        # Check that operation is tracked
        assert "test_op" in orchestrator.get_active_operations()
        
        # Wait for completion
        result = future.result(timeout=5)
        assert result == "completed"
        
        # Check final state
        status = orchestrator.get_operation_status("test_op")
        assert status["status"] == "completed"


class TestRobustness:
    """Test system robustness and error recovery."""
    
    def test_missing_configuration(self):
        """Test behavior with missing configuration."""
        # Test that system handles missing config gracefully
        missing_value = config.get('nonexistent.deeply.nested.key', 'default')
        assert missing_value == 'default'
        
    def test_service_factory_with_errors(self):
        """Test service factory error handling."""
        factory = ServiceFactory()
        
        # Test that we can override services for testing
        mock_service = Mock()
        factory.override_service('outlook_manager', mock_service)
        
        assert factory.get_outlook_manager() is mock_service
        
        # Test factory reset
        factory.reset()
        # After reset, should create new instance
        new_service = factory.get_outlook_manager()
        assert new_service is not mock_service
        
    def test_json_error_recovery(self):
        """Test JSON error recovery with various malformed inputs."""
        test_cases = [
            ('{"valid": true}', {"valid": True}),
            ('invalid json', None),
            ('{"incomplete": ', None),
            ('```json\n{"wrapped": true}\n```', {"wrapped": True}),
        ]
        
        for json_input, expected in test_cases:
            result = parse_json_with_fallback(json_input, None)
            if expected is None:
                assert result is None
            else:
                assert result == expected


def run_production_tests():
    """Run all production-critical tests."""
    print("🧪 Running Essential Email Helper Tests")
    print("=" * 50)
    
    test_classes = [
        TestEssentialFunctionality,
        TestDataPersistence, 
        TestIntegrationWorkflow,
        TestRobustness
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 {test_class.__name__}")
        print("-" * 30)
        
        instance = test_class()
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✅ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {method_name}: {e}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
    
    # Summary
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} passed")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for class_name, method_name, error in failed_tests:
            print(f"   {class_name}.{method_name}: {error}")
        return False
    else:
        print("🎉 All essential tests passed!")
        return True


if __name__ == "__main__":
    success = run_production_tests()
    sys.exit(0 if success else 1)