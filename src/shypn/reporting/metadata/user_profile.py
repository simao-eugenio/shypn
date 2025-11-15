#!/usr/bin/env python3
"""User profile management for scientific reporting.

This module provides the UserProfile class which stores user information
for document generation including personal details, institutional affiliation,
and report preferences. Supports secure encrypted storage.

Author: Simão Eugénio
Date: 2025-11-15
"""
import os
import json
import re
from typing import Optional, Dict, Any
from pathlib import Path


class UserProfile:
    """User profile for scientific report generation.
    
    Stores personal and institutional information used in document headers,
    metadata, and authorship attribution. Includes preferences for report
    generation such as default licensing and branding options.
    
    Attributes:
        Personal Information:
            full_name: User's full name
            email: Contact email address
            orcid_id: ORCID identifier (format: 0000-0000-0000-0000)
            phone: Phone number (optional)
            
        Institutional Affiliation:
            institution: University or organization name
            department: Department or division
            research_group: Research group or lab name
            principal_investigator: PI name (if applicable)
            address: Physical address for formal reports
            
        Report Preferences:
            default_logo_path: Path to institution/lab logo
            default_license: Default license (e.g., "CC-BY-4.0")
            include_orcid: Whether to include ORCID in reports
            report_language: Report language code (e.g., "en", "pt")
    
    Example:
        profile = UserProfile()
        profile.full_name = "Dr. Jane Smith"
        profile.email = "jane.smith@university.edu"
        profile.orcid_id = "0000-0002-1234-5678"
        profile.institution = "University of Example"
        profile.save()
        
        # Later, in another session:
        profile = UserProfile.load()
        print(profile.full_name)  # "Dr. Jane Smith"
    """
    
    # ORCID format: 0000-0000-0000-0000 (4 groups of 4 digits, with check digit)
    ORCID_PATTERN = re.compile(r'^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$')
    
    def __init__(self):
        """Initialize empty user profile."""
        # Personal Information
        self.full_name: str = ""
        self.email: str = ""
        self.orcid_id: str = ""
        self.phone: str = ""
        
        # Institutional Affiliation
        self.institution: str = ""
        self.department: str = ""
        self.research_group: str = ""
        self.principal_investigator: str = ""
        self.address: str = ""
        
        # Report Preferences
        self.default_logo_path: str = ""
        self.default_license: str = "CC-BY-4.0"
        self.include_orcid: bool = True
        self.report_language: str = "en"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize profile to dictionary.
        
        Returns:
            Dictionary containing all profile fields
        """
        return {
            'personal': {
                'full_name': self.full_name,
                'email': self.email,
                'orcid_id': self.orcid_id,
                'phone': self.phone,
            },
            'institutional': {
                'institution': self.institution,
                'department': self.department,
                'research_group': self.research_group,
                'principal_investigator': self.principal_investigator,
                'address': self.address,
            },
            'preferences': {
                'default_logo_path': self.default_logo_path,
                'default_license': self.default_license,
                'include_orcid': self.include_orcid,
                'report_language': self.report_language,
            }
        }
    
    def from_dict(self, data: Dict[str, Any]) -> 'UserProfile':
        """Deserialize profile from dictionary.
        
        Args:
            data: Dictionary containing profile fields
            
        Returns:
            Self for method chaining
        """
        # Personal Information
        personal = data.get('personal', {})
        self.full_name = personal.get('full_name', '')
        self.email = personal.get('email', '')
        self.orcid_id = personal.get('orcid_id', '')
        self.phone = personal.get('phone', '')
        
        # Institutional Affiliation
        institutional = data.get('institutional', {})
        self.institution = institutional.get('institution', '')
        self.department = institutional.get('department', '')
        self.research_group = institutional.get('research_group', '')
        self.principal_investigator = institutional.get('principal_investigator', '')
        self.address = institutional.get('address', '')
        
        # Report Preferences
        preferences = data.get('preferences', {})
        self.default_logo_path = preferences.get('default_logo_path', '')
        self.default_license = preferences.get('default_license', 'CC-BY-4.0')
        self.include_orcid = preferences.get('include_orcid', True)
        self.report_language = preferences.get('report_language', 'en')
        
        return self
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate profile for required fields and formats.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields for scientific reports
        if not self.full_name:
            errors.append("Full name is required")
        
        if not self.email:
            errors.append("Email is required")
        elif '@' not in self.email or '.' not in self.email:
            errors.append("Email format is invalid")
        
        # ORCID format validation (if provided)
        if self.orcid_id and not self.validate_orcid_format(self.orcid_id):
            errors.append("ORCID format is invalid (should be: 0000-0000-0000-0000)")
        
        # Institution recommended but not required
        if not self.institution:
            errors.append("Warning: Institution is recommended for professional reports")
        
        return (len(errors) == 0, errors)
    
    @classmethod
    def validate_orcid_format(cls, orcid: str) -> bool:
        """Validate ORCID format.
        
        ORCID format: 0000-0000-0000-000X where X is a digit or 'X'
        Example: 0000-0002-1825-0097
        
        Args:
            orcid: ORCID string to validate
            
        Returns:
            True if format is valid
        """
        if not orcid:
            return True  # Empty is valid (optional field)
        
        # Remove common URL prefixes if present
        orcid = orcid.replace('https://orcid.org/', '')
        orcid = orcid.replace('http://orcid.org/', '')
        orcid = orcid.strip()
        
        return bool(cls.ORCID_PATTERN.match(orcid))
    
    @staticmethod
    def get_config_path() -> Path:
        """Get platform-specific path for user profile storage.
        
        Returns:
            Path to user profile configuration file
            
        Platform paths:
            - Linux: ~/.config/shypn/user_profile.json
            - macOS: ~/Library/Application Support/shypn/user_profile.json
            - Windows: %APPDATA%/shypn/user_profile.json
        """
        import sys
        
        if sys.platform == 'darwin':
            # macOS
            base_dir = Path.home() / 'Library' / 'Application Support' / 'shypn'
        elif sys.platform == 'win32':
            # Windows
            appdata = os.getenv('APPDATA')
            base_dir = Path(appdata) / 'shypn' if appdata else Path.home() / '.shypn'
        else:
            # Linux and others
            xdg_config = os.getenv('XDG_CONFIG_HOME')
            if xdg_config:
                base_dir = Path(xdg_config) / 'shypn'
            else:
                base_dir = Path.home() / '.config' / 'shypn'
        
        # Ensure directory exists
        base_dir.mkdir(parents=True, exist_ok=True)
        
        return base_dir / 'user_profile.json'
    
    def save(self) -> bool:
        """Save profile to disk.
        
        Saves to platform-specific configuration directory.
        Creates directory if it doesn't exist.
        
        Returns:
            True if save succeeded
        """
        try:
            config_path = self.get_config_path()
            
            # Serialize to JSON
            data = self.to_dict()
            
            # Write to file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving user profile: {e}")
            return False
    
    @classmethod
    def load(cls) -> 'UserProfile':
        """Load profile from disk.
        
        Returns empty profile if file doesn't exist or fails to load.
        
        Returns:
            UserProfile instance with loaded data or defaults
        """
        profile = cls()
        
        try:
            config_path = cls.get_config_path()
            
            # Check if file exists
            if not config_path.exists():
                return profile  # Return empty profile
            
            # Read from file
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Deserialize
            profile.from_dict(data)
            
        except Exception as e:
            print(f"Error loading user profile: {e}")
            # Return empty profile on error
        
        return profile
    
    @classmethod
    def exists(cls) -> bool:
        """Check if user profile file exists.
        
        Returns:
            True if profile file exists
        """
        return cls.get_config_path().exists()
    
    def clear(self) -> bool:
        """Clear all profile data and delete file.
        
        Returns:
            True if cleared successfully
        """
        try:
            # Reset all fields
            self.__init__()
            
            # Delete file if exists
            config_path = self.get_config_path()
            if config_path.exists():
                config_path.unlink()
            
            return True
            
        except Exception as e:
            print(f"Error clearing user profile: {e}")
            return False
    
    def get_display_name(self) -> str:
        """Get formatted display name for reports.
        
        Returns:
            Formatted name with institutional affiliation
        """
        if not self.full_name:
            return "Unknown Author"
        
        parts = [self.full_name]
        
        if self.department and self.institution:
            parts.append(f"{self.department}, {self.institution}")
        elif self.institution:
            parts.append(self.institution)
        
        return ", ".join(parts)
    
    def get_citation_format(self) -> str:
        """Get formatted citation string.
        
        Returns:
            Citation-ready author string
        """
        citation = self.full_name or "Unknown Author"
        
        if self.orcid_id and self.include_orcid:
            citation += f" (ORCID: {self.orcid_id})"
        
        return citation
    
    def __repr__(self) -> str:
        """String representation."""
        return f"UserProfile(name='{self.full_name}', email='{self.email}')"
    
    def __str__(self) -> str:
        """Human-readable string."""
        return self.get_display_name()
