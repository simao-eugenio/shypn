#!/usr/bin/env python3
"""UI components for scientific reporting.

This module provides GTK dialogs and widgets for document generation
and metadata management.
"""
from .metadata_dialog import MetadataDialog
from .profile_dialog import ProfileDialog

__all__ = [
    'MetadataDialog',
    'ProfileDialog',
]
