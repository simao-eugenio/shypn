#!/usr/bin/env python3
"""BRENDA Login Dialog.

Simple authentication dialog for BRENDA database credentials.
Users enter their BRENDA account email and password to enable
kinetic parameter fetching via SOAP API.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional, Tuple


class BRENDALoginDialog(Gtk.Dialog):
    """Dialog for BRENDA authentication.
    
    Collects user email and password for BRENDA SOAP API access.
    Credentials are validated by attempting authentication.
    """
    
    def __init__(self, parent=None):
        """Initialize BRENDA login dialog.
        
        Args:
            parent: Parent window for modal dialog
        """
        super().__init__(
            title="BRENDA Login",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        # Add buttons
        self.add_button("_Cancel", Gtk.ResponseType.CANCEL)
        login_button = self.add_button("_Login", Gtk.ResponseType.OK)
        login_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        
        # Set default button
        self.set_default_response(Gtk.ResponseType.OK)
        
        # Build UI
        self._build_ui()
        
        # Set size
        self.set_default_size(400, 250)
    
    def _build_ui(self):
        """Build dialog content."""
        content = self.get_content_area()
        content.set_spacing(12)
        content.set_border_width(12)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup(
            "<b>BRENDA Database Authentication</b>\n\n"
            "Enter your BRENDA credentials to fetch kinetic parameters.\n"
            "Register for free at: https://www.brenda-enzymes.org/"
        )
        info_label.set_line_wrap(True)
        info_label.set_xalign(0)
        content.pack_start(info_label, False, False, 0)
        
        # Credentials grid
        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(12)
        content.pack_start(grid, False, False, 0)
        
        # Email field
        email_label = Gtk.Label(label="Email:")
        email_label.set_xalign(1)
        grid.attach(email_label, 0, 0, 1, 1)
        
        self.email_entry = Gtk.Entry()
        self.email_entry.set_placeholder_text("your-email@example.com")
        self.email_entry.set_hexpand(True)
        self.email_entry.set_activates_default(True)
        grid.attach(self.email_entry, 1, 0, 1, 1)
        
        # Password field
        password_label = Gtk.Label(label="Password:")
        password_label.set_xalign(1)
        grid.attach(password_label, 0, 1, 1, 1)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)  # Hide password
        self.password_entry.set_placeholder_text("Your BRENDA password")
        self.password_entry.set_hexpand(True)
        self.password_entry.set_activates_default(True)
        grid.attach(self.password_entry, 1, 1, 1, 1)
        
        # Show password checkbox
        show_password_check = Gtk.CheckButton(label="Show password")
        show_password_check.connect('toggled', self._on_show_password_toggled)
        grid.attach(show_password_check, 1, 2, 1, 1)
        
        # Help text
        help_label = Gtk.Label()
        help_label.set_markup(
            "<small><i>Note: Credentials are used only for this session and not stored.</i></small>"
        )
        help_label.set_line_wrap(True)
        help_label.set_xalign(0)
        help_label.set_margin_top(12)
        content.pack_start(help_label, False, False, 0)
        
        # Show all widgets
        content.show_all()
    
    def _on_show_password_toggled(self, checkbox):
        """Toggle password visibility."""
        self.password_entry.set_visibility(checkbox.get_active())
    
    def get_credentials(self) -> Tuple[str, str]:
        """Get entered credentials.
        
        Returns:
            Tuple of (email, password)
        """
        email = self.email_entry.get_text().strip()
        password = self.password_entry.get_text()
        return email, password
    
    def show_error(self, message: str):
        """Show error message in dialog.
        
        Args:
            message: Error message to display
        """
        error_dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Authentication Failed"
        )
        error_dialog.format_secondary_text(message)
        error_dialog.run()
        error_dialog.destroy()


def show_brenda_login_dialog(parent=None) -> Optional[Tuple[str, str]]:
    """Show BRENDA login dialog and return credentials.
    
    Convenience function to show login dialog and get credentials.
    
    Args:
        parent: Parent window for modal dialog
    
    Returns:
        Tuple of (email, password) if user clicked Login, None if cancelled
    """
    dialog = BRENDALoginDialog(parent=parent)
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        credentials = dialog.get_credentials()
        dialog.destroy()
        return credentials
    else:
        dialog.destroy()
        return None


if __name__ == '__main__':
    """Test the BRENDA login dialog."""
    dialog = BRENDALoginDialog()
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        email, password = dialog.get_credentials()
        print(f"Email: {email}")
        print(f"Password: {'*' * len(password)}")
    else:
        print("Login cancelled")
    
    dialog.destroy()
