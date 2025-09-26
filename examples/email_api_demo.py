#!/usr/bin/env python3
"""
Email Helper API Demo - T2 Email Service Interface

This script demonstrates the complete email service interface functionality
including Microsoft Graph API integration and REST API endpoints.

Usage:
    python examples/email_api_demo.py

Prerequisites:
    1. Start the API server: python -m uvicorn backend.main:app --reload
    2. (Optional) Configure Graph API credentials in .env for real integration
"""

import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_demo():
    """Run a simplified API demonstration."""
    base_url = "http://localhost:8000"
    
    print("🚀 Email Helper API T2 Demo")
    print("=" * 40)
    
    try:
        # Test health check
        print("🏥 Testing health check...")
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API Health: {health['status']}")
            print(f"   Service: {health['service']} v{health['version']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return
        
        # Test API documentation
        print("\n📚 Testing API documentation...")
        response = requests.get(f"{base_url}/docs")
        if response.status_code == 200:
            print("✅ API documentation available at: http://localhost:8000/docs")
        
        print("\n🎉 Basic demo completed!")
        print("\nTo run the full interactive demo:")
        print("1. Ensure the API server is running")
        print("2. Install requests: pip install requests")
        print("3. Run the full demo script")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API server")
        print("Please start the server with: python -m uvicorn backend.main:app --reload")
        return False
    
    return True


if __name__ == "__main__":
    run_demo()