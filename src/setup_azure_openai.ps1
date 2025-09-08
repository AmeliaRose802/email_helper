#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup script for Azure OpenAI integration with Interactive Email Learning System

.DESCRIPTION
    This script helps configure the Azure OpenAI environment variables needed for the email classification system.
    It will guide you through setting up the connection to your Azure AI Foundry project.

.NOTES
    Author: Interactive Email Learning System
    Date: $(Get-Date)
#>

Write-Host "🔧 AZURE OPENAI SETUP FOR EMAIL CLASSIFICATION" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Check if we're running with the right permissions
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "⚠️  Note: Running without administrator privileges. Environment variables will be set for current user only." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "This script will help you configure Azure OpenAI for intelligent email classification." -ForegroundColor Green
Write-Host ""
Write-Host "You'll need the following information from your Azure AI Foundry project:" -ForegroundColor White
Write-Host "1. Azure OpenAI Endpoint URL" -ForegroundColor Yellow
Write-Host "2. API Key" -ForegroundColor Yellow  
Write-Host "3. Deployment Name (model name)" -ForegroundColor Yellow
Write-Host "4. API Version (optional, defaults to 2024-02-01)" -ForegroundColor Yellow
Write-Host ""

# Function to set environment variable
function Set-EnvVar {
    param(
        [string]$Name,
        [string]$Value,
        [bool]$Secure = $false
    )
    
    if ($Secure) {
        Write-Host "Setting $Name..." -ForegroundColor Green
    }
    else {
        Write-Host "Setting $Name = $Value" -ForegroundColor Green
    }
    
    # Set for current session
    [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
    
    # Set persistently for user
    [Environment]::SetEnvironmentVariable($Name, $Value, "User")
}

# Get Azure OpenAI Endpoint
do {
    $endpoint = Read-Host "Enter your Azure OpenAI Endpoint URL (e.g., https://your-resource.openai.azure.com/)"
    if ([string]::IsNullOrWhiteSpace($endpoint)) {
        Write-Host "❌ Endpoint cannot be empty!" -ForegroundColor Red
    }
    elseif (-not $endpoint.StartsWith("https://")) {
        Write-Host "❌ Endpoint must start with https://" -ForegroundColor Red
        $endpoint = $null
    }
} while ([string]::IsNullOrWhiteSpace($endpoint))

# Get API Key
do {
    $apiKey = Read-Host "Enter your Azure OpenAI API Key" -AsSecureString
    $apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey))
    if ([string]::IsNullOrWhiteSpace($apiKeyPlain)) {
        Write-Host "❌ API Key cannot be empty!" -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($apiKeyPlain))

# Get Deployment Name
do {
    $deployment = Read-Host "Enter your Azure OpenAI Deployment Name (e.g., gpt-4, gpt-35-turbo)"
    if ([string]::IsNullOrWhiteSpace($deployment)) {
        Write-Host "❌ Deployment name cannot be empty!" -ForegroundColor Red
    }
} while ([string]::IsNullOrWhiteSpace($deployment))

# Get API Version (optional)
$apiVersion = Read-Host "Enter API Version (press Enter for default: 2024-02-01)"
if ([string]::IsNullOrWhiteSpace($apiVersion)) {
    $apiVersion = "2024-02-01"
}

Write-Host ""
Write-Host "📝 Setting environment variables..." -ForegroundColor Cyan

# Set environment variables
Set-EnvVar -Name "AZURE_OPENAI_ENDPOINT" -Value $endpoint
Set-EnvVar -Name "AZURE_OPENAI_API_KEY" -Value $apiKeyPlain -Secure $true
Set-EnvVar -Name "AZURE_OPENAI_DEPLOYMENT" -Value $deployment  
Set-EnvVar -Name "AZURE_OPENAI_API_VERSION" -Value $apiVersion

Write-Host ""
Write-Host "✅ Azure OpenAI configuration complete!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Environment Variables Set:" -ForegroundColor White
Write-Host "   AZURE_OPENAI_ENDPOINT = $endpoint" -ForegroundColor Gray
Write-Host "   AZURE_OPENAI_API_KEY = [HIDDEN]" -ForegroundColor Gray
Write-Host "   AZURE_OPENAI_DEPLOYMENT = $deployment" -ForegroundColor Gray
Write-Host "   AZURE_OPENAI_API_VERSION = $apiVersion" -ForegroundColor Gray
Write-Host ""
Write-Host "🔄 Please restart your PowerShell session or VS Code to load the new environment variables." -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Install the OpenAI Python package: pip install openai" -ForegroundColor White
Write-Host "2. Restart PowerShell/VS Code" -ForegroundColor White  
Write-Host "3. Run your email classification system: python email_manager.py" -ForegroundColor White
Write-Host ""
Write-Host "🧪 Test Connection:" -ForegroundColor Cyan
$testChoice = Read-Host "Would you like to test the connection now? (y/n)"

if ($testChoice -eq 'y' -or $testChoice -eq 'Y') {
    Write-Host "🔍 Testing Azure OpenAI connection..." -ForegroundColor Yellow
    
    # Create a simple test script
    $testScript = @"
import os
try:
    from openai import AzureOpenAI
    
    client = AzureOpenAI(
        azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        api_key=os.getenv('AZURE_OPENAI_API_KEY'),
        api_version=os.getenv('AZURE_OPENAI_API_VERSION')
    )
    
    # Simple test call
    response = client.chat.completions.create(
        model=os.getenv('AZURE_OPENAI_DEPLOYMENT'),
        messages=[{"role": "user", "content": "Say 'Connection test successful!'"}],
        max_tokens=10
    )
    
    print("✅ Connection successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except ImportError:
    print("❌ OpenAI library not installed. Run: pip install openai")
except Exception as e:
    print(f"❌ Connection failed: {str(e)}")
"@

    $testScript | Out-File -FilePath "test_azure_openai.py" -Encoding utf8
    
    try {
        python test_azure_openai.py
    }
    catch {
        Write-Host "❌ Failed to run test. Make sure Python is installed and in PATH." -ForegroundColor Red
    }
    
    # Clean up test file
    if (Test-Path "test_azure_openai.py") {
        Remove-Item "test_azure_openai.py"
    }
}

Write-Host ""
Write-Host "🎉 Setup complete! Your email classification system is now ready to use Azure OpenAI." -ForegroundColor Green
