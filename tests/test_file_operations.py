#!/usr/bin/env python3
"""Test script for file operations in FileExplorer.

This script tests all the new file operation methods:
- create_folder()
- rename_item()
- delete_item()
- get_file_info()

Run this script from the repository root:
    python3 scripts/test_file_operations.py
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

from shypn.api.file import FileExplorer


def test_file_operations():
    """Test all file operations."""
    print("=" * 60)
    print("Testing FileExplorer File Operations")
    print("=" * 60)
    
    # Create a temporary directory for testing
    test_dir = tempfile.mkdtemp(prefix="shypn_test_")
    print(f"\n✓ Created test directory: {test_dir}")
    
    try:
        # Initialize explorer
        explorer = FileExplorer(base_path=test_dir)
        errors = []
        
        # Set up error callback
        def on_error(msg):
            errors.append(msg)
            print(f"  ✗ API Error: {msg}")
        
        explorer.on_error = on_error
        
        print(f"\n→ Current path: {explorer.current_path}")
        
        # Test 1: Create folder
        print("\n--- Test 1: Create Folder ---")
        success = explorer.create_folder("test_folder")
        if success:
            print("  ✓ Created folder: test_folder")
            folder_path = os.path.join(test_dir, "test_folder")
            if os.path.isdir(folder_path):
                print("  ✓ Folder exists on disk")
            else:
                print("  ✗ Folder not found on disk")
        else:
            print("  ✗ Failed to create folder")
        
        # Test 2: Try to create duplicate folder
        print("\n--- Test 2: Create Duplicate Folder (should fail) ---")
        errors.clear()
        success = explorer.create_folder("test_folder")
        if not success and errors:
            print(f"  ✓ Correctly rejected duplicate: {errors[0]}")
        else:
            print("  ✗ Should have rejected duplicate")
        
        # Test 3: Create a test file for rename/delete operations
        print("\n--- Test 3: Create Test File ---")
        test_file = os.path.join(test_dir, "test_file.txt")
        with open(test_file, 'w') as f:
            f.write("Test content")
        print(f"  ✓ Created test file: test_file.txt")
        
        # Test 4: Get file info
        print("\n--- Test 4: Get File Info ---")
        info = explorer.get_file_info(test_file)
        if info:
            print(f"  ✓ Name: {info['name']}")
            print(f"  ✓ Type: {'Directory' if info['is_directory'] else 'File'}")
            print(f"  ✓ Size: {info['size_formatted']}")
            print(f"  ✓ Modified: {info['modified_formatted']}")
            print(f"  ✓ Permissions: {info['permissions']}")
            print(f"  ✓ Readable: {info['readable']}")
            print(f"  ✓ Writable: {info['writable']}")
        else:
            print("  ✗ Failed to get file info")
        
        # Test 5: Get folder info
        print("\n--- Test 5: Get Folder Info ---")
        folder_path = os.path.join(test_dir, "test_folder")
        info = explorer.get_file_info(folder_path)
        if info:
            print(f"  ✓ Name: {info['name']}")
            print(f"  ✓ Type: {'Directory' if info['is_directory'] else 'File'}")
            print(f"  ✓ Items: {info.get('item_count', 'N/A')}")
        else:
            print("  ✗ Failed to get folder info")
        
        # Test 6: Rename file
        print("\n--- Test 6: Rename File ---")
        errors.clear()
        success = explorer.rename_item(test_file, "renamed_file.txt")
        if success:
            print("  ✓ Renamed file: test_file.txt → renamed_file.txt")
            new_path = os.path.join(test_dir, "renamed_file.txt")
            if os.path.exists(new_path) and not os.path.exists(test_file):
                print("  ✓ File renamed on disk")
                test_file = new_path  # Update path for delete test
            else:
                print("  ✗ File not properly renamed on disk")
        else:
            print("  ✗ Failed to rename file")
        
        # Test 7: Rename folder
        print("\n--- Test 7: Rename Folder ---")
        errors.clear()
        success = explorer.rename_item(folder_path, "renamed_folder")
        if success:
            print("  ✓ Renamed folder: test_folder → renamed_folder")
            new_folder_path = os.path.join(test_dir, "renamed_folder")
            if os.path.exists(new_folder_path) and not os.path.exists(folder_path):
                print("  ✓ Folder renamed on disk")
                folder_path = new_folder_path
            else:
                print("  ✗ Folder not properly renamed on disk")
        else:
            print("  ✗ Failed to rename folder")
        
        # Test 8: Try to rename to existing name (should fail)
        print("\n--- Test 8: Rename to Existing Name (should fail) ---")
        errors.clear()
        # Create another file
        another_file = os.path.join(test_dir, "another_file.txt")
        with open(another_file, 'w') as f:
            f.write("Another file")
        success = explorer.rename_item(test_file, "another_file.txt")
        if not success and errors:
            print(f"  ✓ Correctly rejected duplicate name: {errors[0]}")
        else:
            print("  ✗ Should have rejected duplicate name")
        
        # Test 9: Delete file
        print("\n--- Test 9: Delete File ---")
        errors.clear()
        success = explorer.delete_item(test_file)
        if success:
            print("  ✓ Deleted file: renamed_file.txt")
            if not os.path.exists(test_file):
                print("  ✓ File deleted from disk")
            else:
                print("  ✗ File still exists on disk")
        else:
            print("  ✗ Failed to delete file")
        
        # Test 10: Try to delete non-empty folder (should fail)
        print("\n--- Test 10: Delete Non-Empty Folder (should fail) ---")
        # Put a file in the folder
        temp_file = os.path.join(folder_path, "temp.txt")
        with open(temp_file, 'w') as f:
            f.write("temp")
        errors.clear()
        success = explorer.delete_item(folder_path)
        if not success and errors:
            print(f"  ✓ Correctly rejected non-empty folder: {errors[0]}")
        else:
            print("  ✗ Should have rejected non-empty folder")
        
        # Clean up the temp file
        os.remove(temp_file)
        
        # Test 11: Delete empty folder
        print("\n--- Test 11: Delete Empty Folder ---")
        errors.clear()
        success = explorer.delete_item(folder_path)
        if success:
            print("  ✓ Deleted folder: renamed_folder")
            if not os.path.exists(folder_path):
                print("  ✓ Folder deleted from disk")
            else:
                print("  ✗ Folder still exists on disk")
        else:
            print("  ✗ Failed to delete folder")
        
        # Test 12: Try invalid operations
        print("\n--- Test 12: Invalid Operations ---")
        
        # Empty name
        errors.clear()
        success = explorer.create_folder("")
        if not success:
            print("  ✓ Rejected empty folder name")
        
        # Invalid characters
        errors.clear()
        success = explorer.create_folder("test/folder")
        if success:  # It will sanitize and create "testfolder"
            print("  ✓ Sanitized invalid characters")
        
        # Non-existent item
        errors.clear()
        success = explorer.delete_item("/non/existent/path")
        if not success:
            print("  ✓ Rejected non-existent item")
        
        print("\n" + "=" * 60)
        print("✓ All file operations tests completed!")
        print("=" * 60)
        
    finally:
        # Clean up test directory
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n✓ Cleaned up test directory: {test_dir}")


if __name__ == '__main__':
    test_file_operations()
