#!/usr/bin/env python3
"""
BRENDA Connection Test with GTK GUI

Simple GUI to test BRENDA credentials safely.
Uses the BRENDAAPIClient class for proper authentication and data retrieval.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import json
import os
import sys
import threading
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / 'src'
sys.path.insert(0, str(src_path))

from shypn.data.brenda_soap_client import BRENDAAPIClient

try:
    from zeep import Client
    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False


class BrendaTestWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="BRENDA Connection Test")
        self.set_default_size(600, 500)
        self.set_border_width(10)
        
        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)
        
        # Title
        title = Gtk.Label()
        title.set_markup('<b><big>BRENDA SOAP API Connection Test</big></b>')
        vbox.pack_start(title, False, False, 0)
        
        # Info label
        info = Gtk.Label()
        info.set_text("Test your BRENDA credentials and verify API access")
        info.set_line_wrap(True)
        vbox.pack_start(info, False, False, 0)
        
        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Credentials section
        creds_frame = Gtk.Frame(label="Credentials")
        creds_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        creds_box.set_margin_start(10)
        creds_box.set_margin_end(10)
        creds_box.set_margin_top(10)
        creds_box.set_margin_bottom(10)
        creds_frame.add(creds_box)
        vbox.pack_start(creds_frame, False, False, 0)
        
        # Email field
        email_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        email_label = Gtk.Label(label="Email:")
        email_label.set_width_chars(12)
        email_label.set_xalign(0)
        email_box.pack_start(email_label, False, False, 0)
        
        self.email_entry = Gtk.Entry()
        self.email_entry.set_placeholder_text("your-email@example.com")
        email_box.pack_start(self.email_entry, True, True, 0)
        creds_box.pack_start(email_box, False, False, 0)
        
        # Password field
        pass_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pass_label = Gtk.Label(label="Password:")
        pass_label.set_width_chars(12)
        pass_label.set_xalign(0)
        pass_box.pack_start(pass_label, False, False, 0)
        
        self.password_entry = Gtk.Entry()
        self.password_entry.set_visibility(False)
        self.password_entry.set_placeholder_text("Enter your BRENDA password")
        pass_box.pack_start(self.password_entry, True, True, 0)
        creds_box.pack_start(pass_box, False, False, 0)
        
        # Load credentials button
        load_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        load_btn = Gtk.Button(label="Load from workspace/.brenda_credentials.json")
        load_btn.connect("clicked", self.on_load_credentials)
        load_btn_box.pack_start(load_btn, True, False, 0)
        
        # Save credentials button
        save_btn = Gtk.Button(label="💾 Save Credentials")
        save_btn.connect("clicked", self.on_save_credentials)
        load_btn_box.pack_start(save_btn, False, False, 0)
        
        creds_box.pack_start(load_btn_box, False, False, 5)
        
        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Help section
        help_frame = Gtk.Frame(label="Help & Resources")
        help_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        help_box.set_margin_start(10)
        help_box.set_margin_end(10)
        help_box.set_margin_top(5)
        help_box.set_margin_bottom(5)
        help_frame.add(help_box)
        
        help_label = Gtk.Label()
        help_label.set_markup(
            '<small>'
            '• Registration: <a href="https://www.brenda-enzymes.org/register.php">brenda-enzymes.org/register.php</a>\n'
            '• Reset Password: <a href="https://www.brenda-enzymes.org/remember.php">brenda-enzymes.org/remember.php</a>\n'
            '• SOAP API Docs: <a href="https://www.brenda-enzymes.org/soap.php">brenda-enzymes.org/soap.php</a>\n'
            '• Account activation takes 1-2 business days'
            '</small>'
        )
        help_label.set_line_wrap(True)
        help_label.set_xalign(0)
        help_box.pack_start(help_label, False, False, 0)
        
        vbox.pack_start(help_frame, False, False, 0)
        
        # Separator
        vbox.pack_start(Gtk.Separator(), False, False, 5)
        
        # Test button
        self.test_button = Gtk.Button(label="🔬 Test BRENDA Connection")
        self.test_button.connect("clicked", self.on_test_clicked)
        vbox.pack_start(self.test_button, False, False, 0)
        
        # Result area
        result_frame = Gtk.Frame(label="Test Results")
        result_scroll = Gtk.ScrolledWindow()
        result_scroll.set_size_request(-1, 200)
        result_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        result_frame.add(result_scroll)
        vbox.pack_start(result_frame, True, True, 0)
        
        self.result_buffer = Gtk.TextBuffer()
        self.result_view = Gtk.TextView(buffer=self.result_buffer)
        self.result_view.set_editable(False)
        self.result_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.result_view.set_margin_start(10)
        self.result_view.set_margin_end(10)
        self.result_view.set_margin_top(10)
        self.result_view.set_margin_bottom(10)
        result_scroll.add(self.result_view)
        
        # Setup text tags for colored output
        self.setup_tags()
        
        # Try to load credentials on startup
        self.load_credentials_from_file()
    
    def on_load_credentials(self, button):
        """Load credentials from file."""
        self.load_credentials_from_file()
    
    def on_save_credentials(self, button):
        """Save credentials to file."""
        email = self.email_entry.get_text().strip()
        password = self.password_entry.get_text()
        
        if not email or not password:
            self.append_result("❌ Please enter both email and password before saving\n\n", "error")
            return
        
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'workspace', '.brenda_credentials.json')
        
        try:
            # Create workspace directory if it doesn't exist
            os.makedirs(os.path.dirname(creds_path), exist_ok=True)
            
            # Save credentials
            with open(creds_path, 'w') as f:
                json.dump({
                    'email': email,
                    'password': password
                }, f, indent=2)
            
            self.append_result(f"✅ Credentials saved to:\n   {creds_path}\n\n", "success")
        except Exception as e:
            self.append_result(f"❌ Failed to save credentials: {e}\n\n", "error")
    
    def load_credentials_from_file(self):
        """Load credentials from workspace/.brenda_credentials.json or ~/.shypn/brenda_credentials.json"""
        # Try workspace first
        workspace_path = os.path.join(os.path.dirname(__file__), '..', 'workspace', '.brenda_credentials.json')
        # Try home directory second
        home_path = Path.home() / '.shypn' / 'brenda_credentials.json'
        
        creds_path = None
        if os.path.exists(workspace_path):
            creds_path = workspace_path
        elif home_path.exists():
            creds_path = str(home_path)
        
        if creds_path:
            try:
                with open(creds_path, 'r') as f:
                    creds = json.load(f)
                
                self.email_entry.set_text(creds.get('email', ''))
                self.password_entry.set_text(creds.get('password', ''))
                
                self.append_result(f"✅ Credentials loaded from:\n   {creds_path}\n", "success")
            except Exception as e:
                self.append_result(f"⚠️  Could not load credentials: {e}\n", "warning")
        else:
            self.append_result(f"ℹ️  No credentials file found\n", "info")
            self.append_result(f"   Checked:\n", "info")
            self.append_result(f"   • {workspace_path}\n", "info")
            self.append_result(f"   • {home_path}\n", "info")
    
    def append_result(self, text, tag=None):
        """Append text to result buffer."""
        end_iter = self.result_buffer.get_end_iter()
        if tag:
            self.result_buffer.insert_with_tags_by_name(end_iter, text, tag)
        else:
            self.result_buffer.insert(end_iter, text)
        
        # Scroll to end
        mark = self.result_buffer.get_insert()
        self.result_view.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
    
    def on_test_clicked(self, button):
        """Test BRENDA connection."""
        email = self.email_entry.get_text().strip()
        password = self.password_entry.get_text()
        
        if not email or not password:
            self.append_result("❌ Please enter both email and password\n\n", "error")
            return
        
        if not ZEEP_AVAILABLE:
            self.append_result("❌ zeep library not installed\n", "error")
            self.append_result("   Install with: pip install zeep\n\n", "info")
            return
        
        # Clear previous results
        self.result_buffer.set_text("")
        
        # Disable button during test
        self.test_button.set_sensitive(False)
        self.test_button.set_label("⏳ Testing...")
        
        # Run test in thread to avoid blocking GUI
        thread = threading.Thread(target=self.run_test, args=(email, password))
        thread.daemon = True
        thread.start()
    
    def run_test(self, email, password):
        """Run BRENDA test in background thread using BRENDAAPIClient."""
        try:
            GLib.idle_add(self.append_result, f"🔬 Testing BRENDA connection...\n", None)
            GLib.idle_add(self.append_result, f"📧 Email: {email}\n\n", None)
            
            # Create API client
            GLib.idle_add(self.append_result, "� Initializing BRENDA API client...\n", None)
            client = BRENDAAPIClient()
            
            # Step 1: Test authentication
            GLib.idle_add(self.append_result, "🔐 Testing authentication...\n", None)
            GLib.idle_add(self.append_result, "   (Using SHA256 password hashing as per BRENDA spec)\n", None)
            
            success = client.authenticate(email=email, password=password)
            
            if not success:
                raise Exception("Authentication failed - check credentials and account status")
            
            GLib.idle_add(self.append_result, "✅ Authentication successful!\n\n", "success")
            
            # Step 2: Test data retrieval - Km values
            GLib.idle_add(self.append_result, "� Testing data retrieval (Km values)...\n", None)
            GLib.idle_add(self.append_result, "   Querying EC 2.7.1.1 (Hexokinase) in Homo sapiens...\n", None)
            
            km_values = client.get_km_values(ec_number="2.7.1.1", organism="Homo sapiens")
            
            if km_values:
                GLib.idle_add(self.append_result, f"✅ Retrieved {len(km_values)} Km values!\n\n", "success")
                
                # Show sample data
                GLib.idle_add(self.append_result, "📋 Sample Km values:\n", None)
                for i, km in enumerate(km_values[:3], 1):
                    substrate = km.get('substrate', 'N/A')
                    value = km.get('kmValue', 'N/A')
                    organism = km.get('organism', 'N/A')
                    GLib.idle_add(self.append_result, f"   {i}. {substrate}: {value} ({organism})\n", "info")
                
                if len(km_values) > 3:
                    GLib.idle_add(self.append_result, f"   ... and {len(km_values) - 3} more\n", "info")
                
                GLib.idle_add(self.append_result, "\n", None)
            else:
                GLib.idle_add(self.append_result, "⚠️  No Km values returned\n", "warning")
                GLib.idle_add(self.append_result, "   (This may indicate limited API access)\n\n", "warning")
            
            # Step 3: Test kcat values
            GLib.idle_add(self.append_result, "📊 Testing kcat value retrieval...\n", None)
            
            kcat_values = client.get_kcat_values(ec_number="2.7.1.1", organism="Homo sapiens")
            
            if kcat_values:
                GLib.idle_add(self.append_result, f"✅ Retrieved {len(kcat_values)} kcat values!\n\n", "success")
            else:
                GLib.idle_add(self.append_result, "ℹ️  No kcat values available for this query\n\n", "info")
            
            # Success summary
            GLib.idle_add(self.append_result, "═" * 60 + "\n", None)
            GLib.idle_add(self.append_result, "✅ ALL TESTS PASSED!\n", "success")
            GLib.idle_add(self.append_result, "═" * 60 + "\n\n", None)
            
            GLib.idle_add(self.append_result, "✅ Your BRENDA credentials are working correctly!\n", "success")
            GLib.idle_add(self.append_result, "✅ You can now use BRENDA enrichment in shypn\n\n", "success")
            
            GLib.idle_add(self.append_result, "💡 Next steps:\n", None)
            GLib.idle_add(self.append_result, "   1. Use BRENDA category in Pathway Operations panel\n", None)
            GLib.idle_add(self.append_result, "   2. Enter EC numbers to query kinetic parameters\n", None)
            GLib.idle_add(self.append_result, "   3. Select parameters to add to your model\n\n", None)
            
        except Exception as e:
            GLib.idle_add(self.append_result, "═" * 60 + "\n", None)
            GLib.idle_add(self.append_result, "❌ TEST FAILED!\n", "error")
            GLib.idle_add(self.append_result, "═" * 60 + "\n\n", None)
            
            error_msg = str(e)
            GLib.idle_add(self.append_result, f"Error: {error_msg}\n\n", "error")
            
            # Provide specific troubleshooting
            if "403" in error_msg or "Forbidden" in error_msg:
                GLib.idle_add(self.append_result, "🚫 403 Forbidden Error\n\n", "error")
                GLib.idle_add(self.append_result, "BRENDA server rejected the connection.\n\n", None)
                GLib.idle_add(self.append_result, "Possible causes:\n", None)
                GLib.idle_add(self.append_result, "  • BRENDA temporarily blocking automated access\n", None)
                GLib.idle_add(self.append_result, "  • Rate limiting - wait a few minutes and retry\n", None)
                GLib.idle_add(self.append_result, "  • Check service status: https://www.brenda-enzymes.org/\n\n", None)
            elif "credentials" in error_msg.lower() or "authentication" in error_msg.lower():
                GLib.idle_add(self.append_result, "🔐 Authentication Failed\n\n", "error")
                GLib.idle_add(self.append_result, "Please verify:\n", None)
                GLib.idle_add(self.append_result, "  ✓ Email address is correct\n", None)
                GLib.idle_add(self.append_result, "  ✓ Password is correct (case-sensitive)\n", None)
                GLib.idle_add(self.append_result, "  ✓ Account activated by BRENDA (takes 1-2 days)\n\n", None)
                GLib.idle_add(self.append_result, "🔗 Reset password: https://www.brenda-enzymes.org/remember.php\n", "info")
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                GLib.idle_add(self.append_result, "🌐 Network Connection Issue\n\n", "error")
                GLib.idle_add(self.append_result, "Please check:\n", None)
                GLib.idle_add(self.append_result, "  • Internet connection is working\n", None)
                GLib.idle_add(self.append_result, "  • Firewall allows HTTPS to brenda-enzymes.org\n", None)
                GLib.idle_add(self.append_result, "  • Not behind a corporate proxy\n\n", None)
            else:
                GLib.idle_add(self.append_result, "💡 Troubleshooting:\n", None)
                GLib.idle_add(self.append_result, "  • Verify credentials at brenda-enzymes.org\n", None)
                GLib.idle_add(self.append_result, "  • Account must be activated (1-2 business days)\n", None)
                GLib.idle_add(self.append_result, "  • Free accounts may have limited SOAP access\n", None)
                GLib.idle_add(self.append_result, "  • Contact: info@brenda-enzymes.org\n\n", None)
        
        finally:
            # Re-enable button
            GLib.idle_add(self.test_button.set_sensitive, True)
            GLib.idle_add(self.test_button.set_label, "🔬 Test BRENDA Connection")
    
    def setup_tags(self):
        """Setup text tags for colored output."""
        tag_table = self.result_buffer.get_tag_table()
        
        success_tag = Gtk.TextTag(name="success")
        success_tag.set_property("foreground", "#00AA00")
        success_tag.set_property("weight", 700)  # Bold
        tag_table.add(success_tag)
        
        error_tag = Gtk.TextTag(name="error")
        error_tag.set_property("foreground", "#CC0000")
        error_tag.set_property("weight", 700)
        tag_table.add(error_tag)
        
        warning_tag = Gtk.TextTag(name="warning")
        warning_tag.set_property("foreground", "#FF8800")
        tag_table.add(warning_tag)
        
        info_tag = Gtk.TextTag(name="info")
        info_tag.set_property("foreground", "#0066CC")
        tag_table.add(info_tag)


def main():
    window = BrendaTestWindow()
    window.connect("destroy", Gtk.main_quit)
    window.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
