#!/usr/bin/env python3
"""
Azure AD OAuth Setup Script for Email Helper

This script helps you configure Azure AD OAuth single sign-on for the Email Helper application.
It will guide you through:
1. Creating an Azure AD App Registration
2. Configuring the necessary permissions  
3. Setting up the .env file with the correct values
4. Testing the OAuth configuration
"""

import os
import sys
import webbrowser
import subprocess
from pathlib import Path
import json
import uuid

def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step_num, title):
    print(f"\n🔧 Step {step_num}: {title}")
    print("-" * 50)

def open_azure_portal():
    """Open Azure portal for app registration"""
    portal_url = "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade"
    print(f"📖 Opening Azure Portal: {portal_url}")
    try:
        webbrowser.open(portal_url)
        return True
    except Exception as e:
        print(f"❌ Could not open browser: {e}")
        print(f"   Please manually go to: {portal_url}")
        return False

def create_app_registration_automated():
    """Create Azure AD app registration using Azure CLI"""
    
    print_step(1, "Create Azure AD App Registration (Automated)")
    
    try:
        # Check if Azure CLI is available and user is logged in
        result = subprocess.run(["az", "account", "show"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Azure CLI not logged in. Please run 'az login' first.")
            return None
        
        account_info = json.loads(result.stdout)
        tenant_id = account_info["tenantId"]
        print(f"✅ Logged into Azure tenant: {account_info['tenantDisplayName']} ({tenant_id})")
        
        # Generate app registration details
        app_name = "Email Helper OAuth"
        redirect_uri = "http://localhost:8001/auth/callback"
        
        print(f"📝 Creating app registration: {app_name}")
        
        # Create the app registration as a Public Client (SPA) for PKCE flow
        create_cmd = [
            "az", "ad", "app", "create",
            "--display-name", app_name,
            "--public-client-redirect-uris", redirect_uri,
            "--required-resource-accesses", json.dumps([
                {
                    "resourceAppId": "00000003-0000-0000-c000-000000000000",  # Microsoft Graph
                    "resourceAccess": [
                        {
                            "id": "e1fe6dd8-ba31-4d61-89e7-88639da4683d",  # User.Read
                            "type": "Scope"
                        },
                        {
                            "id": "570282fd-fa5c-430d-a7fd-fc8dc98a9dca",  # Mail.Read
                            "type": "Scope"
                        },
                        {
                            "id": "024d486e-b451-40bb-833d-3e66d98c5c73",  # Mail.ReadWrite
                            "type": "Scope"
                        },
                        {
                            "id": "e383f46e-2787-4529-855e-0e479a3ffac0",  # Mail.Send
                            "type": "Scope"
                        },
                        {
                            "id": "b340eb25-3456-403f-be2f-af7a0d370277",  # User.ReadBasic.All
                            "type": "Scope"
                        }
                    ]
                }
            ])
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to create app registration: {result.stderr}")
            return get_app_registration_details_manual()
        
        app_data = json.loads(result.stdout)
        client_id = app_data["appId"]
        
        print(f"✅ Created app registration with Client ID: {client_id}")
        
        # No client secret needed for Public Client Application with PKCE
        print("✅ Public Client Application created (no client secret needed for PKCE flow)")
        
        return {
            "client_id": client_id,
            "tenant_id": tenant_id,
            "redirect_uri": redirect_uri
        }
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Azure CLI command failed: {e}")
        return get_app_registration_details_manual()
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse Azure CLI response: {e}")
        return get_app_registration_details_manual()
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return get_app_registration_details_manual()

def get_app_registration_details_manual():
    """Guide user through manual app registration and collect details"""
    
    print_step(1, "Create Azure AD App Registration (Manual)")
    
    print("""
📝 In the Azure Portal, please:

1. Click '+ New registration'
2. Fill out the form:
   - Name: 'Email Helper OAuth'
   - Supported account types: 'Accounts in this organizational directory only'
   - Redirect URI: 
     - Platform: Web
     - URI: http://localhost:8001/auth/callback

3. Click 'Register'
4. On the overview page, copy the following values:
""")
    
    # Collect app registration details
    client_id = input("🔑 Application (client) ID: ").strip()
    tenant_id = input("🏢 Directory (tenant) ID: ").strip()
    
    if not client_id or not tenant_id:
        print("❌ Client ID and Tenant ID are required!")
        return None
    
    print_step(2, "Configure as Public Client (No Secret Needed)")
    
    print("""
📝 In the Azure Portal:

1. Go to 'Authentication' in the left menu
2. Under 'Platform configurations', ensure you have:
   - Platform: Public client/native (mobile & desktop)
   - Redirect URI: http://localhost:8001/auth/callback
3. Under 'Advanced settings', set:
   - 'Allow public client flows': Yes
   - 'Supported account types': Accounts in this organizational directory only

ℹ️  No client secret is needed for Public Client applications with PKCE flow!
""")
    
    input("Press Enter when you've configured the authentication settings...")
    
    # No client secret for public client
    
    print_step(3, "Configure API Permissions")
    
    print("""
📝 In the Azure Portal:

1. Go to 'API permissions' in the left menu
2. Click '+ Add a permission'
3. Choose 'Microsoft Graph'
4. Choose 'Delegated permissions'
5. Add these permissions:
   ✅ User.Read (should already be present)
   ✅ Mail.Read
   ✅ Mail.ReadWrite  
   ✅ Mail.Send
   ✅ User.ReadBasic.All

6. Click 'Add permissions'
7. If you're an admin, click 'Grant admin consent' (recommended)
""")
    
    input("Press Enter when you've completed the API permissions setup...")
    
    return {
        "client_id": client_id,
        "tenant_id": tenant_id,
        "redirect_uri": "http://localhost:8001/auth/callback"
    }

def update_env_file(config):
    """Update the .env file with Azure AD configuration"""
    
    print_step(4, "Update Environment Configuration")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("❌ .env file not found. Creating from template...")
        # Copy from .env.example if it exists
        example_path = Path(".env.example")
        if example_path.exists():
            with open(example_path, 'r') as f:
                content = f.read()
            with open(env_path, 'w') as f:
                f.write(content)
        else:
            # Create basic .env file
            content = """# Email Helper Configuration
SECRET_KEY=change-this-in-production
DEBUG=true

# Azure AD OAuth Configuration
GRAPH_CLIENT_ID=
GRAPH_CLIENT_SECRET=
GRAPH_TENANT_ID=  
GRAPH_REDIRECT_URI=http://localhost:8001/auth/callback

# Azure OpenAI (if using AI features)
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=gpt-4o
"""
            with open(env_path, 'w') as f:
                f.write(content)
    
    # Read current .env content
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update Azure AD values (no client secret needed for PKCE)
    replacements = {
        'GRAPH_CLIENT_ID="your-azure-ad-app-client-id"': f'GRAPH_CLIENT_ID="{config["client_id"]}"',
        'GRAPH_TENANT_ID="your-azure-ad-tenant-id"': f'GRAPH_TENANT_ID="{config["tenant_id"]}"',
        'GRAPH_REDIRECT_URI="http://localhost:8000/auth/callback"': f'GRAPH_REDIRECT_URI="{config["redirect_uri"]}"',
        
        # Handle cases where values might not have quotes
        'GRAPH_CLIENT_ID=': f'GRAPH_CLIENT_ID="{config["client_id"]}"',
        'GRAPH_TENANT_ID=': f'GRAPH_TENANT_ID="{config["tenant_id"]}"',
        
        # Remove client secret lines since we don't use them
        'GRAPH_CLIENT_SECRET="your-azure-ad-app-client-secret"': '# GRAPH_CLIENT_SECRET not needed for PKCE flow',
        'GRAPH_CLIENT_SECRET=': '# GRAPH_CLIENT_SECRET not needed for PKCE flow',
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Updated {env_path} with your Azure AD configuration")

def test_configuration():
    """Test the OAuth configuration"""
    
    print_step(5, "Test Configuration")
    
    print("🧪 Testing OAuth configuration...")
    
    try:
        import requests
        
        # Test the login endpoint
        response = requests.get("http://localhost:8001/auth/login")
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get("auth_url", "")
            
            if "login.microsoftonline.com" in auth_url or "mock-callback" in auth_url:
                print("✅ OAuth endpoints are working!")
                
                if "mock-callback" in auth_url:
                    print("   (Currently using mock authentication for development)")
                else:
                    print("   (Real Azure AD OAuth is configured)")
                
                return True
            else:
                print("❌ Unexpected auth URL format")
                return False
        else:
            print(f"❌ API server returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API server")
        print("   Make sure the server is running: python simple_api.py")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    
    print_header("Azure AD OAuth Setup for Email Helper")
    
    print("""
🎯 This script will help you set up Azure AD OAuth single sign-on.

Prerequisites:
✅ You have an Azure subscription
✅ You have permissions to create app registrations in Azure AD
✅ The Email Helper API server is running (python simple_api.py)

Let's get started!
""")
    
    # Check if API server is running
    try:
        import requests
        response = requests.get("http://localhost:8001/")
        if response.status_code != 200:
            print("❌ API server is not running correctly")
            return False
    except:
        print("❌ API server is not running")
        print("   Please start it first: python simple_api.py")
        return False
    
    # Open Azure Portal
    print("\n🌐 Opening Azure Portal...")
    open_azure_portal()
    
    # Try automated app registration first, fall back to manual
    print("\n🤖 Attempting automated setup with Azure CLI...")
    config = create_app_registration_automated()
    
    if not config:
        print("\n📖 Falling back to manual setup...")
        open_azure_portal()
        config = get_app_registration_details_manual()
    
    if not config:
        print("❌ Setup cancelled or incomplete")
        return False
    
    # Update .env file
    update_env_file(config)
    
    # Test configuration
    test_result = test_configuration()
    
    # Final summary
    print_header("Setup Complete!")
    
    if test_result:
        print("✅ Azure AD OAuth is configured and working!")
        print("""
📚 Next steps:
1. Restart the API server: python simple_api.py
2. Open the frontend: http://localhost:3000
3. Click 'Sign in with Microsoft' to test OAuth flow
4. Check server logs for authentication details

🔐 Security Notes:
- Keep your client secret secure and never commit it to version control
- The .env file is already in .gitignore
- Consider using shorter secret expiration in production
- Review API permissions regularly
""")
    else:
        print("⚠️  Configuration saved but testing failed")
        print("   You may need to restart the API server and try again")
    
    return test_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
