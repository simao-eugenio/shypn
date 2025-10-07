#!/usr/bin/env python3
"""Operations Palette Loader - Minimal loader for OperationsPalette.

Now that OperationsPalette is pure Python/OOP, the loader simply instantiates it.
No UI file loading, no widget wiring - everything is handled by the palette itself.
"""

from shypn.edit.operations_palette_new import OperationsPalette


class OperationsPaletteLoader:
    """Minimal loader for operations palette.
    
    Responsibilities:
    - Instantiate OperationsPalette (that's it!)
    
    The palette handles its own:
    - Widget creation
    - Signal connection
    - CSS styling
    """
    
    def __init__(self):
        """Initialize the loader."""
        self.palette = None
    
    def load(self) -> OperationsPalette:
        """Create operations palette instance.
        
        Returns:
            OperationsPalette: Configured palette instance
        """
        self.palette = OperationsPalette()
        print(f"[OperationsPaletteLoader] Loaded operations palette")
        return self.palette
    
    def get_palette(self) -> OperationsPalette:
        """Get the palette instance.
        
        Returns:
            OperationsPalette: The palette instance or None
        """
        return self.palette


def create_operations_palette() -> OperationsPalette:
    """Convenience function to create and load operations palette.
    
    Returns:
        OperationsPalette: Loaded palette instance
    """
    loader = OperationsPaletteLoader()
    return loader.load()
