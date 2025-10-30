#!/usr/bin/env python3
"""Test Report Panel widget visibility.

Verifies that:
1. Report Panel creates all categories
2. Category widgets are visible
3. Content is realized/shown
"""
import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

# Add src to path
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.ui.panels.report.report_panel import ReportPanel


def check_widget_visibility(widget, indent=0):
    """Recursively check if widgets are visible."""
    prefix = "  " * indent
    widget_type = type(widget).__name__
    is_visible = widget.get_visible()
    is_realized = widget.get_realized()
    
    print(f"{prefix}{widget_type}: visible={is_visible}, realized={is_realized}")
    
    if hasattr(widget, 'get_children'):
        for child in widget.get_children():
            check_widget_visibility(child, indent + 1)


def main():
    """Test report panel visibility."""
    print("=" * 60)
    print("REPORT PANEL VISIBILITY TEST")
    print("=" * 60)
    
    # Create report panel
    print("\nCreating Report Panel...")
    report_panel = ReportPanel(project=None, model_canvas=None)
    
    # Check categories were created
    print(f"\n✓ Categories created: {len(report_panel.categories)}")
    for i, category in enumerate(report_panel.categories, 1):
        print(f"  {i}. {category.title}")
    
    # Check if panel is visible
    print(f"\n✓ Report Panel visible: {report_panel.get_visible()}")
    
    # Check category widgets
    print("\nCategory widgets:")
    for category in report_panel.categories:
        widget = category.get_widget()
        is_visible = widget.get_visible()
        is_realized = widget.get_realized()
        print(f"  • {category.title}")
        print(f"    Widget: {type(widget).__name__}")
        print(f"    Visible: {is_visible}")
        print(f"    Realized: {is_realized}")
        
        # Check if content exists
        if hasattr(category, 'category_frame'):
            content = category.category_frame.get_content()
            if content:
                print(f"    Content: {type(content).__name__}")
                print(f"    Content visible: {content.get_visible()}")
            else:
                print(f"    ⚠️ No content widget!")
    
    # Check widget tree
    print("\n" + "=" * 60)
    print("Widget Tree:")
    print("=" * 60)
    check_widget_visibility(report_panel)
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    
    # Test by creating a window and showing
    print("\nCreating test window to verify rendering...")
    window = Gtk.Window()
    window.set_default_size(400, 600)
    window.add(report_panel)
    window.show_all()
    
    print("✓ Window created and show_all() called")
    print("\nReport Panel should now be fully visible!")
    print("If you don't see categories, check if they're collapsed (click to expand)")
    
    # Run GTK main loop for 2 seconds then quit
    from gi.repository import GLib
    
    def quit_test():
        Gtk.main_quit()
        return False
    
    GLib.timeout_add(2000, quit_test)  # Quit after 2 seconds
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    
    print("\n✓ Test window closed")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
