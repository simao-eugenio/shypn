#!/usr/bin/env python3
"""Tools Palette Loader - Minimal loader for ToolsPalette.

Now that ToolsPalette is pure Python/OOP, the loader simply instantiates it.
No UI file loading, no widget wiring - everything is handled by the palette itself.
"""

from shypn.edit.tools_palette_new import ToolsPalette


class ToolsPaletteLoader:
    """Minimal loader for tools palette.
    
    Responsibilities:
    - Instantiate ToolsPalette (that's it!)
    
    The palette handles its own:
    - Widget creation
    - Signal connection
    - CSS styling
    """
    
    def __init__(self):
        """Initialize the loader."""
        self.palette = None
    
    def load(self) -> ToolsPalette:
        """Create tools palette instance.
        
        Returns:
            ToolsPalette: Configured palette instance
        """
        self.palette = ToolsPalette()
        print(f"[ToolsPaletteLoader] Loaded tools palette")
        return self.palette
    
    def get_palette(self) -> ToolsPalette:
        """Get the palette instance.
        
        Returns:
            ToolsPalette: The palette instance or None
        """
        return self.palette


def create_tools_palette() -> ToolsPalette:
    """Convenience function to create and load tools palette.
    
    Returns:
        ToolsPalette: Loaded palette instance
    """
    loader = ToolsPaletteLoader()
    return loader.load()
