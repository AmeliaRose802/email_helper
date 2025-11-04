"""Clean Python cache directories to resolve import errors.

This script removes mypy cache and __pycache__ directories that can
cause stale import errors in VS Code and other Python tools.

Usage:
    python scripts/clean_caches.py
"""

import os
import shutil
from pathlib import Path
from typing import List


def find_cache_dirs(root_path: Path, dir_name: str) -> List[Path]:
    """Find all directories with a specific name under root path.
    
    Args:
        root_path: Root directory to search from
        dir_name: Directory name to find (e.g., '__pycache__')
        
    Returns:
        List of Path objects for matching directories
    """
    cache_dirs = []
    for dirpath, dirnames, _ in os.walk(root_path):
        if dir_name in dirnames:
            cache_dirs.append(Path(dirpath) / dir_name)
    return cache_dirs


def main() -> None:
    """Clean all Python cache directories."""
    
    project_root = Path(__file__).parent.parent
    print(f"Cleaning caches in: {project_root}\n")
    
    # Clean mypy cache
    mypy_cache = project_root / ".mypy_cache"
    if mypy_cache.exists():
        print(f"Removing {mypy_cache}...")
        shutil.rmtree(mypy_cache, ignore_errors=True)
        print("  ✓ .mypy_cache removed")
    else:
        print("  ⊗ .mypy_cache not found")
    
    # Clean all __pycache__ directories
    print("\nFinding __pycache__ directories...")
    pycache_dirs = find_cache_dirs(project_root, "__pycache__")
    
    if pycache_dirs:
        print(f"Found {len(pycache_dirs)} __pycache__ directories")
        removed_count = 0
        for cache_dir in pycache_dirs:
            try:
                shutil.rmtree(cache_dir, ignore_errors=True)
                removed_count += 1
            except Exception as e:
                print(f"  Warning: Could not remove {cache_dir}: {e}")
        print(f"  ✓ Removed {removed_count} __pycache__ directories")
    else:
        print("  ⊗ No __pycache__ directories found")
    
    # Clean pytest cache
    pytest_cache = project_root / ".pytest_cache"
    if pytest_cache.exists():
        print(f"\nRemoving {pytest_cache}...")
        shutil.rmtree(pytest_cache, ignore_errors=True)
        print("  ✓ .pytest_cache removed")
    
    print("\n" + "=" * 60)
    print("✅ Cache cleanup complete!")
    print("\nNext steps:")
    print("  1. Reload VS Code window: Ctrl+Shift+P -> 'Developer: Reload Window'")
    print("  2. Or restart Python language server: Ctrl+Shift+P -> 'Python: Restart Language Server'")


if __name__ == "__main__":
    main()
