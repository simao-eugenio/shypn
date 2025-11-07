#!/usr/bin/env python3
"""
BRENDA Connection Test with GTK GUI

Simple GUI to test BRENDA credentials safely.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import json
import os
import hashlib
import threading

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
        """Load credentials from workspace/.brenda_credentials.json"""
        creds_path = os.path.join(os.path.dirname(__file__), '..', 'workspace', '.brenda_credentials.json')
        
        if os.path.exists(creds_path):
            try:
                with open(creds_path, 'r') as f:
                    creds = json.load(f)
                
                self.email_entry.set_text(creds.get('email', ''))
                self.password_entry.set_text(creds.get('password', ''))
                
                self.append_result("✅ Credentials loaded from file\n", "success")
            except Exception as e:
                self.append_result(f"⚠️  Could not load credentials: {e}\n", "warning")
        else:
            self.append_result(f"ℹ️  No credentials file found at:\n   {creds_path}\n", "info")
    
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
        """Run BRENDA test in background thread."""
        try:
            GLib.idle_add(self.append_result, f"🔬 Testing BRENDA connection...\n", None)
            GLib.idle_add(self.append_result, f"📧 Email: {email}\n\n", None)
            
            # Hash password
            GLib.idle_add(self.append_result, "🔐 Hashing password...\n", None)
            password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            
            # Connect to BRENDA
            GLib.idle_add(self.append_result, "🌐 Connecting to BRENDA SOAP service...\n", None)
            WSDL = 'https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl'
            client = Client(WSDL)
            
            # Test with getEcNumber
            GLib.idle_add(self.append_result, "🔍 Testing API access with getEcNumber()...\n", None)
            GLib.idle_add(self.append_result, "   Querying EC 2.7.1.1 (Hexokinase)...\n\n", None)
            
            # BRENDA SOAP API requires specific format with all parameters
            # Based on: https://www.brenda-enzymes.org/soap.php
            result = client.service.getEcNumber(
                email,                      # User email
                password_hash,              # Hashed password (SHA256)
                "ecNumber*2.7.1.1",        # EC number filter
                "organism*",                # Organism filter (empty but required)
                "transferredToEc*"          # Additional required field
            )
            
            # Success!
            GLib.idle_add(self.append_result, "═" * 60 + "\n", None)
            GLib.idle_add(self.append_result, "✅ SUCCESS! BRENDA connection working!\n", "success")
            GLib.idle_add(self.append_result, "═" * 60 + "\n\n", None)
            
            GLib.idle_add(self.append_result, "📊 Sample result:\n", None)
            
            # Convert result to string (might be list, dict, or string)
            result_str = str(result)
            result_preview = result_str[:500] if len(result_str) > 500 else result_str
            GLib.idle_add(self.append_result, result_preview + "\n\n", "info")
            
            if len(result_str) > 500:
                GLib.idle_add(self.append_result, f"... (truncated, total length: {len(result_str)} chars)\n\n", "info")
            
            GLib.idle_add(self.append_result, "✅ Your BRENDA credentials are working correctly!\n", "success")
            GLib.idle_add(self.append_result, "✅ You can now use BRENDA enrichment in shypn\n\n", "success")
            
        except Exception as e:
            GLib.idle_add(self.append_result, "═" * 60 + "\n", None)
            GLib.idle_add(self.append_result, "❌ FAILED!\n", "error")
            GLib.idle_add(self.append_result, "═" * 60 + "\n\n", None)
            
            error_msg = str(e)
            GLib.idle_add(self.append_result, f"Error: {error_msg}\n\n", "error")
            
            # Check for common BRENDA error messages
            if "credentials" in error_msg.lower() or "authentication" in error_msg.lower() or "login" in error_msg.lower():
                GLib.idle_add(self.append_result, "🔐 Authentication Failed\n\n", "error")
                GLib.idle_add(self.append_result, "This error indicates incorrect credentials.\n\n", None)
                GLib.idle_add(self.append_result, "Please check:\n", None)
                GLib.idle_add(self.append_result, "  ✓ Email address is correct\n", None)
                GLib.idle_add(self.append_result, "  ✓ Password is correct (case-sensitive)\n", None)
                GLib.idle_add(self.append_result, "  ✓ Account has been activated by BRENDA admins\n\n", None)
                GLib.idle_add(self.append_result, "Reset password: https://www.brenda-enzymes.org/remember.php\n", "info")
            else:
                GLib.idle_add(self.append_result, "Possible issues:\n", None)
                GLib.idle_add(self.append_result, "  • Incorrect email or password\n", None)
                GLib.idle_add(self.append_result, "  • Account not yet activated (takes 1-2 days)\n", None)
                GLib.idle_add(self.append_result, "  • Network connection problems\n", None)
                GLib.idle_add(self.append_result, "  • BRENDA service temporarily unavailable\n\n", None)
        
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
