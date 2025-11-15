#!/usr/bin/env python3
"""Scientific reporting and document generation.

This module provides comprehensive document generation capabilities
for scientific reports including PDF, Excel, and HTML exports with
professional formatting and metadata management.
"""
from .metadata import ModelMetadata, UserProfile, MetadataStorage
from .ui import MetadataDialog, ProfileDialog

__all__ = [
    'ModelMetadata',
    'UserProfile',
    'MetadataStorage',
    'MetadataDialog',
    'ProfileDialog',
]
