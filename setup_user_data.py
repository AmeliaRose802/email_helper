#!/usr/bin/env python3
"""
Initialize user-specific data for Email Helper
Creates the user_specific_data directory and template files
"""

import os
import shutil
from pathlib import Path

def create_user_data_directory():
    """Create user_specific_data directory and template files"""
    print("🔧 Setting up user-specific data directory...")
    
    # Get project root directory
    project_root = Path(__file__).parent
    user_data_dir = project_root / "user_specific_data"
    
    # Create directory if it doesn't exist
    user_data_dir.mkdir(exist_ok=True)
    print(f"✅ Created directory: {user_data_dir}")
    
    # Template files to copy
    templates = [
        ("job_summery.md.template", "job_summery.md"),
        ("job_skill_summery.md.template", "job_skill_summery.md")
    ]
    
    for template_file, target_file in templates:
        template_path = project_root / template_file
        target_path = user_data_dir / target_file
        
        if template_path.exists():
            if not target_path.exists():
                shutil.copy2(template_path, target_path)
                print(f"✅ Created {target_path}")
                print(f"   📝 Please edit this file with your personal information")
            else:
                print(f"⚠️  {target_path} already exists, skipping")
        else:
            print(f"❌ Template file not found: {template_path}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Edit {user_data_dir}/job_summery.md with your job context")
    print(f"2. Edit {user_data_dir}/job_skill_summery.md with your skills")
    print(f"3. These files will remain private (not committed to git)")
    print(f"\n🔐 Privacy note: The user_specific_data/ directory is in .gitignore")
    print(f"   Your personal information will NOT be committed to the repository")

def main():
    """Main function"""
    print("🚀 Email Helper - User Data Setup")
    print("=" * 50)
    
    try:
        create_user_data_directory()
        print("\n✅ Setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
