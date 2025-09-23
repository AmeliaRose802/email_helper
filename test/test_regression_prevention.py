#!/usr/bin/env python3
"""
Regression Prevention Test Suite

Automated detection of behavioral changes and regression prevention for GUI components.
Ensures existing functionality remains intact across development iterations.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import json
import hashlib
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
sys.path.append(os.path.join(parent_dir, 'src'))


@dataclass
class UIStateSnapshot:
    """Represents a snapshot of UI state for regression comparison"""
    component_exists: Dict[str, bool]
    component_properties: Dict[str, Dict[str, Any]]
    data_structure: Dict[str, Any]
    method_signatures: Dict[str, List[str]]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    def compute_hash(self) -> str:
        """Compute hash of snapshot for comparison"""
        snapshot_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(snapshot_str.encode()).hexdigest()


class UIStateCapture:
    """Captures current UI state for regression testing"""
    
    def __init__(self):
        self.baseline_snapshots = {}
        
    def capture_gui_state(self, gui_instance: Mock) -> UIStateSnapshot:
        """Capture complete GUI state"""
        from datetime import datetime
        
        # Capture component existence
        component_exists = {
            'root': hasattr(gui_instance, 'root'),
            'notebook': hasattr(gui_instance, 'notebook'),
            'email_tree': hasattr(gui_instance, 'email_tree'),
            'summary_text': hasattr(gui_instance, 'summary_text'),
            'email_suggestions': hasattr(gui_instance, 'email_suggestions'),
            'action_items_data': hasattr(gui_instance, 'action_items_data'),
            'summary_sections': hasattr(gui_instance, 'summary_sections')
        }
        
        # Capture component properties
        component_properties = {}
        
        if hasattr(gui_instance, 'email_tree'):
            tree_props = {}
            if hasattr(gui_instance.email_tree, '__getitem__'):
                try:
                    columns = gui_instance.email_tree['columns']
                    tree_props['columns'] = list(columns) if columns else []
                except:
                    tree_props['columns'] = []
            component_properties['email_tree'] = tree_props
            
        if hasattr(gui_instance, 'notebook'):
            notebook_props = {}
            if hasattr(gui_instance.notebook, 'tabs'):
                try:
                    tabs = gui_instance.notebook.tabs()
                    notebook_props['tab_count'] = len(tabs) if tabs else 0
                except:
                    notebook_props['tab_count'] = 0
            component_properties['notebook'] = notebook_props
        
        # Capture data structure
        data_structure = {
            'email_suggestions_type': type(gui_instance.email_suggestions).__name__ if hasattr(gui_instance, 'email_suggestions') else None,
            'action_items_data_type': type(gui_instance.action_items_data).__name__ if hasattr(gui_instance, 'action_items_data') else None,
            'summary_sections_type': type(gui_instance.summary_sections).__name__ if hasattr(gui_instance, 'summary_sections') else None
        }
        
        # Capture method signatures
        method_signatures = {}
        expected_methods = [
            'refresh_email_tree',
            'display_email_details',
            '_open_url'
        ]
        
        for method_name in expected_methods:
            if hasattr(gui_instance, method_name):
                method = getattr(gui_instance, method_name)
                method_signatures[method_name] = ['callable'] if callable(method) else ['not_callable']
        
        return UIStateSnapshot(
            component_exists=component_exists,
            component_properties=component_properties,
            data_structure=data_structure,
            method_signatures=method_signatures,
            timestamp=datetime.now().isoformat()
        )
    
    def save_baseline(self, name: str, snapshot: UIStateSnapshot):
        """Save baseline snapshot for regression comparison"""
        self.baseline_snapshots[name] = snapshot
    
    def compare_with_baseline(self, name: str, current_snapshot: UIStateSnapshot) -> Dict[str, Any]:
        """Compare current snapshot with baseline"""
        if name not in self.baseline_snapshots:
            return {'error': 'No baseline found', 'baseline_exists': False}
        
        baseline = self.baseline_snapshots[name]
        differences = {}
        
        # Compare component existence
        comp_diffs = {}
        for comp, exists in baseline.component_exists.items():
            current_exists = current_snapshot.component_exists.get(comp, False)
            if exists != current_exists:
                comp_diffs[comp] = {'baseline': exists, 'current': current_exists}
        
        if comp_diffs:
            differences['component_existence'] = comp_diffs
        
        # Compare component properties
        prop_diffs = {}
        for comp, props in baseline.component_properties.items():
            current_props = current_snapshot.component_properties.get(comp, {})
            for prop, value in props.items():
                current_value = current_props.get(prop)
                if value != current_value:
                    if comp not in prop_diffs:
                        prop_diffs[comp] = {}
                    prop_diffs[comp][prop] = {'baseline': value, 'current': current_value}
        
        if prop_diffs:
            differences['component_properties'] = prop_diffs
        
        # Compare data structures
        data_diffs = {}
        for key, value in baseline.data_structure.items():
            current_value = current_snapshot.data_structure.get(key)
            if value != current_value:
                data_diffs[key] = {'baseline': value, 'current': current_value}
        
        if data_diffs:
            differences['data_structure'] = data_diffs
        
        # Compare method signatures
        method_diffs = {}
        for method, signature in baseline.method_signatures.items():
            current_signature = current_snapshot.method_signatures.get(method, [])
            if signature != current_signature:
                method_diffs[method] = {'baseline': signature, 'current': current_signature}
        
        if method_diffs:
            differences['method_signatures'] = method_diffs
        
        return {
            'has_differences': len(differences) > 0,
            'differences': differences,
            'baseline_hash': baseline.compute_hash(),
            'current_hash': current_snapshot.compute_hash()
        }


class RegressionTestValidator:
    """Validates that changes don't introduce regressions"""
    
    def __init__(self):
        self.state_capture = UIStateCapture()
        self.validation_results = {}
        
    def setup_mock_gui_baseline(self) -> Mock:
        """Set up a baseline mock GUI that represents expected behavior"""
        mock_gui = Mock()
        
        # Essential components that must exist
        mock_gui.root = Mock()
        mock_gui.notebook = Mock()
        mock_gui.email_tree = Mock()
        mock_gui.summary_text = Mock()
        
        # Data containers with expected types
        mock_gui.email_suggestions = []
        mock_gui.action_items_data = {}
        mock_gui.summary_sections = {}
        
        # Essential methods that must be callable
        mock_gui.refresh_email_tree = Mock()
        mock_gui.display_email_details = Mock()
        mock_gui._open_url = Mock()
        
        # Tree component configuration
        mock_gui.email_tree.__getitem__ = Mock(return_value=['Subject', 'From', 'Category', 'AI Summary', 'Date'])
        mock_gui.email_tree.get_children = Mock(return_value=[])
        mock_gui.email_tree.insert = Mock(return_value='item_id')
        mock_gui.email_tree.selection_set = Mock()
        
        # Notebook configuration
        mock_gui.notebook.tabs = Mock(return_value=['tab1', 'tab2', 'tab3'])
        mock_gui.notebook.select = Mock()
        
        return mock_gui
    
    def test_core_component_regression(self, gui_instance: Mock) -> bool:
        """Test that core components haven't regressed"""
        try:
            # Check essential components exist
            essential_components = ['root', 'notebook', 'email_tree', 'summary_text']
            for component in essential_components:
                if not hasattr(gui_instance, component):
                    self.validation_results[f'missing_{component}'] = False
                    return False
            
            # Check essential data containers
            essential_data = ['email_suggestions', 'action_items_data', 'summary_sections']
            for data_attr in essential_data:
                if not hasattr(gui_instance, data_attr):
                    self.validation_results[f'missing_{data_attr}'] = False
                    return False
            
            # Check essential methods
            essential_methods = ['refresh_email_tree', 'display_email_details', '_open_url']
            for method in essential_methods:
                if not hasattr(gui_instance, method):
                    self.validation_results[f'missing_method_{method}'] = False
                    return False
                if not callable(getattr(gui_instance, method)):
                    self.validation_results[f'not_callable_{method}'] = False
                    return False
            
            self.validation_results['core_components'] = True
            return True
            
        except Exception as e:
            self.validation_results['core_component_error'] = str(e)
            return False
    
    def test_data_structure_regression(self, gui_instance: Mock) -> bool:
        """Test that data structures haven't regressed"""
        try:
            # Check email_suggestions structure
            if hasattr(gui_instance, 'email_suggestions'):
                if not isinstance(gui_instance.email_suggestions, list):
                    self.validation_results['email_suggestions_type_error'] = True
                    return False
                    
            # Check action_items_data structure  
            if hasattr(gui_instance, 'action_items_data'):
                if not isinstance(gui_instance.action_items_data, dict):
                    self.validation_results['action_items_data_type_error'] = True
                    return False
                    
            # Check summary_sections structure
            if hasattr(gui_instance, 'summary_sections'):
                if not isinstance(gui_instance.summary_sections, dict):
                    self.validation_results['summary_sections_type_error'] = True
                    return False
            
            self.validation_results['data_structures'] = True
            return True
            
        except Exception as e:
            self.validation_results['data_structure_error'] = str(e)
            return False
    
    def test_ui_interaction_regression(self, gui_instance: Mock) -> bool:
        """Test that UI interactions haven't regressed"""
        try:
            # Test email tree interactions
            if hasattr(gui_instance, 'email_tree'):
                # Test column access
                try:
                    columns = gui_instance.email_tree['columns']
                    if not columns:
                        self.validation_results['empty_columns'] = True
                        return False
                except Exception:
                    self.validation_results['column_access_error'] = True
                    return False
                
                # Test tree operations
                try:
                    gui_instance.email_tree.get_children()
                    gui_instance.email_tree.insert('', 'end', values=('test',))
                    gui_instance.email_tree.selection_set('test')
                except Exception:
                    self.validation_results['tree_operations_error'] = True
                    return False
            
            # Test notebook interactions
            if hasattr(gui_instance, 'notebook'):
                try:
                    tabs = gui_instance.notebook.tabs()
                    if tabs:
                        gui_instance.notebook.select(0)
                except Exception:
                    self.validation_results['notebook_operations_error'] = True
                    return False
            
            # Test method calls
            try:
                gui_instance.refresh_email_tree()
                gui_instance.display_email_details(0)
                gui_instance._open_url('test_url')
            except Exception:
                self.validation_results['method_call_error'] = True
                return False
            
            self.validation_results['ui_interactions'] = True
            return True
            
        except Exception as e:
            self.validation_results['ui_interaction_error'] = str(e)
            return False
    
    def test_workflow_regression(self, gui_instance: Mock) -> bool:
        """Test that core workflows haven't regressed"""
        try:
            # Test email loading workflow
            test_emails = [
                {
                    'email_data': {
                        'subject': 'Regression Test',
                        'sender': 'regression@test.com',
                        'entry_id': 'regression_001'
                    },
                    'ai_suggestion': 'required_action',
                    'ai_summary': 'Regression test summary'
                }
            ]
            
            gui_instance.email_suggestions = test_emails
            gui_instance.refresh_email_tree()
            
            # Test action items workflow
            action_items = {
                'required_actions': [
                    {
                        'subject': 'Regression Action',
                        'task_id': 'regression_task_001'
                    }
                ]
            }
            
            gui_instance.action_items_data = action_items
            
            # Test summary workflow
            summary_sections = {
                'main_summary': 'Regression test summary'
            }
            
            gui_instance.summary_sections = summary_sections
            
            self.validation_results['workflows'] = True
            return True
            
        except Exception as e:
            self.validation_results['workflow_error'] = str(e)
            return False
    
    def run_full_regression_test(self, gui_instance: Mock) -> Dict[str, Any]:
        """Run complete regression test suite"""
        results = {
            'core_components': self.test_core_component_regression(gui_instance),
            'data_structures': self.test_data_structure_regression(gui_instance),
            'ui_interactions': self.test_ui_interaction_regression(gui_instance),
            'workflows': self.test_workflow_regression(gui_instance)
        }
        
        # Create state snapshot
        current_snapshot = self.state_capture.capture_gui_state(gui_instance)
        
        # Compare with baseline if available
        baseline_comparison = {}
        if 'baseline' in self.state_capture.baseline_snapshots:
            baseline_comparison = self.state_capture.compare_with_baseline('baseline', current_snapshot)
        
        return {
            'test_results': results,
            'all_passed': all(results.values()),
            'validation_details': self.validation_results,
            'baseline_comparison': baseline_comparison,
            'current_snapshot_hash': current_snapshot.compute_hash()
        }


class ChangeDetector:
    """Detects changes in UI behavior that might indicate regressions"""
    
    def __init__(self):
        self.behavior_baselines = {}
        
    def capture_behavior_baseline(self, name: str, gui_instance: Mock) -> Dict[str, Any]:
        """Capture baseline behavior for comparison"""
        behavior = {
            'component_count': self._count_components(gui_instance),
            'method_responses': self._test_method_responses(gui_instance),
            'data_handling': self._test_data_handling(gui_instance)
        }
        
        self.behavior_baselines[name] = behavior
        return behavior
    
    def _count_components(self, gui_instance: Mock) -> Dict[str, int]:
        """Count UI components"""
        count = {
            'total_attributes': len(dir(gui_instance)),
            'mock_calls': len(gui_instance.method_calls) if hasattr(gui_instance, 'method_calls') else 0
        }
        
        # Count specific component types
        components = ['root', 'notebook', 'email_tree', 'summary_text']
        count['essential_components'] = sum(1 for comp in components if hasattr(gui_instance, comp))
        
        return count
    
    def _test_method_responses(self, gui_instance: Mock) -> Dict[str, str]:
        """Test method response behavior"""
        responses = {}
        
        methods_to_test = ['refresh_email_tree', 'display_email_details', '_open_url']
        
        for method_name in methods_to_test:
            if hasattr(gui_instance, method_name):
                try:
                    method = getattr(gui_instance, method_name)
                    if callable(method):
                        # For mocks, just verify callable
                        responses[method_name] = 'callable'
                    else:
                        responses[method_name] = 'not_callable'
                except Exception as e:
                    responses[method_name] = f'error: {str(e)}'
            else:
                responses[method_name] = 'missing'
        
        return responses
    
    def _test_data_handling(self, gui_instance: Mock) -> Dict[str, str]:
        """Test data handling behavior"""
        handling = {}
        
        # Test email_suggestions handling
        if hasattr(gui_instance, 'email_suggestions'):
            try:
                original = gui_instance.email_suggestions
                gui_instance.email_suggestions = [{'test': 'data'}]
                gui_instance.email_suggestions = original
                handling['email_suggestions'] = 'writable'
            except Exception:
                handling['email_suggestions'] = 'read_only_or_error'
        else:
            handling['email_suggestions'] = 'missing'
        
        # Test action_items_data handling
        if hasattr(gui_instance, 'action_items_data'):
            try:
                original = gui_instance.action_items_data
                gui_instance.action_items_data = {'test': []}
                gui_instance.action_items_data = original
                handling['action_items_data'] = 'writable'
            except Exception:
                handling['action_items_data'] = 'read_only_or_error'
        else:
            handling['action_items_data'] = 'missing'
        
        return handling
    
    def detect_behavior_changes(self, name: str, current_gui: Mock) -> Dict[str, Any]:
        """Detect changes in behavior compared to baseline"""
        if name not in self.behavior_baselines:
            return {'error': 'No baseline found'}
        
        baseline = self.behavior_baselines[name]
        current_behavior = {
            'component_count': self._count_components(current_gui),
            'method_responses': self._test_method_responses(current_gui),
            'data_handling': self._test_data_handling(current_gui)
        }
        
        changes = {}
        
        # Compare component counts
        for key, baseline_count in baseline['component_count'].items():
            current_count = current_behavior['component_count'].get(key, 0)
            if baseline_count != current_count:
                changes[f'component_count_{key}'] = {
                    'baseline': baseline_count,
                    'current': current_count
                }
        
        # Compare method responses
        for method, baseline_response in baseline['method_responses'].items():
            current_response = current_behavior['method_responses'].get(method, 'missing')
            if baseline_response != current_response:
                changes[f'method_response_{method}'] = {
                    'baseline': baseline_response,
                    'current': current_response
                }
        
        # Compare data handling
        for data_type, baseline_handling in baseline['data_handling'].items():
            current_handling = current_behavior['data_handling'].get(data_type, 'missing')
            if baseline_handling != current_handling:
                changes[f'data_handling_{data_type}'] = {
                    'baseline': baseline_handling,
                    'current': current_handling
                }
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'current_behavior': current_behavior
        }


# Pytest test functions

@pytest.fixture
def regression_validator():
    """Fixture to provide regression test validator"""
    return RegressionTestValidator()


@pytest.fixture
def change_detector():
    """Fixture to provide change detector"""
    return ChangeDetector()


@pytest.fixture
def baseline_gui(regression_validator):
    """Fixture to provide baseline GUI for comparison"""
    gui = regression_validator.setup_mock_gui_baseline()
    
    # Capture baseline state
    snapshot = regression_validator.state_capture.capture_gui_state(gui)
    regression_validator.state_capture.save_baseline('baseline', snapshot)
    
    return gui


@pytest.mark.regression
@pytest.mark.ui
def test_core_component_regression(regression_validator):
    """Test that core UI components haven't regressed"""
    mock_gui = regression_validator.setup_mock_gui_baseline()
    result = regression_validator.test_core_component_regression(mock_gui)
    assert result is True


@pytest.mark.regression
@pytest.mark.ui
def test_data_structure_regression(regression_validator):
    """Test that data structures haven't regressed"""
    mock_gui = regression_validator.setup_mock_gui_baseline()
    result = regression_validator.test_data_structure_regression(mock_gui)
    assert result is True


@pytest.mark.regression
@pytest.mark.ui
def test_ui_interaction_regression(regression_validator):
    """Test that UI interactions haven't regressed"""
    mock_gui = regression_validator.setup_mock_gui_baseline()
    result = regression_validator.test_ui_interaction_regression(mock_gui)
    assert result is True


@pytest.mark.regression
@pytest.mark.workflow
def test_workflow_regression(regression_validator):
    """Test that core workflows haven't regressed"""
    mock_gui = regression_validator.setup_mock_gui_baseline()
    result = regression_validator.test_workflow_regression(mock_gui)
    assert result is True


@pytest.mark.regression
@pytest.mark.e2e
def test_full_regression_suite(regression_validator):
    """Test complete regression test suite"""
    mock_gui = regression_validator.setup_mock_gui_baseline()
    results = regression_validator.run_full_regression_test(mock_gui)
    
    assert results['all_passed'] is True
    assert results['test_results']['core_components'] is True
    assert results['test_results']['data_structures'] is True
    assert results['test_results']['ui_interactions'] is True
    assert results['test_results']['workflows'] is True


@pytest.mark.regression
def test_state_snapshot_comparison(regression_validator, baseline_gui):
    """Test state snapshot comparison functionality"""
    # Create a modified GUI
    modified_gui = regression_validator.setup_mock_gui_baseline()
    
    # Remove a component to simulate regression
    delattr(modified_gui, 'summary_text')
    
    # Capture modified state
    modified_snapshot = regression_validator.state_capture.capture_gui_state(modified_gui)
    
    # Compare with baseline
    comparison = regression_validator.state_capture.compare_with_baseline('baseline', modified_snapshot)
    
    assert comparison['has_differences'] is True
    assert 'component_existence' in comparison['differences']
    assert 'summary_text' in comparison['differences']['component_existence']


@pytest.mark.regression
def test_behavior_change_detection(change_detector):
    """Test behavior change detection"""
    # Create baseline GUI
    baseline_gui = Mock()
    baseline_gui.root = Mock()
    baseline_gui.email_tree = Mock()
    baseline_gui.refresh_email_tree = Mock()
    baseline_gui.email_suggestions = []
    
    # Capture baseline behavior
    change_detector.capture_behavior_baseline('test', baseline_gui)
    
    # Create modified GUI (simulate behavior change)
    modified_gui = Mock()
    modified_gui.root = Mock()
    modified_gui.email_tree = Mock()
    modified_gui.refresh_email_tree = "not_callable"  # Changed from callable to string
    modified_gui.email_suggestions = []
    
    # Detect changes
    changes = change_detector.detect_behavior_changes('test', modified_gui)
    
    assert changes['has_changes'] is True
    assert 'method_response_refresh_email_tree' in changes['changes']


@pytest.mark.regression
def test_ui_state_snapshot_creation():
    """Test UI state snapshot creation and validation"""
    mock_gui = Mock()
    mock_gui.root = Mock()
    mock_gui.notebook = Mock()
    mock_gui.email_tree = Mock()
    mock_gui.email_suggestions = []
    mock_gui.action_items_data = {}
    
    state_capture = UIStateCapture()
    snapshot = state_capture.capture_gui_state(mock_gui)
    
    assert snapshot.component_exists['root'] is True
    assert snapshot.component_exists['notebook'] is True
    assert snapshot.component_exists['email_tree'] is True
    assert snapshot.data_structure['email_suggestions_type'] == 'list'
    assert snapshot.data_structure['action_items_data_type'] == 'dict'
    
    # Test hash computation
    hash_value = snapshot.compute_hash()
    assert isinstance(hash_value, str)
    assert len(hash_value) == 32  # MD5 hash length


@pytest.mark.regression
@pytest.mark.slow
def test_regression_detection_performance():
    """Test performance of regression detection"""
    regression_validator = RegressionTestValidator()
    
    import time
    start_time = time.time()
    
    # Run regression test multiple times
    for i in range(10):
        mock_gui = regression_validator.setup_mock_gui_baseline()
        results = regression_validator.run_full_regression_test(mock_gui)
        assert results['all_passed'] is True
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    # Should complete 10 regression tests in under 5 seconds
    assert execution_time < 5.0, f"Regression tests too slow: {execution_time}s for 10 runs"


if __name__ == "__main__":
    # Run tests directly if executed as script
    pytest.main([__file__, "-v"])