"""Verify all critical Python dependencies are installed correctly.

This script checks that all required packages are installed and can be imported.
Run this script if you encounter import errors to diagnose dependency issues.

Usage:
    python scripts/verify_dependencies.py
"""

import sys
from typing import List, Tuple


def check_imports() -> Tuple[List[str], List[str]]:
    """Check if all critical dependencies can be imported.
    
    Returns:
        Tuple of (successful_imports, failed_imports)
    """
    dependencies = [
        # Core dependencies
        ("pydantic", "pydantic>=2.0.0"),
        ("pydantic_settings", "pydantic-settings>=2.0.0"),
        ("pandas", "pandas>=2.0.0"),
        ("dotenv", "python-dotenv>=1.0.0"),
        
        # Backend API
        ("fastapi", "fastapi>=0.100.0"),
        ("uvicorn", "uvicorn[standard]>=0.23.0"),
        
        # Azure OpenAI
        ("openai", "openai>=1.3.0"),
        ("azure.identity", "azure-identity>=1.15.0"),
        ("promptflow.core", "prompty>=0.1.50"),
        
        # Real-time updates
        ("websockets", "websockets>=12.0"),
        
        # Testing
        ("pytest", "pytest>=7.0.0"),
        ("pytest_mock", "pytest-mock>=3.10.0"),
        ("pytest_cov", "pytest-cov>=4.0.0"),
        ("pytest_asyncio", "pytest-asyncio>=0.21.0"),
        
        # Visualization
        ("matplotlib", "matplotlib>=3.7.0"),
    ]
    
    # Windows-only dependencies
    if sys.platform == "win32":
        dependencies.extend([
            ("win32com.client", "pywin32>=306"),
            ("pythoncom", "pywin32>=306"),
            ("pywintypes", "pywin32>=306"),
        ])
    
    successful = []
    failed = []
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
            successful.append(f"✓ {package_name}")
        except ImportError as e:
            failed.append(f"✗ {package_name}: {e}")
    
    return successful, failed


def check_package_conflicts() -> bool:
    """Check for package dependency conflicts.
    
    Returns:
        True if no conflicts, False otherwise
    """
    import subprocess
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✓ No package dependency conflicts detected")
            return True
        else:
            print("✗ Package conflicts detected:")
            print(result.stdout)
            return False
            
    except Exception as e:
        print(f"⚠ Could not check package conflicts: {e}")
        return False


def main() -> int:
    """Run dependency verification checks.
    
    Returns:
        Exit code (0 for success, 1 for failures)
    """
    print("=" * 60)
    print("Email Helper - Dependency Verification")
    print("=" * 60)
    print()
    
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    # Check imports
    print("Checking imports...")
    successful, failed = check_imports()
    
    print()
    print(f"Successful imports ({len(successful)}):")
    for item in successful:
        print(f"  {item}")
    
    if failed:
        print()
        print(f"Failed imports ({len(failed)}):")
        for item in failed:
            print(f"  {item}")
    
    print()
    print("-" * 60)
    
    # Check conflicts
    print()
    print("Checking for package conflicts...")
    no_conflicts = check_package_conflicts()
    
    print()
    print("=" * 60)
    
    if failed or not no_conflicts:
        print("❌ VERIFICATION FAILED")
        print()
        print("To fix missing dependencies, run:")
        print("  pip install -r requirements.txt")
        print()
        return 1
    else:
        print("✅ ALL DEPENDENCIES VERIFIED")
        print()
        return 0


if __name__ == "__main__":
    sys.exit(main())
