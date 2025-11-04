#!/usr/bin/env python3
"""
Manual BRENDA API Test Script

This script tests your BRENDA credentials with different query methods
to determine what level of access you have.

Usage:
    python test_brenda_manual.py

You'll see a GTK dialog to enter your BRENDA email and password.
"""

import sys
import os
import hashlib

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import GTK
try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
except ImportError:
    print("ERROR: GTK3 (PyGObject) not available")
    sys.exit(1)

try:
    from zeep import Client, Settings
    from zeep.exceptions import Fault
except ImportError:
    print("ERROR: zeep library not installed")
    print("Install with: pip install zeep")
    sys.exit(1)

BRENDA_WSDL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"


def get_credentials_dialog():
    """Show GTK dialog to get BRENDA credentials.
    
    Returns:
        tuple: (email, password) or (None, None) if cancelled
    """
    dialog = Gtk.Dialog(
        title="BRENDA Credentials",
        flags=Gtk.DialogFlags.MODAL
    )
    dialog.set_default_size(400, 200)
    dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
    dialog.add_button("Test Connection", Gtk.ResponseType.OK)
    dialog.set_default_response(Gtk.ResponseType.OK)
    
    # Create content area
    content = dialog.get_content_area()
    content.set_border_width(10)
    content.set_spacing(10)
    
    # Title label
    title_label = Gtk.Label()
    title_label.set_markup("<b>Enter your BRENDA credentials</b>")
    title_label.set_halign(Gtk.Align.START)
    content.pack_start(title_label, False, False, 0)
    
    # Info label
    info_label = Gtk.Label()
    info_label.set_text("This will test your BRENDA SOAP API access")
    info_label.set_halign(Gtk.Align.START)
    info_label.set_line_wrap(True)
    content.pack_start(info_label, False, False, 0)
    
    # Email field
    email_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    email_label = Gtk.Label(label="Email:")
    email_label.set_width_chars(10)
    email_label.set_halign(Gtk.Align.END)
    email_entry = Gtk.Entry()
    email_entry.set_placeholder_text("your-email@example.com")
    email_entry.set_activates_default(True)
    email_box.pack_start(email_label, False, False, 0)
    email_box.pack_start(email_entry, True, True, 0)
    content.pack_start(email_box, False, False, 0)
    
    # Password field
    password_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    password_label = Gtk.Label(label="Password:")
    password_label.set_width_chars(10)
    password_label.set_halign(Gtk.Align.END)
    password_entry = Gtk.Entry()
    password_entry.set_visibility(False)
    password_entry.set_placeholder_text("Enter password")
    password_entry.set_activates_default(True)
    password_box.pack_start(password_label, False, False, 0)
    password_box.pack_start(password_entry, True, True, 0)
    content.pack_start(password_box, False, False, 0)
    
    # Show password checkbox
    show_password_check = Gtk.CheckButton(label="Show password")
    show_password_check.connect("toggled", lambda cb: password_entry.set_visibility(cb.get_active()))
    show_password_check.set_margin_start(100)
    content.pack_start(show_password_check, False, False, 0)
    
    # Show all widgets
    dialog.show_all()
    
    # Run dialog
    response = dialog.run()
    
    if response == Gtk.ResponseType.OK:
        email = email_entry.get_text().strip()
        password = password_entry.get_text()
        dialog.destroy()
        return email, password
    else:
        dialog.destroy()
        return None, None


def test_brenda_access(email, password):
    """Test BRENDA API access with multiple methods."""
    
    print("=" * 70)
    print("BRENDA API Access Test")
    print("=" * 70)
    print(f"Testing credentials for: {email}\n")
    
    # Hash password
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    
    # Create SOAP client
    print("1. Creating SOAP client...")
    try:
        settings = Settings(strict=False, xml_huge_tree=True)
        client = Client(BRENDA_WSDL, settings=settings)
        print("   ✓ SOAP client created\n")
    except Exception as e:
        print(f"   ✗ Failed to create client: {e}\n")
        return False
    
    # Test 1: Lightweight handshake (getEcNumber)
    print("2. Testing handshake with getEcNumber() [LIGHTWEIGHT]")
    print("   EC: 2.7.1.1 (Hexokinase)")
    try:
        result = client.service.getEcNumber(
            email,
            password_hash,
            'ecNumber*2.7.1.1',
            'organism*',
            'transferredToEc*'
        )
        
        if result:
            print(f"   ✓ Handshake successful!")
            print(f"   Response type: {type(result)}")
            print(f"   Response length: {len(str(result))} chars")
            print(f"   Preview: {str(result)[:200]}...")
            print()
        else:
            print(f"   ⚠ Handshake returned None/empty")
            print(f"   Your account may have limited API access")
            print()
    except Fault as e:
        print(f"   ✗ SOAP Fault: {e}")
        print()
        return False
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        return False
    
    # Test 2: Km values query (getKmValue)
    print("3. Testing Km data query with getKmValue() [KINETIC DATA]")
    print("   EC: 2.7.1.1 (Hexokinase)")
    try:
        result = client.service.getKmValue(
            email,
            password_hash,
            'ecNumber*2.7.1.1#',
            '',  # organism (all)
            '',  # kmValue
            '',  # kmValueMaximum
            '',  # substrate
            '',  # commentary
            '',  # ligandStructureId
            ''   # literature
        )
        
        if result:
            print(f"   ✓ Km query successful!")
            print(f"   Response type: {type(result)}")
            print(f"   Response length: {len(str(result))} chars")
            print(f"   Preview: {str(result)[:500]}...")
            print()
            print("   ✅ YOUR ACCOUNT HAS FULL SOAP API ACCESS!")
            print("   ✅ You can retrieve kinetic data from BRENDA")
            print()
        else:
            print(f"   ✗ Km query returned None/empty")
            print()
            print("   ⚠ YOUR ACCOUNT HAS LIMITED API ACCESS")
            print("   ⚠ You can authenticate but cannot retrieve kinetic data")
            print()
    except Fault as e:
        print(f"   ✗ SOAP Fault: {e}")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
    
    # Test 3: Try another common enzyme
    print("4. Testing with another enzyme (Glucokinase EC 2.7.1.2)")
    try:
        result = client.service.getKmValue(
            email,
            password_hash,
            'ecNumber*2.7.1.2#',
            '',  # organism
            '',  # kmValue
            '',  # kmValueMaximum
            '',  # substrate
            '',  # commentary
            '',  # ligandStructureId
            ''   # literature
        )
        
        if result:
            print(f"   ✓ Query successful - returned data")
        else:
            print(f"   ✗ Query returned None/empty")
        print()
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("\nIf ALL queries returned None/empty:")
    print("  → Your account has LIMITED SOAP API access")
    print("  → You need to request full API access from BRENDA")
    print("  → Contact: info@brenda-enzymes.org")
    print("  → Website: https://www.brenda-enzymes.org/contact.php")
    print()
    print("If queries returned data:")
    print("  → Your account has FULL SOAP API access")
    print("  → Shypn should work correctly with your credentials")
    print()
    print("Alternative: Use BRENDA web interface")
    print("  → https://www.brenda-enzymes.org/")
    print("  → Search EC numbers manually")
    print("  → Copy/paste kinetic data into Shypn")
    print()
    
    return True


def main():
    """Main test function."""
    print("\n" + "=" * 70)
    print("BRENDA SOAP API Manual Test")
    print("=" * 70)
    print()
    print("Opening credentials dialog...")
    print()
    
    # Get credentials via GTK dialog
    email, password = get_credentials_dialog()
    
    if not email or not password:
        print("Cancelled or empty credentials provided.")
        return 1
    
    print(f"Testing credentials for: {email}")
    print()
    
    # Run tests
    success = test_brenda_access(email, password)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
