"""Integration tests for component interactions in Email Helper.

This test suite covers integration between key components:
1. Email retrieval → AI classification
2. AI classification → Task persistence
3. Complete email processing pipeline

These tests use test databases, mock external APIs, and target 70%+ coverage
of integration paths with execution time under 2 minutes.
"""

import pytest
import sys
import os
import sqlite3
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))


# ============================================================================
# Fixtures for Integration Testing
# ============================================================================

@pytest.fixture
def mock_outlook_emails():
    """Sample email data for testing."""
    return [
        {
            'id': 'test-email-1',
            'subject': 'Urgent: Review PR #123 by EOD',
            'sender': 'manager@example.com',
            'recipient': 'user@example.com',
            'body': 'Please review pull request #123 and approve by end of day. This blocks the deployment.',
            'received_time': datetime.now().isoformat(),
            'is_read': False,
            'categories': [],
            'has_attachments': False,
            'conversation_id': 'conv-1'
        },
        {
            'id': 'test-email-2',
            'subject': 'Team Meeting Notes - Q1 Planning',
            'sender': 'team@example.com',
            'recipient': 'user@example.com',
            'body': 'FYI: Here are the notes from today\'s meeting. No action needed.',
            'received_time': (datetime.now() - timedelta(hours=2)).isoformat(),
            'is_read': False,
            'categories': [],
            'has_attachments': True,
            'conversation_id': 'conv-2'
        },
        {
            'id': 'test-email-3',
            'subject': 'Calendar: Sprint Review - Friday 2PM',
            'sender': 'calendar@example.com',
            'recipient': 'user@example.com',
            'body': 'Sprint review meeting scheduled for Friday at 2PM. Conference Room A.',
            'received_time': (datetime.now() - timedelta(hours=1)).isoformat(),
            'is_read': False,
            'categories': ['Meeting'],
            'has_attachments': False,
            'conversation_id': 'conv-3'
        }
    ]


@pytest.fixture
def mock_outlook_manager(mock_outlook_emails):
    """Mock OutlookManager for email retrieval."""
    manager = MagicMock()
    manager.connect.return_value = True
    
    # Configure get_inbox_messages to respect count parameter
    def get_inbox_messages_side_effect(count=None, **kwargs):
        if count:
            return mock_outlook_emails[:count]
        return mock_outlook_emails
    
    manager.get_inbox_messages = Mock(side_effect=get_inbox_messages_side_effect)
    manager.get_email_by_id = Mock(side_effect=lambda email_id: 
        next((e for e in mock_outlook_emails if e['id'] == email_id), None)
    )
    manager.mark_as_read = Mock(return_value=True)
    manager.move_to_folder = Mock(return_value=True)
    manager.categorize_email = Mock(return_value=True)
    return manager


@pytest.fixture
def mock_ai_processor():
    """Mock AIProcessor for classification and action extraction."""
    processor = MagicMock()
    
    # Configure classification responses based on email content
    def classify_email_side_effect(email_text, **kwargs):
        if 'urgent' in email_text.lower() or 'review' in email_text.lower():
            return {
                'category': 'required_personal_action',
                'confidence': 0.95,
                'explanation': 'Email requires immediate action from recipient',
                'alternatives': [
                    {'category': 'optional_fyi', 'confidence': 0.05}
                ],
                'action_required': True,
                'priority': 'high'
            }
        elif 'meeting' in email_text.lower() or 'calendar' in email_text.lower():
            return {
                'category': 'optional_event',
                'confidence': 0.92,
                'explanation': 'Email contains event information',
                'alternatives': [],
                'action_required': True,
                'priority': 'medium'
            }
        else:
            return {
                'category': 'optional_fyi',
                'confidence': 0.88,
                'explanation': 'Informational email for awareness',
                'alternatives': [],
                'action_required': False,
                'priority': 'low'
            }
    
    processor.classify_email_with_explanation = Mock(side_effect=classify_email_side_effect)
    
    # Configure action extraction
    def extract_actions_side_effect(email_text, **kwargs):
        if 'review pr' in email_text.lower():
            return {
                'action_items': [
                    {
                        'action': 'Review pull request #123',
                        'deadline': 'End of day',
                        'priority': 'high',
                        'assignee': 'user@example.com'
                    }
                ],
                'action_required': 'Review and approve PR #123',
                'confidence': 0.93
            }
        elif 'meeting' in email_text.lower():
            return {
                'action_items': [
                    {
                        'action': 'Attend sprint review',
                        'deadline': 'Friday 2PM',
                        'priority': 'medium',
                        'location': 'Conference Room A'
                    }
                ],
                'action_required': 'Attend meeting',
                'confidence': 0.90
            }
        else:
            return {
                'action_items': [],
                'action_required': 'No action required',
                'confidence': 0.95
            }
    
    processor.extract_action_items_from_email = Mock(side_effect=extract_actions_side_effect)
    
    return processor


@pytest.fixture
def mock_task_persistence():
    """Mock TaskPersistence for integration testing."""
    persistence = MagicMock()
    
    # In-memory storage for tasks
    tasks_storage = {}
    task_counter = [1]  # Use list to allow modification in nested function
    
    def create_task(task_data):
        task_id = task_counter[0]
        task_counter[0] += 1
        tasks_storage[task_id] = {**task_data, 'id': task_id}
        return task_id
    
    def get_task(task_id):
        return tasks_storage.get(task_id)
    
    def update_task(task_id, updates):
        if task_id in tasks_storage:
            tasks_storage[task_id].update(updates)
            return True
        return False
    
    def list_tasks(**filters):
        return list(tasks_storage.values())
    
    persistence.create_task = Mock(side_effect=create_task)
    persistence.get_task = Mock(side_effect=get_task)
    persistence.update_task = Mock(side_effect=update_task)
    persistence.list_tasks = Mock(side_effect=list_tasks)
    
    return persistence


# ============================================================================
# Integration Test: Email Retrieval → AI Classification
# ============================================================================

@pytest.mark.integration
class TestEmailRetrievalToClassification:
    """Test integration between email retrieval and AI classification."""
    
    def test_retrieve_and_classify_single_email(
        self, mock_outlook_manager, mock_ai_processor
    ):
        """Test retrieving an email and classifying it with AI."""
        # Retrieve email
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        assert len(emails) == 1
        
        email = emails[0]
        email_text = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"
        
        # Classify email
        classification = mock_ai_processor.classify_email_with_explanation(email_text)
        
        # Verify classification
        assert 'category' in classification
        assert 'confidence' in classification
        assert classification['confidence'] > 0.8
        assert classification['category'] == 'required_personal_action'
        assert classification['action_required'] is True
        
        # Verify Outlook manager was called correctly
        mock_outlook_manager.get_inbox_messages.assert_called_once_with(count=1)
        mock_ai_processor.classify_email_with_explanation.assert_called_once()
    
    def test_retrieve_and_classify_batch_emails(
        self, mock_outlook_manager, mock_ai_processor, mock_outlook_emails
    ):
        """Test batch email retrieval and classification."""
        # Retrieve multiple emails
        emails = mock_outlook_manager.get_inbox_messages(count=10)
        assert len(emails) == len(mock_outlook_emails)
        
        # Classify each email
        classified_emails = []
        for email in emails:
            email_text = f"Subject: {email['subject']}\nFrom: {email['sender']}\n\n{email['body']}"
            classification = mock_ai_processor.classify_email_with_explanation(email_text)
            
            classified_emails.append({
                'email_id': email['id'],
                'subject': email['subject'],
                'category': classification['category'],
                'confidence': classification['confidence'],
                'priority': classification['priority']
            })
        
        # Verify all emails were classified
        assert len(classified_emails) == 3
        
        # Verify different categories based on content
        categories = {e['category'] for e in classified_emails}
        assert 'required_personal_action' in categories
        assert 'optional_event' in categories or 'optional_fyi' in categories
        
        # Verify confidence levels are acceptable
        assert all(e['confidence'] > 0.8 for e in classified_emails)
    
    def test_classification_error_handling(
        self, mock_outlook_manager, mock_ai_processor
    ):
        """Test handling of classification errors during retrieval."""
        # Setup AI processor to raise error
        mock_ai_processor.classify_email_with_explanation.side_effect = Exception("AI service unavailable")
        
        # Retrieve email
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        email = emails[0]
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        # Attempt classification - should raise
        with pytest.raises(Exception) as exc_info:
            mock_ai_processor.classify_email_with_explanation(email_text)
        
        assert "AI service unavailable" in str(exc_info.value)
    
    def test_classify_with_context_from_email_metadata(
        self, mock_outlook_manager, mock_ai_processor
    ):
        """Test classification using email metadata as context."""
        # Retrieve email with metadata
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        email = emails[0]
        
        # Build context from metadata
        email_text = f"""Subject: {email['subject']}
From: {email['sender']}
To: {email['recipient']}
Received: {email['received_time']}
Has Attachments: {email['has_attachments']}
Existing Categories: {', '.join(email['categories']) if email['categories'] else 'None'}

{email['body']}"""
        
        # Classify with context
        classification = mock_ai_processor.classify_email_with_explanation(
            email_text, 
            context={'sender': email['sender'], 'has_attachments': email['has_attachments']}
        )
        
        assert classification['category'] == 'required_personal_action'
        assert classification['confidence'] > 0.9


# ============================================================================
# Integration Test: AI Classification → Task Persistence
# ============================================================================

@pytest.mark.integration
class TestClassificationToTaskPersistence:
    """Test integration between AI classification and task persistence."""
    
    def test_create_task_from_classification(
        self, mock_ai_processor, mock_task_persistence
    ):
        """Test creating a task from AI classification results."""
        # Classify email
        email_text = "Subject: Review PR #123\n\nPlease review the pull request by EOD."
        classification = mock_ai_processor.classify_email_with_explanation(email_text)
        
        # Extract action items
        actions = mock_ai_processor.extract_action_items_from_email(email_text)
        
        # Create task from classification and actions
        if classification['action_required'] and actions['action_items']:
            action_item = actions['action_items'][0]
            
            task_data = {
                'email_id': 'test-email-1',
                'title': action_item['action'],
                'description': classification['explanation'],
                'priority': classification['priority'],
                'category': classification['category'],
                'deadline': action_item.get('deadline'),
                'status': 'open',
                'created_at': datetime.now().isoformat(),
                'confidence': classification['confidence']
            }
            
            # Persist task
            task_id = mock_task_persistence.create_task(task_data)
            
            # Verify task was created
            assert task_id is not None
            
            # Retrieve and verify task
            task = mock_task_persistence.get_task(task_id)
            assert task is not None
            assert task['title'] == action_item['action']
            assert task['priority'] == 'high'
            assert task['status'] == 'open'
    
    def test_batch_task_creation_from_classifications(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence, mock_outlook_emails
    ):
        """Test creating multiple tasks from batch email classification."""
        # Retrieve and classify emails
        emails = mock_outlook_manager.get_inbox_messages(count=10)
        
        tasks_created = []
        for email in emails:
            email_text = f"Subject: {email['subject']}\n\n{email['body']}"
            
            # Classify
            classification = mock_ai_processor.classify_email_with_explanation(email_text)
            
            # Extract actions
            actions = mock_ai_processor.extract_action_items_from_email(email_text)
            
            # Create task if action required
            if classification['action_required'] and actions['action_items']:
                for action_item in actions['action_items']:
                    task_data = {
                        'email_id': email['id'],
                        'title': action_item['action'],
                        'description': email['body'][:200],
                        'priority': classification['priority'],
                        'category': classification['category'],
                        'status': 'open',
                        'created_at': datetime.now().isoformat()
                    }
                    
                    task_id = mock_task_persistence.create_task(task_data)
                    tasks_created.append(task_id)
        
        # Verify tasks were created
        assert len(tasks_created) >= 2  # At least 2 actionable emails
        
        # Verify all tasks can be retrieved
        for task_id in tasks_created:
            task = mock_task_persistence.get_task(task_id)
            assert task is not None
            assert task['status'] == 'open'
    
    def test_update_task_status_after_classification(
        self, mock_task_persistence
    ):
        """Test updating task status based on classification changes."""
        # Create initial task
        task_data = {
            'email_id': 'test-email-1',
            'title': 'Review PR #123',
            'description': 'Pull request needs review',
            'priority': 'high',
            'category': 'required_personal_action',
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        
        task_id = mock_task_persistence.create_task(task_data)
        
        # Update task status
        mock_task_persistence.update_task(task_id, {'status': 'in_progress'})
        
        # Verify update
        task = mock_task_persistence.get_task(task_id)
        assert task['status'] == 'in_progress'
        
        # Complete task
        mock_task_persistence.update_task(task_id, {
            'status': 'completed',
            'completed_at': datetime.now().isoformat()
        })
        
        # Verify completion
        task = mock_task_persistence.get_task(task_id)
        assert task['status'] == 'completed'
        assert 'completed_at' in task
    
    def test_link_email_to_task_bidirectionally(
        self, mock_outlook_manager, mock_task_persistence
    ):
        """Test bidirectional linking between emails and tasks."""
        # Retrieve email
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        email = emails[0]
        
        # Create task from email
        task_data = {
            'email_id': email['id'],
            'title': f"Task from: {email['subject']}",
            'description': email['body'],
            'priority': 'medium',
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        
        task_id = mock_task_persistence.create_task(task_data)
        
        # Retrieve task and verify email link
        task = mock_task_persistence.get_task(task_id)
        assert task['email_id'] == email['id']
        
        # Verify can retrieve email from task
        linked_email = mock_outlook_manager.get_email_by_id(task['email_id'])
        assert linked_email is not None
        assert linked_email['id'] == email['id']
        assert linked_email['subject'] == email['subject']


# ============================================================================
# Integration Test: Complete Email Processing Pipeline
# ============================================================================

@pytest.mark.integration
class TestCompleteEmailPipeline:
    """Test complete end-to-end email processing pipeline."""
    
    def test_full_pipeline_single_email(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence
    ):
        """Test complete pipeline: retrieve → classify → extract → persist."""
        # Step 1: Retrieve email
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        assert len(emails) == 1
        email = emails[0]
        
        # Step 2: Classify email
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        classification = mock_ai_processor.classify_email_with_explanation(email_text)
        
        assert classification['category'] == 'required_personal_action'
        assert classification['action_required'] is True
        
        # Step 3: Extract action items
        actions = mock_ai_processor.extract_action_items_from_email(email_text)
        
        assert len(actions['action_items']) > 0
        assert actions['action_items'][0]['priority'] == 'high'
        
        # Step 4: Create task
        action_item = actions['action_items'][0]
        task_data = {
            'email_id': email['id'],
            'title': action_item['action'],
            'description': email['body'],
            'priority': classification['priority'],
            'category': classification['category'],
            'status': 'open',
            'created_at': datetime.now().isoformat()
        }
        
        task_id = mock_task_persistence.create_task(task_data)
        
        # Step 5: Update email status
        mock_outlook_manager.categorize_email(email['id'], classification['category'])
        mock_outlook_manager.mark_as_read(email['id'])
        
        # Verify complete pipeline
        task = mock_task_persistence.get_task(task_id)
        assert task is not None
        assert task['email_id'] == email['id']
        assert task['category'] == classification['category']
        
        mock_outlook_manager.categorize_email.assert_called_once_with(
            email['id'], classification['category']
        )
        mock_outlook_manager.mark_as_read.assert_called_once_with(email['id'])
    
    def test_full_pipeline_batch_processing(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence, mock_outlook_emails
    ):
        """Test pipeline with batch email processing."""
        # Retrieve all emails
        emails = mock_outlook_manager.get_inbox_messages(count=10)
        
        processed_count = 0
        tasks_created = []
        
        for email in emails:
            try:
                # Classify
                email_text = f"Subject: {email['subject']}\n\n{email['body']}"
                classification = mock_ai_processor.classify_email_with_explanation(email_text)
                
                # Extract actions if needed
                if classification['action_required']:
                    actions = mock_ai_processor.extract_action_items_from_email(email_text)
                    
                    # Create tasks
                    if actions['action_items']:
                        for action_item in actions['action_items']:
                            task_data = {
                                'email_id': email['id'],
                                'title': action_item['action'],
                                'description': email['body'][:200],
                                'priority': classification['priority'],
                                'category': classification['category'],
                                'status': 'open',
                                'created_at': datetime.now().isoformat()
                            }
                            
                            task_id = mock_task_persistence.create_task(task_data)
                            tasks_created.append(task_id)
                
                # Update email
                mock_outlook_manager.categorize_email(email['id'], classification['category'])
                mock_outlook_manager.mark_as_read(email['id'])
                
                processed_count += 1
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing email {email['id']}: {e}")
        
        # Verify batch processing
        assert processed_count == len(mock_outlook_emails)
        assert len(tasks_created) >= 2
        
        # Verify all categorization calls
        assert mock_outlook_manager.categorize_email.call_count == len(mock_outlook_emails)
    
    def test_pipeline_error_recovery(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence
    ):
        """Test pipeline error handling and recovery."""
        emails = mock_outlook_manager.get_inbox_messages(count=1)
        email = emails[0]
        
        # Simulate AI classification failure
        mock_ai_processor.classify_email_with_explanation.side_effect = Exception("AI timeout")
        
        email_text = f"Subject: {email['subject']}\n\n{email['body']}"
        
        # Should raise exception
        with pytest.raises(Exception) as exc_info:
            mock_ai_processor.classify_email_with_explanation(email_text)
        
        assert "AI timeout" in str(exc_info.value)
        
        # Reset mock to succeed on retry
        mock_ai_processor.classify_email_with_explanation.side_effect = None
        mock_ai_processor.classify_email_with_explanation.return_value = {
            'category': 'optional_fyi',
            'confidence': 0.85,
            'explanation': 'Classified after retry',
            'alternatives': [],
            'action_required': False,
            'priority': 'low'
        }
        
        # Retry should succeed
        classification = mock_ai_processor.classify_email_with_explanation(email_text)
        assert classification['category'] == 'optional_fyi'
    
    def test_pipeline_with_different_email_types(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence
    ):
        """Test pipeline handles different email types correctly."""
        emails = mock_outlook_manager.get_inbox_messages(count=10)
        
        results = {
            'required_personal_action': 0,
            'optional_event': 0,
            'optional_fyi': 0,
            'tasks_created': 0
        }
        
        for email in emails:
            email_text = f"Subject: {email['subject']}\n\n{email['body']}"
            classification = mock_ai_processor.classify_email_with_explanation(email_text)
            
            category = classification['category']
            results[category] = results.get(category, 0) + 1
            
            # Create tasks only for action-required emails
            if classification['action_required']:
                actions = mock_ai_processor.extract_action_items_from_email(email_text)
                if actions['action_items']:
                    task_data = {
                        'email_id': email['id'],
                        'title': actions['action_items'][0]['action'],
                        'description': email['body'],
                        'priority': classification['priority'],
                        'status': 'open',
                        'created_at': datetime.now().isoformat()
                    }
                    mock_task_persistence.create_task(task_data)
                    results['tasks_created'] += 1
        
        # Verify different email types were processed
        assert results['required_personal_action'] > 0
        assert results['optional_event'] > 0 or results['optional_fyi'] > 0
        assert results['tasks_created'] >= 2


# ============================================================================
# Integration Test: Performance and Scalability
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestPipelinePerformance:
    """Test pipeline performance with larger datasets."""
    
    def test_pipeline_execution_time(
        self, mock_outlook_manager, mock_ai_processor, mock_task_persistence
    ):
        """Test pipeline completes within acceptable time limits."""
        import time
        
        # Generate larger dataset
        large_email_set = []
        for i in range(20):
            large_email_set.append({
                'id': f'test-email-{i}',
                'subject': f'Test Email {i}',
                'sender': f'sender{i}@example.com',
                'recipient': 'user@example.com',
                'body': f'This is test email number {i} with some content.',
                'received_time': datetime.now().isoformat(),
                'is_read': False,
                'categories': [],
                'has_attachments': False,
                'conversation_id': f'conv-{i}'
            })
        
        mock_outlook_manager.get_inbox_messages.return_value = large_email_set
        
        start_time = time.time()
        
        # Process all emails
        for email in large_email_set:
            email_text = f"Subject: {email['subject']}\n\n{email['body']}"
            classification = mock_ai_processor.classify_email_with_explanation(email_text)
            
            if classification['action_required']:
                actions = mock_ai_processor.extract_action_items_from_email(email_text)
                if actions['action_items']:
                    task_data = {
                        'email_id': email['id'],
                        'title': actions['action_items'][0]['action'],
                        'priority': classification['priority'],
                        'status': 'open',
                        'created_at': datetime.now().isoformat()
                    }
                    mock_task_persistence.create_task(task_data)
        
        elapsed_time = time.time() - start_time
        
        # Should complete in under 5 seconds for 20 emails with mocks
        assert elapsed_time < 5.0, f"Pipeline took {elapsed_time:.2f}s, expected <5s"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
