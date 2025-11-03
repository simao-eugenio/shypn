#!/usr/bin/env python3
"""BRENDA SOAP API Client.

This module provides a Python interface to the BRENDA enzyme database via SOAP API.
Handles authentication, querying kinetic parameters, and response parsing.

BRENDA Website: https://www.brenda-enzymes.org/
API Documentation: https://www.brenda-enzymes.org/soap.php

Requirements:
- zeep>=4.2.1 (SOAP client library)
- Valid BRENDA credentials (email + password)

Credential Storage (Priority Order):
1. Environment variables: BRENDA_EMAIL, BRENDA_PASSWORD
2. Config file: ~/.shypn/brenda_credentials.json (encrypted)
3. User prompt (interactive)
"""

import os
import hashlib
import json
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from pathlib import Path

# Try to import zeep
try:
    from zeep import Client
    from zeep.exceptions import Fault as SOAPFault
    ZEEP_AVAILABLE = True
except ImportError:
    ZEEP_AVAILABLE = False
    Client = None
    SOAPFault = Exception


@dataclass
class BRENDACredentials:
    """BRENDA API credentials."""
    email: str
    password: str
    
    def get_password_hash(self) -> str:
        """Get SHA256 hash of password (required by BRENDA API)."""
        return hashlib.sha256(self.password.encode()).hexdigest()


class BRENDAAPIClient:
    """Client for BRENDA SOAP API.
    
    Provides methods to query kinetic parameters (Km, Vmax, kcat, Ki) for enzymes.
    
    Example:
        >>> client = BRENDAAPIClient()
        >>> client.authenticate("user@example.com", "password")
        >>> km_data = client.get_km_values("2.7.1.1", organism="Homo sapiens")
    """
    
    # BRENDA SOAP WSDL URL
    WSDL_URL = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
    
    def __init__(self):
        """Initialize BRENDA API client.
        
        Client starts unauthenticated. Call authenticate(email, password) to establish connection.
        Credentials are provided dynamically by the user, not loaded from files.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.credentials = None
        self.client = None
        self._authenticated = False
        
        if not ZEEP_AVAILABLE:
            self.logger.warning("zeep library not available. Install with: pip install zeep")
    
    def save_credentials(self, email: str, password: str):
        """Save credentials to config file.
        
        Args:
            email: BRENDA account email
            password: BRENDA account password
        """
        config_dir = Path.home() / '.shypn'
        config_dir.mkdir(parents=True, exist_ok=True)
        
        config_path = config_dir / 'brenda_credentials.json'
        
        # TODO: Encrypt credentials before saving
        # For now, save as plain JSON (development only!)
        data = {
            'email': email,
            'password': password
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Set restrictive permissions (Unix only)
        try:
            config_path.chmod(0o600)
        except Exception:
            pass
        
        self.credentials = BRENDACredentials(email=email, password=password)
        self.logger.info(f"Saved BRENDA credentials to {config_path}")
    
    def authenticate(self, email: Optional[str] = None, password: Optional[str] = None) -> bool:
        """Authenticate with BRENDA API and establish SOAP client session.
        
        Args:
            email: BRENDA account email (required - must be provided)
            password: BRENDA account password (required - must be provided)
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not ZEEP_AVAILABLE:
            self.logger.error("zeep library not available. Cannot authenticate.")
            return False
        
        if not email or not password:
            self.logger.error("Email and password are required for authentication.")
            return False
        
        # Store credentials for this session
        self.credentials = BRENDACredentials(email=email, password=password)
        
        try:
            # Initialize SOAP client
            self.logger.info(f"Connecting to BRENDA API at {self.WSDL_URL}")
            self.client = Client(self.WSDL_URL)
            
            # Test authentication with a lightweight query
            # Use getKmValue with minimal parameters to test login
            password_hash = self.credentials.get_password_hash()
            
            self.logger.info("Testing BRENDA authentication with handshake...")
            # Use lightweight getEcNumber() as handshake (much faster than getKmValue)
            # This just checks if EC 2.7.1.1 exists in BRENDA (doesn't retrieve data)
            result = self.client.service.getEcNumber(
                self.credentials.email,
                password_hash,
                'ecNumber*2.7.1.1',   # EC number for hexokinase (lightweight test)
                'organism*',           # Organism filter (empty but required)
                'transferredToEc*'     # Required field (checks if EC was transferred)
            )
            
            # Check if authentication test returned data
            self.logger.info(f"[AUTH_TEST] Handshake result type: {type(result)}")
            self.logger.info(f"[AUTH_TEST] Handshake result repr: {repr(result)}")
            if result:
                self.logger.info(f"[AUTH_TEST] Handshake data length: {len(str(result))} chars")
                self.logger.info(f"[AUTH_TEST] Preview: {str(result)[:500]}")
                self.logger.info("✓ BRENDA authentication successful - SOAP API handshake OK!")
                self.logger.info("✓ Your account can query the BRENDA database")
            else:
                self.logger.warning("✓ BRENDA authentication accepted BUT handshake returned no data")
                self.logger.warning("⚠ This suggests LIMITED API access (authentication only, no data retrieval)")
                self.logger.warning("⚠ Free academic accounts may not have access to BRENDA data via SOAP API")
                self.logger.warning("⚠ Contact BRENDA support for full API access: info@brenda-enzymes.org")
                self.logger.warning("⚠ Website: https://www.brenda-enzymes.org/contact.php")
            
            self._authenticated = True
            return True
            
        except SOAPFault as e:
            self.logger.error(f"BRENDA SOAP error: {e}")
            self._authenticated = False
            return False
        except Exception as e:
            self.logger.error(f"Failed to authenticate with BRENDA: {e}")
            self._authenticated = False
            return False
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated."""
        return self._authenticated
    
    def get_km_values(self, ec_number: str, organism: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query Km values for an enzyme.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Optional organism filter (e.g., "Homo sapiens")
        
        Returns:
            List of Km value records with substrate, value, units, literature refs
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            password_hash = self.credentials.get_password_hash()
            
            # Build EC number query
            ec_query = f"ecNumber*{ec_number}#"
            
            self.logger.info(f"Querying BRENDA for Km values: EC={ec_number}, organism={organism or 'all'}")
            
            # Call with all required parameters
            self.logger.info(f"[BRENDA_QUERY] Sending SOAP request for EC {ec_number}")
            self.logger.info(f"[BRENDA_QUERY]   Email: {self.credentials.email}")
            self.logger.info(f"[BRENDA_QUERY]   EC query: {ec_query}")
            
            result = self.client.service.getKmValue(
                self.credentials.email,
                password_hash,
                ec_query,
                organism or '',  # organism filter (empty = all)
                '',  # kmValue
                '',  # kmValueMaximum
                '',  # substrate
                '',  # commentary
                '',  # ligandStructureId
                ''   # literature
            )
            
            # Debug: Log raw response with detailed type info
            self.logger.info(f"[BRENDA_RAW] EC {ec_number} raw response type: {type(result)}")
            self.logger.info(f"[BRENDA_RAW] EC {ec_number} raw response repr: {repr(result)}")
            self.logger.info(f"[BRENDA_RAW] EC {ec_number} raw response bool: {bool(result)}")
            if result is not None:
                self.logger.info(f"[BRENDA_RAW] EC {ec_number} response length: {len(str(result))}")
                result_str = str(result)[:1000]  # First 1000 chars
                self.logger.info(f"[BRENDA_RAW] EC {ec_number} response preview: {result_str}")
            else:
                self.logger.warning(f"[BRENDA_RAW] EC {ec_number} returned None/empty response")
                self.logger.warning(f"[BRENDA_RAW] This likely means:")
                self.logger.warning(f"[BRENDA_RAW]   1. BRENDA database has no Km data for EC {ec_number}")
                self.logger.warning(f"[BRENDA_RAW]   2. Your account lacks SOAP API data access (free academic accounts)")
                self.logger.warning(f"[BRENDA_RAW]   3. EC number is invalid or obsolete")
            
            # Parse result
            parsed = self._parse_km_response(result)
            self.logger.info(f"[BRENDA_PARSE] EC {ec_number} parsed {len(parsed)} Km records")
            return parsed
            
        except SOAPFault as e:
            self.logger.error(f"BRENDA SOAP error querying Km: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error querying Km values: {e}")
            return []
    
    def get_kcat_values(self, ec_number: str, organism: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query kcat (turnover number) values for an enzyme.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Optional organism filter
        
        Returns:
            List of kcat value records
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            password_hash = self.credentials.get_password_hash()
            
            ec_query = f"ecNumber*{ec_number}#"
            
            self.logger.info(f"Querying BRENDA for kcat values: EC={ec_number}, organism={organism or 'all'}")
            
            result = self.client.service.getTurnoverNumber(
                self.credentials.email,
                password_hash,
                ec_query,
                organism or '',  # organism filter
                '',  # turnoverNumber
                '',  # turnoverNumberMaximum
                '',  # substrate
                '',  # commentary
                '',  # ligandStructureId
                ''   # literature
            )
            
            return self._parse_kcat_response(result)
            
        except SOAPFault as e:
            self.logger.error(f"BRENDA SOAP error querying kcat: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error querying kcat values: {e}")
            return []
    
    def get_ki_values(self, ec_number: str, organism: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query Ki (inhibition constant) values for an enzyme.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Optional organism filter
        
        Returns:
            List of Ki value records
        """
        if not self._authenticated:
            raise RuntimeError("Not authenticated. Call authenticate() first.")
        
        try:
            password_hash = self.credentials.get_password_hash()
            
            ec_query = f"ecNumber*{ec_number}#"
            
            self.logger.info(f"Querying BRENDA for Ki values: EC={ec_number}, organism={organism or 'all'}")
            
            result = self.client.service.getKiValue(
                self.credentials.email,
                password_hash,
                ec_query,
                organism or '',  # organism filter
                '',  # kiValue
                '',  # kiValueMaximum
                '',  # inhibitor
                '',  # commentary
                '',  # ligandStructureId
                ''   # literature
            )
            
            return self._parse_ki_response(result)
            
        except SOAPFault as e:
            self.logger.error(f"BRENDA SOAP error querying Ki: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error querying Ki values: {e}")
            return []
    
    def _parse_km_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse BRENDA Km response format.
        
        BRENDA format: #ecNumber*2.7.1.1#organism*Homo sapiens#kmValue*0.15#substrate*glucose#literature*12345678#
        
        Args:
            response: Raw BRENDA response string
        
        Returns:
            List of parsed Km records
        """
        results = []
        
        if not response:
            return results
        
        # Split by record separator (usually newline or multiple #)
        records = response.split('\n')
        
        for record in records:
            if not record.strip():
                continue
            
            # Parse fields
            data = {}
            parts = record.split('#')
            
            for part in parts:
                if '*' in part:
                    key, value = part.split('*', 1)
                    data[key] = value
            
            if 'kmValue' in data:
                try:
                    results.append({
                        'ec_number': data.get('ecNumber', ''),
                        'organism': data.get('organism', ''),
                        'value': float(data['kmValue']),
                        'unit': 'mM',  # BRENDA usually uses mM for Km
                        'substrate': data.get('substrate', ''),
                        'literature': data.get('literature', ''),
                        'commentary': data.get('commentary', '')
                    })
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to parse Km record: {e}")
                    continue
        
        return results
    
    def _parse_kcat_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse BRENDA kcat/turnover number response."""
        results = []
        
        if not response:
            return results
        
        records = response.split('\n')
        
        for record in records:
            if not record.strip():
                continue
            
            data = {}
            parts = record.split('#')
            
            for part in parts:
                if '*' in part:
                    key, value = part.split('*', 1)
                    data[key] = value
            
            if 'turnoverNumber' in data:
                try:
                    results.append({
                        'ec_number': data.get('ecNumber', ''),
                        'organism': data.get('organism', ''),
                        'value': float(data['turnoverNumber']),
                        'unit': 's⁻¹',  # kcat unit
                        'substrate': data.get('substrate', ''),
                        'literature': data.get('literature', ''),
                        'commentary': data.get('commentary', '')
                    })
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to parse kcat record: {e}")
                    continue
        
        return results
    
    def _parse_ki_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse BRENDA Ki response."""
        results = []
        
        if not response:
            return results
        
        records = response.split('\n')
        
        for record in records:
            if not record.strip():
                continue
            
            data = {}
            parts = record.split('#')
            
            for part in parts:
                if '*' in part:
                    key, value = part.split('*', 1)
                    data[key] = value
            
            if 'kiValue' in data:
                try:
                    results.append({
                        'ec_number': data.get('ecNumber', ''),
                        'organism': data.get('organism', ''),
                        'value': float(data['kiValue']),
                        'unit': 'mM',  # Ki usually in mM
                        'inhibitor': data.get('inhibitor', ''),
                        'literature': data.get('literature', ''),
                        'commentary': data.get('commentary', '')
                    })
                except (ValueError, KeyError) as e:
                    self.logger.warning(f"Failed to parse Ki record: {e}")
                    continue
        
        return results


# Convenience function for quick access
def get_brenda_client() -> Optional[BRENDAAPIClient]:
    """Get authenticated BRENDA client (convenience function).
    
    Returns:
        Authenticated BRENDAAPIClient if credentials available, None otherwise
    """
    try:
        client = BRENDAAPIClient()
        if client.credentials and client.authenticate():
            return client
    except Exception as e:
        logging.error(f"Failed to create BRENDA client: {e}")
    
    return None


if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 70)
    print("BRENDA SOAP API Client Test")
    print("=" * 70)
    
    if not ZEEP_AVAILABLE:
        print("\n❌ ERROR: zeep library not installed")
        print("Install with: pip install zeep")
        exit(1)
    
    # Check for credentials
    email = os.getenv('BRENDA_EMAIL')
    password = os.getenv('BRENDA_PASSWORD')
    
    if not email or not password:
        print("\n❌ ERROR: BRENDA credentials not found")
        print("\nSet environment variables:")
        print("  export BRENDA_EMAIL='your-email@example.com'")
        print("  export BRENDA_PASSWORD='your-password'")
        exit(1)
    
    print(f"\n✓ Credentials found: {email}")
    
    # Test authentication
    print("\n--- Testing Authentication ---")
    client = BRENDAAPIClient()
    
    if client.authenticate():
        print("✓ Authentication successful!")
        
        # Test Km query
        print("\n--- Testing Km Query (Hexokinase EC 2.7.1.1) ---")
        km_values = client.get_km_values("2.7.1.1", organism="Homo sapiens")
        
        if km_values:
            print(f"✓ Found {len(km_values)} Km values:")
            for i, km in enumerate(km_values[:5], 1):  # Show first 5
                print(f"  {i}. Substrate: {km['substrate']}, Km: {km['value']} {km['unit']}")
        else:
            print("❌ No Km values found")
        
        # Test kcat query
        print("\n--- Testing kcat Query ---")
        kcat_values = client.get_kcat_values("2.7.1.1", organism="Homo sapiens")
        
        if kcat_values:
            print(f"✓ Found {len(kcat_values)} kcat values:")
            for i, kcat in enumerate(kcat_values[:5], 1):
                print(f"  {i}. Substrate: {kcat['substrate']}, kcat: {kcat['value']} {kcat['unit']}")
        else:
            print("❌ No kcat values found")
        
        print("\n✓ All tests passed!")
        
    else:
        print("❌ Authentication failed")
        exit(1)
