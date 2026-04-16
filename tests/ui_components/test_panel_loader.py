"""Tests for PanelLoader to verify UI/implementation decoupling.

This test verifies that:
1. PanelLoader correctly finds /ui/ at repo root
2. Can load existing .ui files
3. Properly validates paths and files
"""

import pytest
from pathlib import Path
from shypn.loaders import PanelLoader


def test_panel_loader_finds_ui_root():
    """Test that PanelLoader correctly finds /ui/ at repo root."""
    loader = PanelLoader()
    
    # Should find ui root
    assert loader.ui_root.exists()
    assert loader.ui_root.name == "ui"
    
    # Should be at repo root (not in src/)
    assert "src" not in str(loader.ui_root)


def test_panel_loader_finds_existing_ui_files():
    """Test that PanelLoader can find existing .ui files."""
    loader = PanelLoader()
    
    # Check that known UI files exist
    assert loader.ui_file_exists("panels/left_panel.ui")
    assert loader.ui_file_exists("panels/right_panel.ui")
    assert loader.ui_file_exists("canvas/model_canvas.ui")
    assert loader.ui_file_exists("palettes/edit_palette.ui")


def test_panel_loader_get_ui_path():
    """Test that get_ui_path returns correct paths."""
    loader = PanelLoader()
    
    path = loader.get_ui_path("panels/left_panel.ui")
    
    # Should be absolute path
    assert path.is_absolute()
    
    # Should end with correct path
    assert str(path).endswith("ui/panels/left_panel.ui")
    
    # Should exist
    assert path.exists()


def test_panel_loader_detects_missing_ui_file():
    """Test that PanelLoader detects when UI file doesn't exist."""
    loader = PanelLoader()
    
    # Non-existent file should return False
    assert not loader.ui_file_exists("panels/nonexistent.ui")


def test_panel_loader_custom_ui_root():
    """Test that PanelLoader accepts custom UI root."""
    # Get actual UI root
    loader_auto = PanelLoader()
    ui_root = loader_auto.ui_root
    
    # Create loader with explicit root
    loader_explicit = PanelLoader(ui_root=ui_root)
    
    # Should use the provided root
    assert loader_explicit.ui_root == ui_root


if __name__ == "__main__":
    # Run tests manually
    test_panel_loader_finds_ui_root()
    print("✓ Finds UI root")
    
    test_panel_loader_finds_existing_ui_files()
    print("✓ Finds existing UI files")
    
    test_panel_loader_get_ui_path()
    print("✓ Returns correct paths")
    
    test_panel_loader_detects_missing_ui_file()
    print("✓ Detects missing files")
    
    test_panel_loader_custom_ui_root()
    print("✓ Accepts custom UI root")
    
    print("\n✅ All PanelLoader tests passed!")
