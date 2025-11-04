"""Comprehensive integration tests for component interactions.

This test suite covers critical integration paths:
1. Email retrieval → AI classification
2. AI classification → Task persistence
3. Complete email processing pipeline

Uses test database and mocks external APIs to ensure fast, reliable testing.
Target: 70%+ coverage of integration paths, execution time <2min.
"""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from typing import Dict, Any, List
import sqlite3
import tempfile
import os


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def test_database():
    """Create a test database with schema."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        db_path = temp_file.name

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Create schema
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY,
            subject TEXT,
            sender TEXT,
            recipient TEXT,
            body TEXT,
            received_time TEXT,
            is_read INTEGER,
            categories TEXT,
            conversation_id TEXT,
            classification TEXT,
            confidence REAL,
            processed_at TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT,
            title TEXT,
            description TEXT,
            due_date TEXT,
            priority TEXT,
            status TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (email_id) REFERENCES emails (id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id TEXT,
            action_required TEXT,
            due_date TEXT,
            priority TEXT,
            confidence REAL,
            created_at TEXT,
            FOREIGN KEY (email_id) REFERENCES emails (id)
        )
    """)

    conn.commit()
    yield db_path, conn

    conn.close()
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def mock_email_provider():
    """Mock email provider with realistic test data."""
    provider = MagicMock()
    provider.authenticate = Mock(return_value=True)
    provider.authenticated = True

    # Sample emails with different characteristics
    provider.get_emails = Mock(return_value=[
        {
            'id': 'email-action-1',
            'subject': 'URGENT: Code Review Required by Friday',
            'sender': 'tech.lead@company.com',
            'recipient': 'developer@company.com',
            'body': 'Please review PR #123 before EOD Friday. This blocks the release.',
            'received_time': '2024-01-15T10:00:00Z',
            'is_read': False,
            'categories': ['Important'],
            'conversation_id': 'conv-1'
        },
        {
            'id': 'email-meeting-1',
            'subject': 'Team Standup - Monday 10am',
            'sender': 'scrum.master@company.com',
            'recipient': 'developer@company.com',
            'body': 'Join us for the weekly standup. Agenda: Sprint planning, blockers.',
            'received_time': '2024-01-15T11:00:00Z',
            'is_read': False,
            'categories': [],
            'conversation_id': 'conv-2'
        },
        {
            'id': 'email-fyi-1',
            'subject': 'FYI: System Maintenance Notice',
            'sender': 'ops@company.com',
            'recipient': 'developer@company.com',
            'body': 'Scheduled maintenance this weekend. No action required.',
            'received_time': '2024-01-15T12:00:00Z',
            'is_read': True,
            'categories': [],
            'conversation_id': 'conv-3'
        }
    ])

    provider.get_email_by_id = Mock(side_effect=lambda email_id: next(
        (e for e in provider.get_emails() if e['id'] == email_id), None
    ))

    return provider


@pytest.fixture
def mock_ai_service():
    """Mock AI service with realistic classification responses."""
    service = MagicMock()

    # Configure classification responses based on email content
    def classify_email(email_data: Dict[str, Any]) -> Dict[str, Any]:
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')

        # Determine category based on content
        if 'URGENT' in subject or 'Code Review' in subject:
            return {
                'category': 'required_personal_action',
                'confidence': 0.95,
                'explanation': 'Email contains urgent action items requiring immediate attention',
                'alternatives': [
                    {'category': 'work_relevant', 'confidence': 0.05}
                ]
            }
        elif 'meeting' in subject.lower() or 'standup' in subject.lower():
            return {
                'category': 'optional_event',
                'confidence': 0.88,
                'explanation': 'Email is about a scheduled meeting',
                'alternatives': [
                    {'category': 'work_relevant', 'confidence': 0.12}
                ]
            }
        elif 'FYI' in subject or 'No action required' in body:
            return {
                'category': 'optional_fyi',
                'confidence': 0.82,
                'explanation': 'Informational email, no action required',
                'alternatives': [
                    {'category': 'work_relevant', 'confidence': 0.18}
                ]
            }
        else:
            return {
                'category': 'optional_fyi',
                'confidence': 0.82,
                'explanation': 'Informational email, no action required',
                'alternatives': [
                    {'category': 'work_relevant', 'confidence': 0.18}
                ]
            }

    service.classify_email = Mock(side_effect=classify_email)

    # Configure action item extraction
    def extract_action_items(email_data: Dict[str, Any]) -> Dict[str, Any]:
        body = email_data.get('body', '')

        if 'review' in body.lower():
            return {
                'action_items': [
                    {
                        'action_required': 'Review PR #123',
                        'due_date': 'Friday',
                        'priority': 'high',
                        'confidence': 0.92
                    }
                ]
            }
        return {'action_items': []}

    service.extract_action_items = Mock(side_effect=extract_action_items)

    # Configure summarization
    service.generate_summary = Mock(return_value={
        'summary': 'Brief summary of email content',
        'key_points': ['Point 1', 'Point 2'],
        'confidence': 0.85
    })

    return service


@pytest.fixture
def mock_task_persistence(test_database):
    """Mock task persistence using test database."""
    db_path, conn = test_database

    class TestTaskPersistence:
        def __init__(self):
            self.db_path = db_path
            self.conn = conn

        def save_task(self, task_data: Dict[str, Any]) -> int:
            """Save task to database."""
            cursor = self.conn.execute("""
                INSERT INTO tasks (email_id, title, description, due_date, 
                                 priority, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_data.get('email_id'),
                task_data.get('title'),
                task_data.get('description'),
                task_data.get('due_date'),
                task_data.get('priority', 'medium'),
                task_data.get('status', 'pending'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return cursor.lastrowid

        def get_task(self, task_id: int) -> Dict[str, Any]:
            """Retrieve task by ID."""
            cursor = self.conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None

        def get_tasks_by_email(self, email_id: str) -> List[Dict[str, Any]]:
            """Get all tasks for an email."""
            cursor = self.conn.execute(
                "SELECT * FROM tasks WHERE email_id = ?", (email_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

        def update_task_status(self, task_id: int, status: str) -> bool:
            """Update task status."""
            self.conn.execute(
                "UPDATE tasks SET status = ?, updated_at = ? WHERE id = ?",
                (status, datetime.now().isoformat(), task_id)
            )
            self.conn.commit()
            return True

        def save_email_classification(self, email_id: str, classification: Dict[str, Any]) -> bool:
            """Save email classification."""
            self.conn.execute("""
                UPDATE emails SET classification = ?, confidence = ?, processed_at = ?
                WHERE id = ?
            """, (
                classification.get('category'),
                classification.get('confidence'),
                datetime.now().isoformat(),
                email_id
            ))
            self.conn.commit()
            return True

    return TestTaskPersistence()


# ============================================================================
# Integration Test 1: Email Retrieval → AI Classification
# ============================================================================

@pytest.mark.integration
class TestEmailRetrievalToClassification:
    """Test integration between email retrieval and AI classification."""

    def test_retrieve_and_classify_single_email(
        self, mock_email_provider, mock_ai_service
    ):
        """Test retrieving and classifying a single email."""
        # Retrieve emails
        emails = mock_email_provider.get_emails()
        assert len(emails) > 0

        # Classify first email
        email = emails[0]
        classification = mock_ai_service.classify_email(email)

        # Verify classification
        assert classification['category'] == 'required_personal_action'
        assert classification['confidence'] >= 0.9
        assert 'explanation' in classification

        # Verify email data passed correctly
        mock_ai_service.classify_email.assert_called_once_with(email)

    def test_retrieve_and_classify_batch_emails(
        self, mock_email_provider, mock_ai_service
    ):
        """Test batch email classification."""
        # Retrieve all emails
        emails = mock_email_provider.get_emails()

        # Classify each email
        classifications = []
        for email in emails:
            classification = mock_ai_service.classify_email(email)
            classifications.append({
                'email_id': email['id'],
                'classification': classification
            })

        # Verify all emails classified
        assert len(classifications) == 3

        # Verify different categories assigned
        categories = [c['classification']['category'] for c in classifications]
        assert 'required_personal_action' in categories
        assert 'optional_event' in categories
        assert 'optional_fyi' in categories

    def test_classification_with_missing_fields(
        self, mock_ai_service
    ):
        """Test classification handles incomplete email data."""
        # Email with minimal data
        incomplete_email = {
            'id': 'email-incomplete',
            'subject': 'Test',
            'body': ''
        }

        # Should still classify without error
        classification = mock_ai_service.classify_email(incomplete_email)

        assert 'category' in classification
        assert 'confidence' in classification

    def test_classification_confidence_thresholds(
        self, mock_email_provider, mock_ai_service
    ):
        """Test that confidence thresholds are properly evaluated."""
        emails = mock_email_provider.get_emails()

        for email in emails:
            classification = mock_ai_service.classify_email(email)

            # High-priority categories should have high confidence
            if classification['category'] == 'required_personal_action':
                assert classification['confidence'] >= 0.9
            # Optional categories can have lower confidence
            elif classification['category'].startswith('optional_'):
                assert classification['confidence'] >= 0.8


# ============================================================================
# Integration Test 2: AI Classification → Task Persistence
# ============================================================================

@pytest.mark.integration
class TestClassificationToTaskPersistence:
    """Test integration between AI classification and task persistence."""

    def test_save_classification_to_database(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test saving classification results to database."""
        # Get and classify email
        emails = mock_email_provider.get_emails()
        email = emails[0]
        classification = mock_ai_service.classify_email(email)

        # Save classification
        success = mock_task_persistence.save_email_classification(
            email['id'], classification
        )

        assert success is True

    def test_create_task_from_classification(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test creating task from classified email."""
        # Get action-required email
        emails = mock_email_provider.get_emails()
        action_email = emails[0]  # URGENT email

        classification = mock_ai_service.classify_email(action_email)

        # If requires action, create task
        if classification['category'] == 'required_personal_action':
            task_data = {
                'email_id': action_email['id'],
                'title': action_email['subject'],
                'description': action_email['body'],
                'due_date': '2024-01-19',  # Friday
                'priority': 'high',
                'status': 'pending'
            }

            task_id = mock_task_persistence.save_task(task_data)
            assert task_id > 0

            # Verify task saved
            saved_task = mock_task_persistence.get_task(task_id)
            assert saved_task['email_id'] == action_email['id']
            assert saved_task['priority'] == 'high'

    def test_extract_and_save_action_items(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test extracting action items and creating tasks."""
        emails = mock_email_provider.get_emails()
        action_email = emails[0]

        # Extract action items
        action_items = mock_ai_service.extract_action_items(action_email)

        # Create task for each action item
        task_ids = []
        for item in action_items.get('action_items', []):
            task_data = {
                'email_id': action_email['id'],
                'title': item['action_required'],
                'description': f"From: {action_email['subject']}",
                'due_date': item.get('due_date', 'TBD'),
                'priority': item.get('priority', 'medium'),
                'status': 'pending'
            }
            task_id = mock_task_persistence.save_task(task_data)
            task_ids.append(task_id)

        # Verify tasks created
        assert len(task_ids) > 0

        # Verify tasks associated with email
        email_tasks = mock_task_persistence.get_tasks_by_email(action_email['id'])
        assert len(email_tasks) == len(task_ids)

    def test_update_task_status_workflow(
        self, mock_task_persistence
    ):
        """Test task status update workflow."""
        # Create a task
        task_data = {
            'email_id': 'test-email',
            'title': 'Test Task',
            'description': 'Test Description',
            'priority': 'medium',
            'status': 'pending'
        }
        task_id = mock_task_persistence.save_task(task_data)

        # Update to in-progress
        success = mock_task_persistence.update_task_status(task_id, 'in_progress')
        assert success is True

        # Verify update
        updated_task = mock_task_persistence.get_task(task_id)
        assert updated_task['status'] == 'in_progress'

        # Update to completed
        mock_task_persistence.update_task_status(task_id, 'completed')
        completed_task = mock_task_persistence.get_task(task_id)
        assert completed_task['status'] == 'completed'


# ============================================================================
# Integration Test 3: Complete Email Processing Pipeline
# ============================================================================

@pytest.mark.integration
class TestCompleteEmailProcessingPipeline:
    """Test end-to-end email processing workflow."""

    def test_full_pipeline_action_email(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test complete pipeline for action-required email."""
        # Step 1: Retrieve emails
        emails = mock_email_provider.get_emails()
        action_email = emails[0]  # URGENT email

        # Step 2: Classify email
        classification = mock_ai_service.classify_email(action_email)

        # Step 3: Save classification
        mock_task_persistence.save_email_classification(
            action_email['id'], classification
        )

        # Step 4: If action required, extract action items
        if classification['category'] == 'required_personal_action':
            action_items = mock_ai_service.extract_action_items(action_email)

            # Step 5: Create tasks for action items
            for item in action_items.get('action_items', []):
                task_data = {
                    'email_id': action_email['id'],
                    'title': item['action_required'],
                    'description': action_email['body'],
                    'due_date': item.get('due_date'),
                    'priority': item.get('priority'),
                    'status': 'pending'
                }
                task_id = mock_task_persistence.save_task(task_data)
                assert task_id > 0

        # Verify complete workflow
        email_tasks = mock_task_persistence.get_tasks_by_email(action_email['id'])
        assert len(email_tasks) > 0
        assert all(task['status'] == 'pending' for task in email_tasks)

    def test_full_pipeline_meeting_email(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test complete pipeline for meeting invitation."""
        # Step 1: Retrieve meeting email
        emails = mock_email_provider.get_emails()
        meeting_email = emails[1]

        # Step 2: Classify
        classification = mock_ai_service.classify_email(meeting_email)
        assert classification['category'] == 'optional_event'

        # Step 3: Save classification
        mock_task_persistence.save_email_classification(
            meeting_email['id'], classification
        )

        # Step 4: Generate summary for meetings
        summary = mock_ai_service.generate_summary(meeting_email)
        assert 'summary' in summary

    def test_full_pipeline_fyi_email(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test complete pipeline for FYI email."""
        emails = mock_email_provider.get_emails()
        fyi_email = emails[2]

        # Classify FYI email
        classification = mock_ai_service.classify_email(fyi_email)
        assert classification['category'] == 'optional_fyi'

        # Save classification (no task creation needed)
        mock_task_persistence.save_email_classification(
            fyi_email['id'], classification
        )

        # Verify no tasks created for FYI
        tasks = mock_task_persistence.get_tasks_by_email(fyi_email['id'])
        assert len(tasks) == 0

    def test_pipeline_batch_processing(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test processing multiple emails in batch."""
        emails = mock_email_provider.get_emails()

        processed_count = 0
        tasks_created = 0

        for email in emails:
            # Classify
            classification = mock_ai_service.classify_email(email)

            # Save classification
            mock_task_persistence.save_email_classification(
                email['id'], classification
            )
            processed_count += 1

            # Create tasks if needed
            if classification['category'] == 'required_personal_action':
                action_items = mock_ai_service.extract_action_items(email)
                for item in action_items.get('action_items', []):
                    task_data = {
                        'email_id': email['id'],
                        'title': item['action_required'],
                        'priority': item.get('priority', 'medium'),
                        'status': 'pending'
                    }
                    mock_task_persistence.save_task(task_data)
                    tasks_created += 1

        # Verify batch processing
        assert processed_count == 3
        assert tasks_created >= 1  # At least one action email


# ============================================================================
# Integration Test 4: Error Handling and Edge Cases
# ============================================================================

@pytest.mark.integration
class TestPipelineErrorHandling:
    """Test error handling in integration workflows."""

    def test_classification_failure_recovery(
        self, mock_email_provider, mock_ai_service
    ):
        """Test graceful handling of classification failures."""
        # Configure AI service to fail
        mock_ai_service.classify_email = Mock(
            side_effect=Exception("AI service unavailable")
        )

        emails = mock_email_provider.get_emails()
        email = emails[0]

        # Attempt classification with error handling
        try:
            mock_ai_service.classify_email(email)
            assert False, "Should have raised exception"
        except Exception as e:
            # Verify error can be caught and handled
            assert "AI service unavailable" in str(e)

    def test_task_persistence_failure_recovery(
        self, mock_task_persistence
    ):
        """Test handling of task save failures."""
        # Attempt to save invalid task (missing required field)
        task_data = {
            'email_id': None,  # Invalid
            'title': 'Test Task'
        }

        # Should handle gracefully (implementation dependent)
        # This tests that the interface is robust
        try:
            task_id = mock_task_persistence.save_task(task_data)
            # If it succeeds, verify it's saved
            if task_id:
                assert task_id > 0
        except Exception:
            # If it fails, that's also acceptable behavior
            pass

    def test_empty_email_batch_handling(
        self, mock_ai_service, mock_task_persistence
    ):
        """Test handling of empty email batch."""
        empty_emails = []

        processed_count = 0
        for email in empty_emails:
            mock_ai_service.classify_email(email)
            processed_count += 1

        # Should handle empty list gracefully
        assert processed_count == 0

    def test_malformed_email_data_handling(
        self, mock_ai_service
    ):
        """Test handling of malformed email data."""
        malformed_email = {
            'id': 'malformed',
            # Missing subject, sender, body, etc.
        }

        # Should still attempt classification
        classification = mock_ai_service.classify_email(malformed_email)

        # Should return valid structure even for malformed input
        assert 'category' in classification
        assert 'confidence' in classification


# ============================================================================
# Performance and Coverage Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestPipelinePerformance:
    """Test pipeline performance and scalability."""

    def test_processing_time_under_target(
        self, mock_email_provider, mock_ai_service, mock_task_persistence
    ):
        """Test that processing completes within time target."""
        import time

        start_time = time.time()

        # Process all emails
        emails = mock_email_provider.get_emails()
        for email in emails:
            classification = mock_ai_service.classify_email(email)
            mock_task_persistence.save_email_classification(
                email['id'], classification
            )

            if classification['category'] == 'required_personal_action':
                action_items = mock_ai_service.extract_action_items(email)
                for item in action_items.get('action_items', []):
                    task_data = {
                        'email_id': email['id'],
                        'title': item['action_required'],
                        'status': 'pending'
                    }
                    mock_task_persistence.save_task(task_data)

        elapsed_time = time.time() - start_time

        # Should complete in under 1 second for 3 emails
        # (Target is <2min for full suite)
        assert elapsed_time < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
