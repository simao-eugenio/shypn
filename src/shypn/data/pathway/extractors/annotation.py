"""
Annotation Extractor

Extracts MIRIAM annotations from SBML elements.
"""

from typing import Dict, Optional, Tuple
import logging
import re

try:
    import libsbml
except ImportError:
    libsbml = None

from ..pathway_data import Annotation
from .base import BaseExtractor


class AnnotationExtractor(BaseExtractor[Dict[str, Annotation]]):
    """
    Extracts MIRIAM annotations from SBML elements.
    
    Responsibilities:
    - Parse RDF annotations
    - Extract identifiers.org URIs
    - Map to database IDs (ChEBI, KEGG, UniProt, etc.)
    - Extract SBO terms
    - Extract notes
    
    Supports:
    - Species annotations (metabolites, proteins)
    - Reaction annotations (EC numbers, GO terms)
    """
    
    def extract(self) -> Dict[str, Annotation]:
        """
        Extract annotations for all species and reactions.
        
        Returns:
            Dict mapping element IDs to Annotation objects
        """
        annotations = {}
        
        # Extract species annotations
        for i in range(self.model.getNumSpecies()):
            species = self.model.getSpecies(i)
            species_id = species.getId()
            annotation = self._extract_annotation(species)
            if annotation:
                annotations[species_id] = annotation
        
        # Extract reaction annotations
        for i in range(self.model.getNumReactions()):
            reaction = self.model.getReaction(i)
            reaction_id = reaction.getId()
            annotation = self._extract_annotation(reaction)
            if annotation:
                annotations[reaction_id] = annotation
        
        self.logger.info(f"Extracted {len(annotations)} annotations")
        return annotations
    
    def _extract_annotation(self, sbml_element) -> Optional[Annotation]:
        """
        Extract annotation from single SBML element.
        
        Args:
            sbml_element: libsbml SBase object (Species or Reaction)
            
        Returns:
            Annotation object or None
        """
        if not sbml_element.isSetAnnotation():
            return None
        
        annotation = Annotation()
        
        # Extract SBO term (simple)
        if sbml_element.isSetSBOTerm():
            sbo_term = sbml_element.getSBOTermID()  # Returns "SBO:0000247"
            annotation.sbo_term = sbo_term
        
        # Extract MIRIAM identifiers from RDF
        cv_terms = sbml_element.getCVTerms()
        if cv_terms:
            for i in range(cv_terms.getSize()):
                cv_term = cv_terms.get(i)
                
                # Only process biological qualifiers (not model qualifiers)
                if cv_term.getQualifierType() == libsbml.BIOLOGICAL_QUALIFIER:
                    
                    # Extract URIs
                    for j in range(cv_term.getNumResources()):
                        uri = cv_term.getResourceURI(j)
                        annotation.uris.append(uri)
                        
                        # Parse identifiers.org URIs
                        # Format: http://identifiers.org/{database}/{id}
                        db_info = self._parse_identifiers_uri(uri)
                        if db_info:
                            db_name, db_id = db_info
                            annotation.identifiers[db_name] = db_id
        
        # Extract notes
        if sbml_element.isSetNotes():
            notes_xml = sbml_element.getNotesString()
            # Simple text extraction (strip HTML)
            annotation.notes = self._strip_html(notes_xml)
        
        # Return annotation only if we found something
        return annotation if (annotation.identifiers or annotation.uris or annotation.sbo_term) else None
    
    def _parse_identifiers_uri(self, uri: str) -> Optional[Tuple[str, str]]:
        """
        Parse identifiers.org URI to extract database and ID.
        
        Examples:
            "http://identifiers.org/chebi/CHEBI:15422" → ("chebi", "CHEBI:15422")
            "http://identifiers.org/kegg.compound/C00002" → ("kegg.compound", "C00002")
            "https://identifiers.org/uniprot/P12345" → ("uniprot", "P12345")
        
        Args:
            uri: Full identifiers.org URI
            
        Returns:
            Tuple of (database, id) or None
        """
        if "identifiers.org" not in uri:
            return None
        
        try:
            # Handle both http and https
            parts = uri.split("/")
            if len(parts) >= 5:
                database = parts[-2]
                db_id = parts[-1]
                
                # Normalize database names
                # kegg.compound → kegg, chebi → chebi, etc.
                if '.' in database:
                    # For compound databases like kegg.compound, use base name
                    base_db = database.split('.')[0]
                    if base_db in ['kegg', 'reactome', 'ec-code']:
                        database = base_db
                
                return (database.lower(), db_id)
        except Exception as e:
            self.logger.warning(f"Failed to parse URI: {uri} - {e}")
        
        return None
    
    def _strip_html(self, html: str) -> str:
        """
        Simple HTML tag removal for notes.
        
        Args:
            html: HTML string
            
        Returns:
            Plain text with tags removed
        """
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
