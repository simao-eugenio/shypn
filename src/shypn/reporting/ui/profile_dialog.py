#!/usr/bin/env python3
"""User profile management dialog.

This dialog manages user profile information for scientific reports.
Simple form-based editing with validation.

Author: Simão Eugénio
Date: 2025-11-15
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Optional

from ..metadata import UserProfile


class ProfileDialog(Gtk.Dialog):
    """Dialog for managing user profile.
    
    Allows editing personal information, institutional affiliation,
    and report preferences. Validates ORCID format and email.
    """
    
    def __init__(self, parent: Optional[Gtk.Window], profile: Optional[UserProfile] = None):
        """Initialize profile dialog.
        
        Args:
            parent: Parent window for modal behavior
            profile: Existing profile to edit, or None for new
        """
        super().__init__(
            title="User Profile",
            transient_for=parent,
            modal=True,
            destroy_with_parent=True
        )
        
        # Load existing profile or create new
        self.profile = profile if profile else UserProfile.load()
        
        # Dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Save", Gtk.ResponseType.OK)
        
        # Set dialog size
        self.set_default_size(500, 550)
        
        # Build UI
        self._build_ui()
        
        # Populate fields
        self._populate_fields()
        
        self.show_all()
    
    def _build_ui(self):
        """Build dialog UI."""
        content = self.get_content_area()
        content.set_border_width(12)
        
        # Create scrolled window for form
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        content.pack_start(scroll, True, True, 0)
        
        # Main form container
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        form.set_border_width(6)
        scroll.add(form)
        
        # Personal Information Section
        self._add_section_header(form, "Personal Information")
        self.fullname_entry = self._add_entry_row(form, "Full Name:", "*Required")
        self.email_entry = self._add_entry_row(form, "Email:", "*Required")
        self.orcid_entry = self._add_entry_row(form, "ORCID:", "0000-0000-0000-0000")
        self.phone_entry = self._add_entry_row(form, "Phone:", "Optional")
        
        # Institutional Affiliation Section
        self._add_section_header(form, "Institutional Affiliation")
        self.institution_entry = self._add_entry_row(form, "Institution:", "University/Organization")
        self.department_entry = self._add_entry_row(form, "Department:", "Department/Division")
        self.research_group_entry = self._add_entry_row(form, "Research Group:", "Lab/Group name")
        self.pi_entry = self._add_entry_row(form, "Principal Investigator:", "Optional")
        
        # Address (multiline)
        addr_label = Gtk.Label(label="Address:", xalign=0)
        addr_label.get_style_context().add_class("dim-label")
        form.pack_start(addr_label, False, False, 0)
        
        addr_scroll = Gtk.ScrolledWindow()
        addr_scroll.set_min_content_height(60)
        addr_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        self.address_buffer = Gtk.TextBuffer()
        address_view = Gtk.TextView(buffer=self.address_buffer)
        address_view.set_wrap_mode(Gtk.WrapMode.WORD)
        addr_scroll.add(address_view)
        form.pack_start(addr_scroll, False, False, 0)
        
        # Report Preferences Section
        self._add_section_header(form, "Report Preferences")
        self.logo_entry = self._add_entry_row(form, "Default Logo Path:", "Path to institution logo")
        
        # License selection
        license_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        license_label = Gtk.Label(label="Default License:", xalign=0)
        license_label.set_size_request(150, -1)
        license_box.pack_start(license_label, False, False, 0)
        
        self.license_combo = Gtk.ComboBoxText()
        licenses = ["CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0", "MIT", "GPL-3.0", "Apache-2.0", "Proprietary"]
        for lic in licenses:
            self.license_combo.append_text(lic)
        self.license_combo.set_active(0)
        license_box.pack_start(self.license_combo, True, True, 0)
        form.pack_start(license_box, False, False, 0)
        
        # Include ORCID checkbox
        self.include_orcid_check = Gtk.CheckButton(label="Include ORCID in reports")
        self.include_orcid_check.set_active(True)
        form.pack_start(self.include_orcid_check, False, False, 0)
        
        # Language selection
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        lang_label = Gtk.Label(label="Report Language:", xalign=0)
        lang_label.set_size_request(150, -1)
        lang_box.pack_start(lang_label, False, False, 0)
        
        self.language_combo = Gtk.ComboBoxText()
        languages = [("en", "English"), ("pt", "Portuguese"), ("es", "Spanish"), ("fr", "French"), ("de", "German")]
        for code, name in languages:
            self.language_combo.append(code, name)
        self.language_combo.set_active_id("en")
        lang_box.pack_start(self.language_combo, True, True, 0)
        form.pack_start(lang_box, False, False, 0)
    
    def _add_section_header(self, parent: Gtk.Box, text: str):
        """Add section header with separator.
        
        Args:
            parent: Parent container
            text: Header text
        """
        header = Gtk.Label(label=f"<b>{text}</b>", xalign=0)
        header.set_use_markup(True)
        header.set_margin_top(12)
        parent.pack_start(header, False, False, 0)
        
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        parent.pack_start(separator, False, False, 0)
    
    def _add_entry_row(self, parent: Gtk.Box, label_text: str, placeholder: str) -> Gtk.Entry:
        """Helper to add label + entry row.
        
        Args:
            parent: Parent container
            label_text: Label text
            placeholder: Entry placeholder
            
        Returns:
            Created entry widget
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        label = Gtk.Label(label=label_text, xalign=0)
        label.set_size_request(150, -1)
        box.pack_start(label, False, False, 0)
        
        entry = Gtk.Entry()
        entry.set_placeholder_text(placeholder)
        box.pack_start(entry, True, True, 0)
        
        parent.pack_start(box, False, False, 0)
        return entry
    
    def _populate_fields(self):
        """Populate fields from profile."""
        # Personal Information
        self.fullname_entry.set_text(self.profile.full_name or "")
        self.email_entry.set_text(self.profile.email or "")
        self.orcid_entry.set_text(self.profile.orcid_id or "")
        self.phone_entry.set_text(self.profile.phone or "")
        
        # Institutional Affiliation
        self.institution_entry.set_text(self.profile.institution or "")
        self.department_entry.set_text(self.profile.department or "")
        self.research_group_entry.set_text(self.profile.research_group or "")
        self.pi_entry.set_text(self.profile.principal_investigator or "")
        self.address_buffer.set_text(self.profile.address or "")
        
        # Report Preferences
        self.logo_entry.set_text(self.profile.default_logo_path or "")
        
        # Set license combo
        license_idx = 0
        for i, lic in enumerate(["CC-BY-4.0", "CC-BY-SA-4.0", "CC-BY-NC-4.0", "MIT", "GPL-3.0", "Apache-2.0", "Proprietary"]):
            if lic == self.profile.default_license:
                license_idx = i
                break
        self.license_combo.set_active(license_idx)
        
        self.include_orcid_check.set_active(self.profile.include_orcid)
        self.language_combo.set_active_id(self.profile.report_language)
    
    def _collect_fields(self) -> bool:
        """Collect field values back to profile.
        
        Returns:
            True if validation passed
        """
        # Personal Information
        self.profile.full_name = self.fullname_entry.get_text().strip()
        self.profile.email = self.email_entry.get_text().strip()
        self.profile.orcid_id = self.orcid_entry.get_text().strip()
        self.profile.phone = self.phone_entry.get_text().strip()
        
        # Institutional Affiliation
        self.profile.institution = self.institution_entry.get_text().strip()
        self.profile.department = self.department_entry.get_text().strip()
        self.profile.research_group = self.research_group_entry.get_text().strip()
        self.profile.principal_investigator = self.pi_entry.get_text().strip()
        
        start, end = self.address_buffer.get_bounds()
        self.profile.address = self.address_buffer.get_text(start, end, True).strip()
        
        # Report Preferences
        self.profile.default_logo_path = self.logo_entry.get_text().strip()
        self.profile.default_license = self.license_combo.get_active_text() or "CC-BY-4.0"
        self.profile.include_orcid = self.include_orcid_check.get_active()
        self.profile.report_language = self.language_combo.get_active_id() or "en"
        
        # Validate
        is_valid, errors = self.profile.validate()
        if not is_valid:
            # Filter out warnings (those starting with "Warning:")
            critical_errors = [e for e in errors if not e.startswith("Warning:")]
            if critical_errors:
                error_text = "\n".join(critical_errors)
                self._show_error_dialog("Validation Error", error_text)
                return False
        
        return True
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog.
        
        Args:
            title: Dialog title
            message: Error message
        """
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def get_profile(self) -> Optional[UserProfile]:
        """Get edited profile after dialog closes.
        
        Returns:
            Updated profile if OK was clicked, None if cancelled
        """
        response = self.run()
        self.hide()
        
        if response == Gtk.ResponseType.OK:
            if self._collect_fields():
                # Save to disk
                if self.profile.save():
                    return self.profile
                else:
                    self._show_error_dialog("Save Error", "Failed to save profile to disk")
        
        return None
