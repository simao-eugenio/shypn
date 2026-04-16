#!/usr/bin/env python3
"""Fix colors in currently loaded model to match color schema.

Run this in the Python REPL after loading a model to fix any incorrect colors.

Usage:
    >>> exec(open('dev/fix_model_colors.py').read())
    
Or from terminal:
    python -c "exec(open('dev/fix_model_colors.py').read())"
"""

def fix_current_model_colors():
    """Fix colors in the currently active model."""
    try:
        # Import required modules
        from shypn.utils.color_schema_manager import ColorSchemaManager
        
        # Get the main window and model canvas loader
        # This assumes the shypn GUI is already running
        import gi
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk
        
        # Find the ShypnWindow
        windows = Gtk.Window.list_toplevels()
        main_window = None
        for win in windows:
            if hasattr(win, 'model_canvas_loader'):
                main_window = win
                break
        
        if not main_window:
            print("❌ ERROR: Could not find ShypnWindow with model_canvas_loader")
            print("   Make sure the application is running and a model is loaded")
            return
        
        # Get current model
        loader = main_window.model_canvas_loader
        if not loader:
            print("❌ ERROR: No model canvas loader found")
            return
        
        canvas_manager = None
        if hasattr(loader, 'get_current_model'):
            canvas_manager = loader.get_current_model()
        elif hasattr(loader, 'canvas_managers'):
            drawing_area = loader.get_current_document()
            if drawing_area:
                canvas_manager = loader.canvas_managers.get(drawing_area)
        
        if not canvas_manager:
            print("❌ ERROR: No model is currently loaded")
            return
        
        # Get document name
        doc_name = "Unknown"
        if hasattr(canvas_manager, 'document') and canvas_manager.document:
            doc_name = getattr(canvas_manager.document, 'filename', 'Untitled')
        
        print(f"\n🔧 Fixing colors in model: {doc_name}")
        print("=" * 60)
        
        # Apply color fixes
        fixed_counts = ColorSchemaManager.fix_model_colors(canvas_manager)
        
        # Report results
        print(f"\n✅ Color fixes applied:")
        print(f"   • Places:      {fixed_counts['places']} fixed")
        print(f"   • Arcs:        {fixed_counts['arcs']} fixed")
        print(f"   • Transitions: {fixed_counts['transitions']} fixed")
        print(f"\n📝 Save the file to persist these changes")
        
        # Trigger redraw
        if hasattr(canvas_manager, 'drawing_area'):
            canvas_manager.drawing_area.queue_draw()
            print("🎨 Canvas redraw triggered")
        
        return fixed_counts
        
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return None


if __name__ == '__main__':
    # Run directly if executed as script
    fix_current_model_colors()
else:
    # If imported/exec'd, just run it
    print("Running color fix utility...")
    result = fix_current_model_colors()
    if result:
        print("\n✨ Done! Your model colors are now correct.")
        print("   Don't forget to save the file (Ctrl+S)")
