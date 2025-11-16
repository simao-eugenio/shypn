"""Base document generator for creating reports from model metadata.

This module provides the abstract base class for all document generators,
defining the common interface and shared functionality for generating
technical reports, publication documents, and summary sheets.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

from ..metadata.model_metadata import ModelMetadata
from ..metadata.user_profile import UserProfile


class DocumentType(Enum):
    """Types of documents that can be generated."""
    TECHNICAL = "technical"      # Comprehensive technical report
    PUBLICATION = "publication"  # Publication-ready document
    SUMMARY = "summary"          # Brief summary sheet


class BaseDocumentGenerator(ABC):
    """Abstract base class for document generators.
    
    This class provides the common infrastructure for generating documents
    from model metadata, including template management, data composition,
    and output file handling.
    
    Subclasses must implement:
    - _generate_impl(): The actual document generation logic
    - get_file_extension(): The file extension for the output format
    """
    
    def __init__(self, metadata: ModelMetadata, user_profile: Optional[UserProfile] = None):
        """Initialize the generator.
        
        Args:
            metadata: The model metadata to include in the document
            user_profile: Optional user profile for author information
        """
        self.metadata = metadata
        self.user_profile = user_profile
        self.template_dir = Path(__file__).parent.parent / "templates"
        
    def generate(self, 
                 output_path: Path,
                 document_type: DocumentType = DocumentType.TECHNICAL,
                 include_timestamp: bool = True,
                 additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """Generate a document and save it to the specified path.
        
        Args:
            output_path: Path where the document should be saved
            document_type: Type of document to generate
            include_timestamp: Whether to include generation timestamp
            additional_data: Optional additional data to include in document
            
        Returns:
            True if generation succeeded, False otherwise
        """
        try:
            # Compose the document data
            document_data = self._compose_document_data(
                document_type=document_type,
                include_timestamp=include_timestamp,
                additional_data=additional_data
            )
            
            # Call the implementation-specific generation
            self._generate_impl(output_path, document_data, document_type)
            
            return True
            
        except Exception as e:
            print(f"Error generating document: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _compose_document_data(self,
                               document_type: DocumentType,
                               include_timestamp: bool,
                               additional_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Compose all data needed for document generation.
        
        Args:
            document_type: Type of document being generated
            include_timestamp: Whether to include generation timestamp
            additional_data: Optional additional data
            
        Returns:
            Dictionary containing all document data
        """
        data = {
            "metadata": self.metadata.to_dict(),
            "document_type": document_type.value,
            "generation_date": datetime.now().isoformat() if include_timestamp else None,
        }
        
        # Add user profile if available
        if self.user_profile:
            data["user_profile"] = self.user_profile.to_dict()
            
        # Add additional data if provided
        if additional_data:
            data["additional"] = additional_data
            
        # Add computed fields (check in the dict structure)
        metadata_dict = self.metadata.to_dict()
        data["has_authors"] = bool(metadata_dict.get("authorship", {}).get("primary_author") or 
                                   metadata_dict.get("authorship", {}).get("contributors"))
        data["has_references"] = bool(metadata_dict.get("references", {}).get("publications"))
        data["has_biological_context"] = bool(
            metadata_dict.get("biological_context", {}).get("organism") or
            metadata_dict.get("biological_context", {}).get("biological_system") or
            metadata_dict.get("biological_context", {}).get("pathway_name")
        )
        
        return data
    
    @abstractmethod
    def _generate_impl(self,
                       output_path: Path,
                       document_data: Dict[str, Any],
                       document_type: DocumentType) -> None:
        """Implementation-specific document generation.
        
        This method must be implemented by subclasses to generate
        the actual document in their specific format.
        
        Args:
            output_path: Where to save the generated document
            document_data: All data for the document
            document_type: Type of document to generate
            
        Raises:
            Exception: If generation fails
        """
        pass
    
    @abstractmethod
    def get_file_extension(self) -> str:
        """Get the file extension for this generator's output format.
        
        Returns:
            File extension including the dot (e.g., '.pdf', '.xlsx')
        """
        pass
    
    def get_template_path(self, document_type: DocumentType, template_name: str) -> Path:
        """Get the path to a template file.
        
        Args:
            document_type: Type of document
            template_name: Name of the template file
            
        Returns:
            Path to the template file
        """
        return self.template_dir / document_type.value / template_name
    
    def format_author_list(self, authors: List[Dict[str, str]], max_authors: Optional[int] = None) -> str:
        """Format a list of authors for display.
        
        Args:
            authors: List of author dictionaries with 'name' and optionally 'affiliation'
            max_authors: Maximum number of authors to include before using 'et al.'
            
        Returns:
            Formatted author string
        """
        if not authors:
            return "Unknown"
            
        if max_authors and len(authors) > max_authors:
            displayed = authors[:max_authors]
            names = [a.get("name", "Unknown") for a in displayed]
            return ", ".join(names) + " et al."
        else:
            names = [a.get("name", "Unknown") for a in authors]
            if len(names) == 1:
                return names[0]
            elif len(names) == 2:
                return f"{names[0]} and {names[1]}"
            else:
                return ", ".join(names[:-1]) + f", and {names[-1]}"
    
    def format_date(self, date_str: Optional[str]) -> str:
        """Format a date string for display.
        
        Args:
            date_str: ISO format date string
            
        Returns:
            Human-readable date string
        """
        if not date_str:
            return "Not specified"
            
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%B %d, %Y")
        except (ValueError, AttributeError):
            return date_str
