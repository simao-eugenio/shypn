"""Palette button widget (GTK) - small wrapper used by MasterPalette.

This file contains a minimal PaletteButton class that wraps a Gtk.ToggleButton
with an icon and accessibility-friendly tooltip. It's intentionally small and
unit-testable.

CSS styling is applied via class names:
    - 'palette-button' for normal state
    - 'palette-button-active' added when toggled on
"""

from gi.repository import Gtk


class PaletteButton:
    """Simple toggle button used inside MasterPalette.

    API:
        PaletteButton(name, icon_name, tooltip)
        .widget -> Gtk.ToggleButton instance
        .set_active(bool)
        .get_active() -> bool
        .connect_toggled(callback)
        .set_sensitive(bool)
    """

    BUTTON_SIZE = 48
    ICON_SIZE = 40

    def __init__(self, name: str, icon_name: str, tooltip: str = ""):
        self.name = name
        self.icon_name = icon_name
        self.tooltip = tooltip

        self._button = Gtk.ToggleButton()
        self._button.set_name(f'palette_button_{name}')
        self._button.set_relief(Gtk.ReliefStyle.NONE)
        self._button.set_size_request(self.BUTTON_SIZE, self.BUTTON_SIZE)
        self._button.set_tooltip_text(tooltip)
        
        # Add CSS class for styling
        style_context = self._button.get_style_context()
        style_context.add_class('palette-button')

        # TEMPORARY: Use text labels instead of icons
        # Map button names to display text
        text_labels = {
            'files': 'Files',
            'pathways': 'Path',
            'analyses': 'Anal',
            'topology': 'Topo'
        }
        
        label_text = text_labels.get(name, name[:4].title())
        label = Gtk.Label(label=label_text)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_line_wrap(True)
        label.set_max_width_chars(5)
        self._button.add(label)

        # Connect to toggled to manage CSS classes
        self._button.connect('toggled', self._on_toggled_internal)
        self._button.show_all()

    def _on_toggled_internal(self, widget):
        """Internal handler to manage CSS classes on toggle."""
        style_context = widget.get_style_context()
        if widget.get_active():
            style_context.add_class('palette-button-active')
        else:
            style_context.remove_class('palette-button-active')

    @property
    def widget(self):
        return self._button

    def set_active(self, active: bool):
        """Set button active state (programmatically)."""
        self._button.set_active(active)

    def get_active(self) -> bool:
        """Get button active state."""
        return self._button.get_active()

    def set_sensitive(self, sensitive: bool):
        """Enable/disable button (e.g., for Topology placeholder)."""
        self._button.set_sensitive(sensitive)

    def connect_toggled(self, callback):
        """Connect to the toggled signal; callback gets (active: bool).
        
        Note: This connects AFTER the internal CSS management handler.
        """

        def _on_toggled(widget):
            callback(widget.get_active())

        self._button.connect('toggled', _on_toggled)


__all__ = ['PaletteButton']
