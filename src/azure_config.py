#!/usr/bin/env python3
"""
Azure Configuration Manager - Azure OpenAI + Azure AD OAuth authentication
Uses DefaultAzureCredential (az login) with fallback to environment variables
Supports OAuth Single Sign-On with service principal identity
"""

import os
from typing import Optional

# Optional import for dotenv - only needed for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available - rely on environment variables only
    pass

class AzureConfig:
    """Secure Azure OpenAI configuration management"""
    
    def __init__(self):
        self.endpoint = self._get_endpoint()
        self.deployment = self._get_deployment() 
        self.api_version = self._get_api_version()
        self._validate_config()
    
    def _get_endpoint(self) -> str:
        """Get Azure OpenAI endpoint"""
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        if not endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")
        return endpoint.rstrip('/')
    
    def _get_deployment(self) -> str:
        """Get Azure OpenAI deployment name"""
        deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
        return deployment
    
    def _get_api_version(self) -> str:
        """Get Azure OpenAI API version"""
        return os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment (fallback authentication)"""
        return os.getenv('AZURE_OPENAI_API_KEY')
    
    def use_azure_credential(self) -> bool:
        """Check if we should use DefaultAzureCredential (preferred)"""
        # Use Azure credential if no API key is explicitly set
        # This allows az login to work seamlessly
        return self.get_api_key() is None
    
    def get_azure_credential(self):
        """Get Azure credential for authentication"""
        try:
            from azure.identity import DefaultAzureCredential
            return DefaultAzureCredential()
        except ImportError:
            raise ImportError(
                "azure-identity package is required for Azure authentication. "
                "Install it with: pip install azure-identity"
            )
    
    def get_openai_client(self):
        """Get configured Azure OpenAI client"""
        try:
            from openai import AzureOpenAI
            
            if self.use_azure_credential():
                # Use DefaultAzureCredential (preferred - works with az login)
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider
                
                # Convert OpenAI endpoint to cognitive services endpoint if needed
                cognitive_endpoint = self.endpoint.replace('.openai.azure.com', '.cognitiveservices.azure.com')
                
                token_provider = get_bearer_token_provider(
                    DefaultAzureCredential(), 
                    "https://cognitiveservices.azure.com/.default"
                )
                
                client = AzureOpenAI(
                    api_version=self.api_version,
                    azure_endpoint=cognitive_endpoint,
                    azure_ad_token_provider=token_provider
                )
                print("✅ Using Azure credential authentication (az login)")
            else:
                # Fallback to API key
                api_key = self.get_api_key()
                client = AzureOpenAI(
                    api_key=api_key,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                )
                print("⚠️  Using API key authentication (consider using az login)")
            
            return client
            
        except ImportError:
            raise ImportError(
                "openai package is required. Install it with: pip install openai"
            )
    
    def get_prompty_config(self) -> dict:
        """Get configuration for prompty files"""
        config = {
            "type": "azure_openai",
            "azure_endpoint": self.endpoint,
            "azure_deployment": self.deployment,
            "api_version": self.api_version
        }
        
        if not self.use_azure_credential():
            # Only add API key if not using Azure credential
            api_key = self.get_api_key()
            if api_key:
                config["api_key"] = api_key
        else:
            # For Azure credential, we need to use a token provider
            # But prompty may not support this directly, so we'll handle it in the execution
            pass
        
        return config
    
    def get_promptflow_config(self):
        """Get configuration for promptflow/prompty integration"""
        try:
            from promptflow.core import AzureOpenAIModelConfiguration
            
            if self.use_azure_credential():
                # Use DefaultAzureCredential
                config = AzureOpenAIModelConfiguration(
                    azure_deployment=self.deployment,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint
                    # promptflow will automatically use DefaultAzureCredential when no api_key is provided
                )
                print("✅ Using PromptFlow with Azure DefaultCredential")
            else:
                # Use API key
                config = AzureOpenAIModelConfiguration(
                    azure_deployment=self.deployment,
                    api_version=self.api_version,
                    azure_endpoint=self.endpoint,
                    api_key=self.get_api_key()
                )
            
            return config
            
        except ImportError:
            raise ImportError(
                "promptflow package is required for this configuration method. "
                "Install it with: pip install promptflow"
            )
    
    def _validate_config(self):
        """Validate configuration"""
        if not self.endpoint:
            raise ValueError("Azure OpenAI endpoint is required")
        
        if not self.deployment:
            raise ValueError("Azure OpenAI deployment is required")
        
        # Check if we have either Azure credential capability or API key
        has_azure_identity = False
        try:
            from azure.identity import DefaultAzureCredential
            has_azure_identity = True
        except ImportError:
            pass
        
        has_api_key = self.get_api_key() is not None
        
        if not has_azure_identity and not has_api_key:
            raise ValueError(
                "No authentication method available. Either:\n"
                "1. Install azure-identity and run 'az login', or\n" 
                "2. Set AZURE_OPENAI_API_KEY environment variable"
            )
    
    def __str__(self) -> str:
        """String representation of configuration"""
        auth_method = "Azure Credential" if self.use_azure_credential() else "API Key"
        return (
            f"AzureConfig(\n"
            f"  endpoint={self.endpoint}\n"
            f"  deployment={self.deployment}\n" 
            f"  api_version={self.api_version}\n"
            f"  auth_method={auth_method}\n"
            f")"
        )

# Global configuration instance
_config_instance = None

def get_azure_config() -> AzureConfig:
    """Get global Azure configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AzureConfig()
    return _config_instance

def test_azure_connection():
    """Test Azure OpenAI connection"""
    try:
        config = get_azure_config()
        print(f"🔧 Azure Configuration:")
        print(f"   Endpoint: {config.endpoint}")
        print(f"   Deployment: {config.deployment}")
        print(f"   API Version: {config.api_version}")
        print(f"   Auth Method: {'Azure Credential' if config.use_azure_credential() else 'API Key'}")
        
        # Test connection
        client = config.get_openai_client()
        
        # Simple test call
        response = client.chat.completions.create(
            model=config.deployment,
            messages=[{"role": "user", "content": "Say 'connection test successful'"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content.strip()
        print(f"✅ Connection test successful: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_azure_connection()
