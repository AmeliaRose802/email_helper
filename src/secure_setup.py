#!/usr/bin/env python3
"""
Secure Setup Script for Email Helper
Installs dependencies and configures secure Azure authentication
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_azure_cli():
    """Check if Azure CLI is installed and user is logged in"""
    print("🔍 Checking Azure CLI...")
    
    # Check if az command exists
    try:
        result = subprocess.run("az --version", shell=True, check=True, capture_output=True, text=True)
        print("✅ Azure CLI is installed")
        
        # Check if user is logged in
        try:
            result = subprocess.run("az account show", shell=True, check=True, capture_output=True, text=True)
            print("✅ You are logged in to Azure CLI")
            return True
        except subprocess.CalledProcessError:
            print("⚠️  You are not logged in to Azure CLI")
            print("   Run 'az login' to authenticate with Azure")
            return False
            
    except subprocess.CalledProcessError:
        print("❌ Azure CLI is not installed")
        print("   Please install Azure CLI from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        return False

def setup_environment():
    """Set up the environment file"""
    env_file = Path(".env")
    env_template = Path(".env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_template.exists():
        print("📝 Creating .env file from template...")
        with open(env_template, 'r') as template:
            content = template.read()
        
        # Replace template values with actual values
        content = content.replace(
            "AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/",
            "AZURE_OPENAI_ENDPOINT=https://ameliapayne-5039-test-e-resource.openai.azure.com/"
        )
        content = content.replace(
            "AZURE_OPENAI_DEPLOYMENT=gpt-4o",
            "AZURE_OPENAI_DEPLOYMENT=gpt-4o"
        )
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print("✅ .env file created successfully")
        print("⚠️  Please review and update the .env file with your configuration")
        return True
    
    print("❌ .env.template not found")
    return False

def setup_user_data():
    """Set up user-specific data files"""
    print("👤 Setting up user-specific data...")
    
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    user_data_dir = project_root / 'user_specific_data'
    
    # Ensure user_specific_data directory exists
    user_data_dir.mkdir(exist_ok=True)
    
    # Set up username.txt
    username_file = user_data_dir / 'username.txt'
    if not username_file.exists():
        print("📝 Setting up username configuration...")
        
        # Try to get current user's login name as default
        import getpass
        default_username = getpass.getuser()
        
        print(f"   Current system username: {default_username}")
        username = input(f"   Enter your email username/alias (press Enter for '{default_username}'): ").strip()
        
        if not username:
            username = default_username
            
        try:
            with open(username_file, 'w', encoding='utf-8') as f:
                f.write(username)
            print(f"✅ Username '{username}' saved to {username_file}")
        except Exception as e:
            print(f"❌ Failed to create username file: {e}")
            return False
    else:
        with open(username_file, 'r', encoding='utf-8') as f:
            username = f.read().strip()
        print(f"✅ Username file exists: '{username}'")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    # Install requirements
    if not run_command("pip install -r requirements.txt", "Installing requirements"):
        return False
    
    print("✅ All dependencies installed successfully")
    return True

def test_configuration():
    """Test the Azure configuration"""
    print("🧪 Testing Azure OpenAI configuration...")
    
    try:
        # Import our secure configuration
        sys.path.append(os.path.join(os.path.dirname(__file__)))
        from azure_config import test_azure_connection
        
        if test_azure_connection():
            print("✅ Azure OpenAI configuration is working correctly!")
            return True
        else:
            print("❌ Azure OpenAI configuration test failed")
            return False
            
    except ImportError as e:
        print(f"❌ Could not import azure_config: {e}")
        print("   Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Email Helper with Secure Azure Authentication")
    print("=" * 60)
    
    # Change to script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    success = True
    
    # Step 1: Install dependencies
    if not install_dependencies():
        success = False
    
    # Step 2: Set up environment
    if not setup_environment():
        success = False
    
    # Step 3: Set up user-specific data
    if not setup_user_data():
        success = False
    
    # Step 4: Check Azure CLI
    azure_cli_ok = check_azure_cli()
    
    # Step 5: Test configuration
    if not test_configuration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Setup completed successfully!")
        
        if azure_cli_ok:
            print("\n🎉 You're ready to use the Email Helper!")
            print("   The system will use your Azure CLI authentication (az login)")
        else:
            print("\n⚠️  Setup completed but Azure CLI authentication not available")
            print("   The system will fall back to API key authentication")
            print("   For better security, install Azure CLI and run 'az login'")
            
        print("\n📚 Next steps:")
        print("   1. Review your .env file configuration")
        print("   2. Run: python email_manager_main.py")
        print("   3. (Optional) Run 'az login' for enhanced security")
        
    else:
        print("❌ Setup encountered errors")
        print("   Please review the error messages above and fix any issues")
        
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
