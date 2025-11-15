#!/usr/bin/env python3
"""Model metadata container for scientific reporting.

This module provides the ModelMetadata class which stores comprehensive
information about Petri net models including authorship, biological context,
provenance, and references.

Author: Simão Eugénio
Date: 2025-11-15
"""
from datetime import datetime
from typing import List, Dict, Optional, Any


class ModelMetadata:
    """Container for comprehensive model metadata.
    
    Stores all metadata associated with a Petri net model including
    basic information, authorship, biological context, provenance,
    and references. Designed for serialization to .shypn files.
    
    Attributes:
        Basic Information:
            model_name: Human-readable model name
            model_id: Unique identifier
            version: Model version string
            description: Detailed model description
            keywords: List of searchable keywords/tags
            
        Authorship:
            primary_author: Name of primary author
            contributors: List of contributor names
            institution: Institution/university name
            department: Department or research group
            contact_email: Contact email address
            
        Biological Context:
            organism: Species/organism name
            biological_system: System being modeled (e.g., "Glycolysis")
            pathway_name: Pathway name if applicable
            cell_type: Cell type or tissue
            
        Provenance:
            import_source: Source of model ("SBML", "KEGG", "Manual")
            original_model_id: External model ID if imported
            import_date: Date/time of import
            modification_history: List of modification records
            
        References:
            publications: List of DOI/PubMed references
            related_models: List of related model IDs
            external_resources: List of external resource URLs
    
    Example:
        metadata = ModelMetadata()
        metadata.model_name = "E. coli Glycolysis"
        metadata.organism = "Escherichia coli"
        metadata.import_source = "SBML"
        metadata.add_publication("10.1093/bioinformatics/btv123")
    """
    
    def __init__(self):
        """Initialize empty model metadata."""
        # Basic Information
        self.model_name: str = ""
        self.model_id: str = ""
        self.version: str = "1.0"
        self.description: str = ""
        self.keywords: List[str] = []
        
        # Authorship
        self.primary_author: str = ""
        self.contributors: List[str] = []
        self.institution: str = ""
        self.department: str = ""
        self.contact_email: str = ""
        
        # Biological Context
        self.organism: str = ""
        self.biological_system: str = ""
        self.pathway_name: str = ""
        self.cell_type: str = ""
        
        # Provenance
        self.import_source: str = ""  # "SBML", "KEGG", "Manual"
        self.original_model_id: str = ""
        self.import_date: Optional[datetime] = None
        self.modification_history: List[Dict[str, Any]] = []
        
        # References
        self.publications: List[str] = []  # DOIs or PubMed IDs
        self.related_models: List[str] = []
        self.external_resources: List[str] = []
        
        # System metadata (auto-generated)
        self.created_date: Optional[datetime] = datetime.now()
        self.last_modified: Optional[datetime] = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize metadata to dictionary for storage.
        
        Converts all metadata fields to a dictionary suitable for JSON
        serialization. Datetime objects are converted to ISO format strings.
        
        Returns:
            Dictionary containing all metadata fields
        """
        return {
            'basic': {
                'model_name': self.model_name,
                'model_id': self.model_id,
                'version': self.version,
                'description': self.description,
                'keywords': self.keywords,
            },
            'authorship': {
                'primary_author': self.primary_author,
                'contributors': self.contributors,
                'institution': self.institution,
                'department': self.department,
                'contact_email': self.contact_email,
            },
            'biological_context': {
                'organism': self.organism,
                'biological_system': self.biological_system,
                'pathway_name': self.pathway_name,
                'cell_type': self.cell_type,
            },
            'provenance': {
                'import_source': self.import_source,
                'original_model_id': self.original_model_id,
                'import_date': self.import_date.isoformat() if self.import_date else None,
                'modification_history': self.modification_history,
            },
            'references': {
                'publications': self.publications,
                'related_models': self.related_models,
                'external_resources': self.external_resources,
            },
            'system': {
                'created_date': self.created_date.isoformat() if self.created_date else None,
                'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            }
        }
    
    def from_dict(self, data: Dict[str, Any]) -> 'ModelMetadata':
        """Deserialize metadata from dictionary.
        
        Loads metadata from a dictionary (typically loaded from JSON).
        Handles missing fields gracefully with defaults.
        
        Args:
            data: Dictionary containing metadata fields
            
        Returns:
            Self for method chaining
        """
        # Basic Information
        basic = data.get('basic', {})
        self.model_name = basic.get('model_name', '')
        self.model_id = basic.get('model_id', '')
        self.version = basic.get('version', '1.0')
        self.description = basic.get('description', '')
        self.keywords = basic.get('keywords', [])
        
        # Authorship
        authorship = data.get('authorship', {})
        self.primary_author = authorship.get('primary_author', '')
        self.contributors = authorship.get('contributors', [])
        self.institution = authorship.get('institution', '')
        self.department = authorship.get('department', '')
        self.contact_email = authorship.get('contact_email', '')
        
        # Biological Context
        bio = data.get('biological_context', {})
        self.organism = bio.get('organism', '')
        self.biological_system = bio.get('biological_system', '')
        self.pathway_name = bio.get('pathway_name', '')
        self.cell_type = bio.get('cell_type', '')
        
        # Provenance
        prov = data.get('provenance', {})
        self.import_source = prov.get('import_source', '')
        self.original_model_id = prov.get('original_model_id', '')
        import_date_str = prov.get('import_date')
        self.import_date = datetime.fromisoformat(import_date_str) if import_date_str else None
        self.modification_history = prov.get('modification_history', [])
        
        # References
        refs = data.get('references', {})
        self.publications = refs.get('publications', [])
        self.related_models = refs.get('related_models', [])
        self.external_resources = refs.get('external_resources', [])
        
        # System
        system = data.get('system', {})
        created_str = system.get('created_date')
        self.created_date = datetime.fromisoformat(created_str) if created_str else None
        modified_str = system.get('last_modified')
        self.last_modified = datetime.fromisoformat(modified_str) if modified_str else None
        
        return self
    
    def validate(self) -> tuple[bool, List[str]]:
        """Validate metadata for completeness.
        
        Checks that required fields are populated and formats are valid.
        Returns validation status and list of error messages.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Required fields
        if not self.model_name:
            errors.append("Model name is required")
        
        if not self.model_id:
            errors.append("Model ID is required")
        
        # Email format validation (basic)
        if self.contact_email and '@' not in self.contact_email:
            errors.append("Contact email format is invalid")
        
        return (len(errors) == 0, errors)
    
    def add_modification(self, action: str, description: str, user: str = ""):
        """Add a modification record to history.
        
        Args:
            action: Type of modification ("created", "edited", "imported", etc.)
            description: Description of the modification
            user: Username who made the modification
        """
        record = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'description': description,
            'user': user
        }
        self.modification_history.append(record)
        self.last_modified = datetime.now()
    
    def add_publication(self, doi_or_pmid: str):
        """Add a publication reference.
        
        Args:
            doi_or_pmid: DOI or PubMed ID
        """
        if doi_or_pmid and doi_or_pmid not in self.publications:
            self.publications.append(doi_or_pmid)
    
    def add_keyword(self, keyword: str):
        """Add a keyword/tag.
        
        Args:
            keyword: Keyword to add
        """
        keyword = keyword.strip().lower()
        if keyword and keyword not in self.keywords:
            self.keywords.append(keyword)
    
    def remove_keyword(self, keyword: str):
        """Remove a keyword/tag.
        
        Args:
            keyword: Keyword to remove
        """
        keyword = keyword.strip().lower()
        if keyword in self.keywords:
            self.keywords.remove(keyword)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ModelMetadata(name='{self.model_name}', id='{self.model_id}', version='{self.version}')"
