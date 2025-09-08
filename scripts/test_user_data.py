#!/usr/bin/env python3
"""
Simple test to verify user-specific data loading works
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_processor import AIProcessor

def test_user_data_loading():
    """Test if the AIProcessor can load user-specific data"""
    
    print("🧪 Testing User-Specific Data Loading")
    print("=" * 40)
    
    try:
        ai = AIProcessor()
        
        # Test username loading
        username = ai.get_username()
        print(f"✅ Username: {username}")
        
        # Test job role context loading
        job_role_context = ai.get_job_role_context()
        if job_role_context and "unavailable" not in job_role_context.lower():
            print(f"✅ Job Role Context: Loaded ({len(job_role_context)} characters)")
        else:
            print(f"❌ Job Role Context: {job_role_context}")
        
        # Test classification rules loading
        classification_rules = ai.get_classification_rules()
        if classification_rules and "unavailable" not in classification_rules.lower():
            print(f"✅ Classification Rules: Loaded ({len(classification_rules)} characters)")
        else:
            print(f"❌ Classification Rules: {classification_rules}")
        
        # Test job context loading (existing method)
        job_context = ai.get_job_context()
        if job_context and "unavailable" not in job_context.lower():
            print(f"✅ Job Context: Loaded ({len(job_context)} characters)")
        else:
            print(f"❌ Job Context: {job_context}")
        
        # Test job skills loading (existing method)
        job_skills = ai.get_job_skills()
        if job_skills and "unavailable" not in job_skills.lower():
            print(f"✅ Job Skills: Loaded ({len(job_skills)} characters)")
        else:
            print(f"❌ Job Skills: {job_skills}")
        
        print("\n🎉 User data loading test completed!")
        print("The system is now ready to process emails with your personalized context.")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_user_data_loading()
