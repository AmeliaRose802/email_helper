#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick Azure OpenAI setup for Amelia's email classification system

.DESCRIPTION
    Sets up Azure OpenAI environment variables based on the provided Azure information
#>

Write-Host "🔧 AZURE OPENAI QUICK SETUP" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Set the known endpoint from azure_info.md
$env:AZURE_OPENAI_ENDPOINT = "https://ameliapayne-5039-test-e-resource.openai.azure.com/"
[Environment]::SetEnvironmentVariable("AZURE_OPENAI_ENDPOINT", $env:AZURE_OPENAI_ENDPOINT, "User")
Write-Host "✅ Set AZURE_OPENAI_ENDPOINT = $($env:AZURE_OPENAI_ENDPOINT)" -ForegroundColor Green

# Set default API version
$env:AZURE_OPENAI_API_VERSION = "2024-02-01"
[Environment]::SetEnvironmentVariable("AZURE_OPENAI_API_VERSION", $env:AZURE_OPENAI_API_VERSION, "User")
Write-Host "✅ Set AZURE_OPENAI_API_VERSION = $($env:AZURE_OPENAI_API_VERSION)" -ForegroundColor Green

Write-Host ""
Write-Host "🔑 You still need to set:" -ForegroundColor Yellow
Write-Host "1. AZURE_OPENAI_API_KEY - Get this from Azure portal → Your OpenAI resource → Keys and Endpoint" -ForegroundColor White
Write-Host "2. AZURE_OPENAI_DEPLOYMENT - The name of your GPT model deployment" -ForegroundColor White
Write-Host ""
Write-Host "📋 Manual setup commands:" -ForegroundColor Cyan
Write-Host "`$env:AZURE_OPENAI_API_KEY = 'your-api-key-here'" -ForegroundColor Gray
Write-Host "`$env:AZURE_OPENAI_DEPLOYMENT = 'gpt-4'" -ForegroundColor Gray
Write-Host ""
Write-Host "💾 To make these permanent:" -ForegroundColor Cyan  
Write-Host "[Environment]::SetEnvironmentVariable('AZURE_OPENAI_API_KEY', 'your-key', 'User')" -ForegroundColor Gray
Write-Host "[Environment]::SetEnvironmentVariable('AZURE_OPENAI_DEPLOYMENT', 'gpt-4', 'User')" -ForegroundColor Gray
Write-Host ""

# Test if we can import the modules
Write-Host "🧪 Testing Python modules..." -ForegroundColor Yellow
try {
    python -c "from openai import AzureOpenAI; print('✅ OpenAI module available')"
}
catch {
    Write-Host "❌ OpenAI module not available" -ForegroundColor Red
}

try {
    python -c "import win32com.client; print('✅ Win32com module available')"  
}
catch {
    Write-Host "❌ Win32com module not available" -ForegroundColor Red
}

try {
    python -c "import pandas; print('✅ Pandas module available')"
}
catch {
    Write-Host "❌ Pandas module not available" -ForegroundColor Red
}

Write-Host ""
Write-Host "🚀 Next steps:" -ForegroundColor Green
Write-Host "1. Get your API key from Azure portal" -ForegroundColor White
Write-Host "2. Set the AZURE_OPENAI_API_KEY environment variable" -ForegroundColor White
Write-Host "3. Set the AZURE_OPENAI_DEPLOYMENT to your model name (e.g., 'gpt-4')" -ForegroundColor White
Write-Host "4. Run: python interactive_learning_system.py" -ForegroundColor White
