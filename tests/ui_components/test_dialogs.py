#!/usr/bin/env python3
"""Test script for UI dialogs.

Visual/interactive test for MetadataDialog and ProfileDialog.
Run this to test the dialogs in a real GTK environment.

Usage:
    PYTHONPATH=src python3 test_dialogs.py
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.reporting import ModelMetadata, UserProfile, MetadataDialog, ProfileDialog


class TestWindow(Gtk.Window):
    """Test window with buttons to launch dialogs."""
    
    def __init__(self):
        super().__init__(title="Dialog Test Suite")
        self.set_default_size(400, 200)
        self.set_border_width(20)
        
        # Create test metadata and profile
        self.test_metadata = self._create_test_metadata()
        self.test_profile = self._create_test_profile()
        
        # Build UI
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.add(vbox)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<big><b>Reporting UI Dialogs Test</b></big>")
        vbox.pack_start(title, False, False, 0)
        
        # Info
        info = Gtk.Label()
        info.set_markup("<i>Click buttons to test dialogs</i>")
        vbox.pack_start(info, False, False, 0)
        
        vbox.pack_start(Gtk.Separator(), False, False, 12)
        
        # Metadata Dialog Button
        metadata_btn = Gtk.Button(label="Test MetadataDialog")
        metadata_btn.connect("clicked", self.on_test_metadata)
        vbox.pack_start(metadata_btn, False, False, 0)
        
        # Metadata Dialog (Empty) Button
        metadata_empty_btn = Gtk.Button(label="Test MetadataDialog (Empty)")
        metadata_empty_btn.connect("clicked", self.on_test_metadata_empty)
        vbox.pack_start(metadata_empty_btn, False, False, 0)
        
        # Profile Dialog Button
        profile_btn = Gtk.Button(label="Test ProfileDialog")
        profile_btn.connect("clicked", self.on_test_profile)
        vbox.pack_start(profile_btn, False, False, 0)
        
        # Profile Dialog (Empty) Button
        profile_empty_btn = Gtk.Button(label="Test ProfileDialog (Empty)")
        profile_empty_btn.connect("clicked", self.on_test_profile_empty)
        vbox.pack_start(profile_empty_btn, False, False, 0)
        
        # Results area
        vbox.pack_start(Gtk.Separator(), False, False, 12)
        
        self.result_label = Gtk.Label()
        self.result_label.set_line_wrap(True)
        self.result_label.set_text("No tests run yet")
        vbox.pack_start(self.result_label, True, True, 0)
        
        # Connect close
        self.connect("destroy", Gtk.main_quit)
    
    def _create_test_metadata(self) -> ModelMetadata:
        """Create sample metadata for testing."""
        metadata = ModelMetadata()
        metadata.model_name = "Test Glycolysis Model"
        metadata.model_id = "TEST_GLYC_001"
        metadata.version = "1.2.0"
        metadata.description = "Comprehensive model of glycolysis pathway for testing metadata dialog functionality."
        metadata.keywords = ["glycolysis", "metabolism", "test"]
        
        metadata.primary_author = "Dr. Jane Test"
        metadata.contributors = ["Dr. John Contributor", "Dr. Alice Helper"]
        metadata.institution = "Test University"
        metadata.department = "Systems Biology"
        metadata.contact_email = "jane.test@testuniv.edu"
        
        metadata.organism = "Saccharomyces cerevisiae"
        metadata.biological_system = "Central Carbon Metabolism"
        metadata.pathway_name = "Glycolysis"
        metadata.cell_type = "Yeast cell"
        
        metadata.import_source = "SBML"
        metadata.original_model_id = "BIOMD0000000001"
        metadata.add_modification("created", "Initial model creation")
        metadata.add_modification("validated", "Model structure validated")
        
        metadata.publications = ["10.1093/bioinformatics/btv123", "PMID:12345678"]
        metadata.related_models = ["MODEL001", "MODEL002"]
        metadata.external_resources = ["https://www.kegg.jp/pathway/sce00010"]
        
        return metadata
    
    def _create_test_profile(self) -> UserProfile:
        """Create sample profile for testing."""
        profile = UserProfile()
        profile.full_name = "Dr. Test User"
        profile.email = "test.user@example.edu"
        profile.orcid_id = "0000-0002-1234-5678"
        profile.phone = "+1-555-TEST"
        
        profile.institution = "Test Research Institute"
        profile.department = "Computational Biology"
        profile.research_group = "Systems Modeling Lab"
        profile.principal_investigator = "Prof. Big Boss"
        profile.address = "123 Test Street\nTest City, TC 12345\nTestland"
        
        profile.default_logo_path = "/path/to/logo.png"
        profile.default_license = "CC-BY-4.0"
        profile.include_orcid = True
        profile.report_language = "en"
        
        return profile
    
    def on_test_metadata(self, button):
        """Test MetadataDialog with sample data."""
        dialog = MetadataDialog(self, self.test_metadata)
        result = dialog.get_metadata()
        dialog.destroy()
        
        if result:
            self.result_label.set_markup(
                f"<b>MetadataDialog Result:</b>\n"
                f"Model: {result.model_name}\n"
                f"ID: {result.model_id}\n"
                f"Keywords: {', '.join(result.keywords)}\n"
                f"Author: {result.primary_author}\n"
                f"Organism: {result.organism}"
            )
        else:
            self.result_label.set_text("MetadataDialog: Cancelled")
    
    def on_test_metadata_empty(self, button):
        """Test MetadataDialog with empty data."""
        dialog = MetadataDialog(self, None)
        result = dialog.get_metadata()
        dialog.destroy()
        
        if result:
            self.result_label.set_markup(
                f"<b>MetadataDialog Result (Empty Start):</b>\n"
                f"Model: {result.model_name or '(empty)'}\n"
                f"ID: {result.model_id or '(empty)'}\n"
                f"Keywords: {', '.join(result.keywords) or '(none)'}\n"
                f"Author: {result.primary_author or '(empty)'}"
            )
        else:
            self.result_label.set_text("MetadataDialog (Empty): Cancelled")
    
    def on_test_profile(self, button):
        """Test ProfileDialog with sample data."""
        dialog = ProfileDialog(self, self.test_profile)
        result = dialog.get_profile()
        dialog.destroy()
        
        if result:
            self.result_label.set_markup(
                f"<b>ProfileDialog Result:</b>\n"
                f"Name: {result.full_name}\n"
                f"Email: {result.email}\n"
                f"ORCID: {result.orcid_id}\n"
                f"Institution: {result.institution}\n"
                f"License: {result.default_license}"
            )
        else:
            self.result_label.set_text("ProfileDialog: Cancelled")
    
    def on_test_profile_empty(self, button):
        """Test ProfileDialog with empty data."""
        # Create empty profile
        empty_profile = UserProfile()
        dialog = ProfileDialog(self, empty_profile)
        result = dialog.get_profile()
        dialog.destroy()
        
        if result:
            self.result_label.set_markup(
                f"<b>ProfileDialog Result (Empty Start):</b>\n"
                f"Name: {result.full_name or '(empty)'}\n"
                f"Email: {result.email or '(empty)'}\n"
                f"ORCID: {result.orcid_id or '(empty)'}\n"
                f"Institution: {result.institution or '(empty)'}"
            )
        else:
            self.result_label.set_text("ProfileDialog (Empty): Cancelled")


def main():
    """Run test application."""
    print("=" * 60)
    print("REPORTING UI DIALOGS TEST")
    print("=" * 60)
    print("\nLaunching test window...")
    print("Click buttons to test each dialog.\n")
    
    window = TestWindow()
    window.show_all()
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    
    print("\nTest complete.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
