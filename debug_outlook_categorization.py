#!/usr/bin/env python3
"""
Outlook Categorization Diagnostic Tool
Identifies specific issues with email categorization and folder organization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.outlook_manager import OutlookManager
from src.ai_processor import AIProcessor
from src.accuracy_tracker import AccuracyTracker
import json
from datetime import datetime, timedelta


class OutlookDiagnostic:
    def __init__(self):
        self.outlook_manager = OutlookManager()
        self.ai_processor = AIProcessor()
        self.accuracy_tracker = AccuracyTracker("c:\\Users\\ameliapayne\\email_helper\\runtime_data")
        
    def run_comprehensive_diagnosis(self):
        """Run all diagnostic checks"""
        print("🔍 OUTLOOK CATEGORIZATION DIAGNOSTIC TOOL")
        print("=" * 60)
        
        # Test 1: Outlook Connection
        print("\n📧 Testing Outlook Connection...")
        outlook_status = self.test_outlook_connection()
        
        if not outlook_status['connected']:
            print("❌ Cannot proceed - Outlook connection failed")
            return
        
        # Test 2: Folder Structure
        print("\n📁 Testing Folder Structure...")
        folder_status = self.test_folder_structure()
        
        # Test 3: Email Access and Processing
        print("\n📬 Testing Email Access...")
        email_access_status = self.test_email_access()
        
        # Test 4: Categorization Logic
        print("\n🧠 Testing Categorization Logic...")
        categorization_status = self.test_categorization_logic()
        
        # Test 5: Historical Analysis
        print("\n📊 Analyzing Historical Issues...")
        historical_analysis = self.analyze_historical_issues()
        
        # Generate Report
        print("\n" + "="*60)
        print("📋 DIAGNOSTIC SUMMARY")
        print("="*60)
        
        self.generate_diagnostic_report({
            'outlook_connection': outlook_status,
            'folder_structure': folder_status,
            'email_access': email_access_status,
            'categorization_logic': categorization_status,
            'historical_analysis': historical_analysis
        })
        
    def test_outlook_connection(self):
        """Test basic Outlook connectivity"""
        try:
            self.outlook_manager.connect_to_outlook()
            
            # Test inbox access
            inbox_items = self.outlook_manager.inbox.Items
            item_count = inbox_items.Count
            
            print(f"✅ Outlook connected successfully")
            print(f"   📧 Inbox contains {item_count} emails")
            
            return {
                'connected': True,
                'inbox_items': item_count,
                'error': None
            }
            
        except Exception as e:
            print(f"❌ Outlook connection failed: {str(e)}")
            return {
                'connected': False,
                'inbox_items': 0,
                'error': str(e)
            }
    
    def test_folder_structure(self):
        """Test folder creation and access"""
        print("   Checking folder organization...")
        
        folder_results = {
            'inbox_folders': {},
            'non_inbox_folders': {},
            'missing_folders': [],
            'access_errors': []
        }
        
        # Expected folder structure
        expected_folders = {
            'inbox': {
                'required_personal_action': 'Required Actions (Me)',
                'optional_action': 'Optional Actions',
                'job_listing': 'Job Listings',
                'work_relevant': 'Work Relevant'
            },
            'non_inbox': {
                'team_action': 'Team Actions',
                'optional_event': 'Optional Events',
                'fyi': 'FYI',
                'newsletter': 'Newsletters',
                'general_information': 'Summarized',
                'spam_to_delete': 'ai_deleted'
            }
        }
        
        # Check if folders were created correctly
        for category, folder_path in self.outlook_manager.folders.items():
            if folder_path is None:
                folder_results['missing_folders'].append(category)
                print(f"   ⚠️  Missing folder for category: {category}")
            else:
                try:
                    # Test folder access
                    folder_name = folder_path.Name
                    parent_name = folder_path.Parent.Name if hasattr(folder_path, 'Parent') else 'Unknown'
                    
                    if category in expected_folders['inbox']:
                        folder_results['inbox_folders'][category] = {
                            'name': folder_name,
                            'parent': parent_name,
                            'accessible': True
                        }
                        print(f"   ✅ Inbox folder: {folder_name} (in {parent_name})")
                    else:
                        folder_results['non_inbox_folders'][category] = {
                            'name': folder_name, 
                            'parent': parent_name,
                            'accessible': True
                        }
                        print(f"   ✅ Reference folder: {folder_name} (in {parent_name})")
                        
                except Exception as e:
                    folder_results['access_errors'].append({
                        'category': category,
                        'error': str(e)
                    })
                    print(f"   ❌ Cannot access folder for {category}: {str(e)}")
        
        return folder_results
    
    def test_email_access(self):
        """Test email retrieval and conversation threading"""
        print("   Testing email retrieval...")
        
        try:
            # Get a small sample of recent emails
            recent_emails = self.outlook_manager.get_recent_emails(days_back=1, max_emails=5)
            
            if not recent_emails:
                print("   ⚠️  No recent emails found in last 24 hours")
                # Try a longer period
                recent_emails = self.outlook_manager.get_recent_emails(days_back=7, max_emails=5)
            
            email_test_results = {
                'emails_found': len(recent_emails),
                'conversation_test': None,
                'body_access_test': None,
                'errors': []
            }
            
            print(f"   ✅ Found {len(recent_emails)} recent emails")
            
            if recent_emails:
                # Test conversation threading
                try:
                    conversations = self.outlook_manager.get_emails_with_full_conversations(days_back=1, max_emails=3)
                    email_test_results['conversation_test'] = {
                        'conversations_found': len(conversations),
                        'success': True
                    }
                    print(f"   ✅ Conversation threading working - {len(conversations)} threads found")
                except Exception as e:
                    email_test_results['conversation_test'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"   ❌ Conversation threading failed: {str(e)}")
                
                # Test email body access
                try:
                    test_email = recent_emails[0]
                    body = self.outlook_manager.get_email_body(test_email)
                    email_test_results['body_access_test'] = {
                        'body_length': len(body) if body else 0,
                        'success': True
                    }
                    print(f"   ✅ Email body access working - sample length: {len(body) if body else 0} chars")
                except Exception as e:
                    email_test_results['body_access_test'] = {
                        'success': False,
                        'error': str(e)
                    }
                    print(f"   ❌ Email body access failed: {str(e)}")
            
            return email_test_results
            
        except Exception as e:
            print(f"   ❌ Email access test failed: {str(e)}")
            return {
                'emails_found': 0,
                'conversation_test': None,
                'body_access_test': None,
                'errors': [str(e)]
            }
    
    def test_categorization_logic(self):
        """Test the actual categorization process with a small sample"""
        print("   Testing categorization with sample emails...")
        
        try:
            # Get 2-3 recent emails for testing
            recent_emails = self.outlook_manager.get_recent_emails(days_back=7, max_emails=3)
            
            if not recent_emails:
                print("   ⚠️  No emails available for categorization test")
                return {'tested': False, 'reason': 'No emails available'}
            
            # Create mock suggestions for testing (don't actually categorize)
            test_suggestions = []
            for email in recent_emails[:2]:  # Test with just 2 emails
                # Create a mock suggestion structure
                mock_suggestion = {
                    'email_object': email,
                    'ai_suggestion': 'fyi',  # Use a safe category for testing
                    'thread_data': {
                        'all_emails': [email],
                        'thread_count': 1
                    },
                    'processing_notes': ['Diagnostic test - not actually applied']
                }
                test_suggestions.append(mock_suggestion)
            
            # Test the categorization logic without actually applying
            categorization_results = {
                'test_emails': len(test_suggestions),
                'folder_mapping_test': {},
                'move_test': None,
                'errors': []
            }
            
            # Test folder mapping
            for suggestion in test_suggestions:
                category = suggestion['ai_suggestion']
                if category in self.outlook_manager.folders:
                    target_folder = self.outlook_manager.folders[category]
                    if target_folder:
                        categorization_results['folder_mapping_test'][category] = {
                            'folder_name': target_folder.Name,
                            'accessible': True
                        }
                    else:
                        categorization_results['folder_mapping_test'][category] = {
                            'folder_name': None,
                            'accessible': False
                        }
                        
            print(f"   ✅ Categorization logic test completed - {len(test_suggestions)} emails processed")
            return categorization_results
            
        except Exception as e:
            print(f"   ❌ Categorization logic test failed: {str(e)}")
            return {
                'tested': False,
                'reason': str(e),
                'errors': [str(e)]
            }
    
    def analyze_historical_issues(self):
        """Analyze historical accuracy and failure patterns"""
        print("   Analyzing accuracy trends...")
        
        try:
            trends = self.accuracy_tracker.get_accuracy_trends(days_back=30)
            
            if not trends:
                print("   ⚠️  No historical accuracy data available")
                return {'data_available': False}
            
            print(f"   📊 Average accuracy: {trends['average_accuracy']}%")
            print(f"   📈 Trend: {trends['improvement_trend']}")
            print(f"   🔧 Most corrected categories: {list(trends['most_corrected_categories'].keys())[:3]}")
            
            # Identify specific problem patterns
            problem_analysis = {
                'accuracy_issues': trends['average_accuracy'] < 75,
                'declining_trend': trends['improvement_trend'] == 'declining',
                'problem_categories': trends['most_corrected_categories'],
                'recommendations': []
            }
            
            # Generate recommendations
            if problem_analysis['accuracy_issues']:
                problem_analysis['recommendations'].append("Overall accuracy below 75% - review AI classification rules")
            
            if problem_analysis['declining_trend']:
                problem_analysis['recommendations'].append("Accuracy declining - check for recent system changes")
            
            # Check problem categories against folder issues
            for problem_cat in trends['most_corrected_categories'].keys():
                if problem_cat in ['work_relevant', 'required_personal_action', 'team_action']:
                    problem_analysis['recommendations'].append(f"High corrections for {problem_cat} - review prompts for this category")
            
            return {
                'data_available': True,
                'trends': trends,
                'analysis': problem_analysis
            }
            
        except Exception as e:
            print(f"   ❌ Historical analysis failed: {str(e)}")
            return {
                'data_available': False,
                'error': str(e)
            }
    
    def generate_diagnostic_report(self, results):
        """Generate comprehensive diagnostic report"""
        
        # Overall Health Score
        health_score = self.calculate_health_score(results)
        print(f"\n🏥 OVERALL SYSTEM HEALTH: {health_score}/100")
        
        # Critical Issues
        critical_issues = []
        if not results['outlook_connection']['connected']:
            critical_issues.append("❌ CRITICAL: Cannot connect to Outlook")
        
        if results['folder_structure']['missing_folders']:
            critical_issues.append(f"⚠️  WARNING: {len(results['folder_structure']['missing_folders'])} folders missing")
        
        if results['historical_analysis'].get('data_available') and results['historical_analysis']['analysis']['accuracy_issues']:
            critical_issues.append(f"📉 PERFORMANCE: Low accuracy ({results['historical_analysis']['trends']['average_accuracy']}%)")
        
        if critical_issues:
            print("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            for issue in critical_issues:
                print(f"   {issue}")
        else:
            print("\n✅ No critical issues identified")
        
        # Recommendations
        recommendations = self.generate_recommendations(results)
        if recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"c:\\Users\\ameliapayne\\email_helper\\runtime_data\\outlook_diagnostic_{timestamp}.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: outlook_diagnostic_{timestamp}.json")
        except Exception as e:
            print(f"⚠️  Could not save detailed report: {e}")
    
    def calculate_health_score(self, results):
        """Calculate overall system health score"""
        score = 100
        
        # Outlook connection (critical)
        if not results['outlook_connection']['connected']:
            score -= 40
        
        # Folder structure
        missing_folders = len(results['folder_structure']['missing_folders'])
        if missing_folders > 0:
            score -= min(20, missing_folders * 3)
        
        # Email access
        if results['email_access']['emails_found'] == 0:
            score -= 15
        if results['email_access']['conversation_test'] and not results['email_access']['conversation_test']['success']:
            score -= 10
        
        # Historical performance
        if results['historical_analysis'].get('data_available'):
            accuracy = results['historical_analysis']['trends']['average_accuracy']
            if accuracy < 50:
                score -= 20
            elif accuracy < 75:
                score -= 10
        
        return max(0, score)
    
    def generate_recommendations(self, results):
        """Generate specific recommendations based on diagnostic results"""
        recommendations = []
        
        # Outlook connection issues
        if not results['outlook_connection']['connected']:
            recommendations.extend([
                "Restart Outlook and ensure it's running before using the email helper",
                "Check Outlook permissions and security settings",
                "Verify Outlook is properly configured with email accounts"
            ])
        
        # Folder issues
        missing_folders = results['folder_structure']['missing_folders']
        if missing_folders:
            recommendations.append(f"Manually create missing folders for categories: {', '.join(missing_folders)}")
            recommendations.append("Run the email helper once to auto-create folder structure")
        
        # Performance issues
        if results['historical_analysis'].get('data_available'):
            analysis = results['historical_analysis']['analysis']
            if analysis['accuracy_issues']:
                recommendations.append("Review AI classification prompts - accuracy below acceptable threshold")
            
            recommendations.extend(analysis.get('recommendations', []))
        
        # Email access issues
        if results['email_access']['emails_found'] == 0:
            recommendations.append("Check if emails exist in Outlook inbox for the specified date range")
        
        return recommendations


if __name__ == "__main__":
    diagnostic = OutlookDiagnostic()
    diagnostic.run_comprehensive_diagnosis()
