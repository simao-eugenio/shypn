"""Workspace Settings - Persist window state and user preferences.

This module handles saving and restoring:
- Window geometry (size, position)
- Window state (maximized)
- User preferences

Settings are stored in ~/.config/shypn/workspace.json
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class WorkspaceSettings:
    """Manages workspace settings persistence."""
    
    def __init__(self):
        """Initialize workspace settings."""
        # Determine config directory
        config_dir = os.path.join(Path.home(), '.config', 'shypn')
        self.config_file = os.path.join(config_dir, 'workspace.json')
        
        # Create config directory if needed
        os.makedirs(config_dir, exist_ok=True)
        
        # Default settings
        self.settings = {
            "window": {
                "width": 1200,
                "height": 800,
                "x": None,  # None = let window manager decide
                "y": None,
                "maximized": False
            },
            "editor": {
                "snap_to_grid": True,  # Snap to grid enabled by default
                "grid_spacing": 10.0   # Default grid spacing in pixels
            }
        }
        
        # Load existing settings
        self.load()
    
    def load(self) -> None:
        """Load settings from file."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge loaded settings with defaults
                    self.settings.update(loaded)
            except Exception as e:
                print(f"Warning: Could not load workspace settings: {e}", file=sys.stderr)
    
    def save(self) -> None:
        """Save settings to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save workspace settings: {e}", file=sys.stderr)
    
    def get_window_geometry(self) -> Dict[str, Any]:
        """Get window geometry settings.
        
        Returns:
            dict: Window settings (width, height, x, y, maximized)
        """
        return self.settings.get("window", {})
    
    def set_window_geometry(self, width: int, height: int, 
                          x: Optional[int] = None, y: Optional[int] = None,
                          maximized: bool = False) -> None:
        """Save window geometry settings.
        
        Args:
            width: Window width in pixels
            height: Window height in pixels
            x: Window X position (None = centered)
            y: Window Y position (None = centered)
            maximized: Whether window is maximized
        """
        self.settings["window"] = {
            "width": width,
            "height": height,
            "x": x,
            "y": y,
            "maximized": maximized
        }
        self.save()
    
    def get_snap_to_grid(self) -> bool:
        """Get snap to grid setting.
        
        Returns:
            bool: Whether snap to grid is enabled
        """
        editor = self.settings.get("editor", {})
        return editor.get("snap_to_grid", True)  # Default True
    
    def set_snap_to_grid(self, enabled: bool) -> None:
        """Set snap to grid setting.
        
        Args:
            enabled: Whether to enable snap to grid
        """
        if "editor" not in self.settings:
            self.settings["editor"] = {}
        self.settings["editor"]["snap_to_grid"] = enabled
        self.save()
    
    def get_grid_spacing(self) -> float:
        """Get grid spacing setting.
        
        Returns:
            float: Grid spacing in pixels
        """
        editor = self.settings.get("editor", {})
        return editor.get("grid_spacing", 10.0)  # Default 10.0px
    
    def set_grid_spacing(self, spacing: float) -> None:
        """Set grid spacing setting.
        
        Args:
            spacing: Grid spacing in pixels
        """
        if "editor" not in self.settings:
            self.settings["editor"] = {}
        self.settings["editor"]["grid_spacing"] = spacing
        self.save()
