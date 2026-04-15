"""Tests for metadata enhancement processor.

Tests:
- Creation and configuration
- Applicability checks
- Compound name extraction
- Reaction name extraction
- KEGG ID extraction
- Compound type detection (metabolite vs cofactor)
- Color extraction
- Statistics tracking
"""

import pytest
from unittest.mock import Mock

from shypn.pathway.metadata_enhancer import MetadataEnhancer
from shypn.pathway.options import EnhancementOptions
from shypn.data.canvas.document_model import DocumentModel


# Fixtures

@pytest.fixture
def options():
    """Create test options."""
    return EnhancementOptions(
        enable_metadata_enhancement=True,
        metadata_extract_names=True,
        metadata_extract_colors=True,
        metadata_extract_kegg_ids=True
    )


@pytest.fixture
def enhancer(options):
    """Create metadata enhancer."""
    return MetadataEnhancer(options)


@pytest.fixture
def document():
    """Create empty document."""
    doc = DocumentModel()
    return doc


@pytest.fixture
def mock_entry():
    """Create mock KEGG entry for a compound."""
    entry = Mock()
    entry.graphics = Mock()
    entry.graphics.name = "Glucose"
    entry.graphics.bgcolor = "#BFFFBF"
    entry.graphics.fgcolor = "#000000"
    entry.name = "cpd:C00031"
    entry.get_kegg_ids.return_value = ["cpd:C00031"]
    return entry


@pytest.fixture
def mock_cofactor_entry():
    """Create mock KEGG entry for ATP."""
    entry = Mock()
    entry.graphics = Mock()
    entry.graphics.name = "ATP"
    entry.graphics.bgcolor = "#FFFFBF"
    entry.graphics.fgcolor = "#000000"
    entry.name = "cpd:C00002"
    entry.get_kegg_ids.return_value = ["cpd:C00002"]
    return entry


@pytest.fixture
def mock_gene_entry():
    """Create mock KEGG entry for genes."""
    entry = Mock()
    entry.graphics = Mock()
    entry.graphics.name = "HK1, HK2, HK3"
    entry.graphics.bgcolor = "#BFBFFF"
    entry.graphics.fgcolor = "#000000"
    entry.name = "hsa:3098"
    entry.get_kegg_ids.return_value = ["hsa:3098", "hsa:3099", "hsa:3101"]
    return entry


@pytest.fixture
def mock_reaction():
    """Create mock KEGG reaction."""
    reaction = Mock()
    reaction.id = "1"
    reaction.name = "rn:R01786"
    reaction.type = "irreversible"
    reaction.substrates = []
    reaction.products = []
    reaction.is_reversible.return_value = False
    return reaction


@pytest.fixture
def mock_pathway(mock_entry, mock_gene_entry, mock_reaction):
    """Create mock KEGG pathway."""
    pathway = Mock()
    pathway.entries = {
        '1': mock_entry,
        '2': mock_gene_entry
    }
    pathway.reactions = [mock_reaction]
    return pathway


# Creation Tests

class TestMetadataEnhancerCreation:
    """Test MetadataEnhancer creation."""
    
    def test_creation_with_options(self, options):
        """Test creating enhancer with options."""
        enhancer = MetadataEnhancer(options)
        assert enhancer is not None
        assert enhancer.options == options
        assert enhancer.get_name() == "Metadata Enhancer"
    
    def test_creation_without_options(self):
        """Test creating enhancer without options."""
        enhancer = MetadataEnhancer()
        assert enhancer is not None
        assert enhancer.options is None


# Applicability Tests

class TestMetadataEnhancerApplicability:
    """Test applicability checks."""
    
    def test_applicable_with_pathway(self, enhancer, document, mock_pathway):
        """Test applicable when pathway provided."""
        # Add a place
        document.create_place(100, 100)
        
        assert enhancer.is_applicable(document, mock_pathway)
    
    def test_not_applicable_without_pathway(self, enhancer, document):
        """Test not applicable without pathway."""
        document.create_place(100, 100)
        
        assert not enhancer.is_applicable(document, None)
    
    def test_not_applicable_when_disabled(self, document, mock_pathway):
        """Test not applicable when disabled."""
        options = EnhancementOptions(enable_metadata_enhancement=False)
        enhancer = MetadataEnhancer(options)
        
        document.create_place(100, 100)
        
        assert not enhancer.is_applicable(document, mock_pathway)
    
    def test_not_applicable_empty_document(self, enhancer, document, mock_pathway):
        """Test not applicable with empty document."""
        assert not enhancer.is_applicable(document, mock_pathway)


# Compound Name Extraction Tests

class TestCompoundNameExtraction:
    """Test compound name extraction."""
    
    def test_extract_name_from_graphics(self, enhancer, mock_entry):
        """Test extracting name from graphics."""
        name = enhancer._extract_compound_name(mock_entry)
        assert name == "Glucose"
    
    def test_extract_name_fallback_to_kegg_id(self, enhancer):
        """Test fallback to KEGG ID."""
        entry = Mock()
        entry.graphics = None
        entry.get_kegg_ids.return_value = ["cpd:C00031"]
        
        name = enhancer._extract_compound_name(entry)
        assert name == "cpd:C00031"
    
    def test_extract_name_default(self, enhancer):
        """Test default name."""
        entry = Mock()
        entry.graphics = None
        entry.get_kegg_ids.return_value = []
        
        name = enhancer._extract_compound_name(entry)
        assert name == "Compound"
    
    def test_clean_compound_name_formatting(self, enhancer):
        """Test cleaning compound name formatting."""
        entry = Mock()
        entry.graphics = Mock()
        entry.graphics.name = "D-Glucose,alpha-D-Glucose"
        entry.get_kegg_ids.return_value = []
        
        name = enhancer._extract_compound_name(entry)
        # Should add space after comma
        assert ", " in name


# Reaction Name Extraction Tests

class TestReactionNameExtraction:
    """Test reaction name extraction."""
    
    def test_extract_reaction_name_from_graphics(self, enhancer, mock_gene_entry):
        """Test extracting reaction name from graphics."""
        name = enhancer._extract_reaction_name(mock_gene_entry, None)
        # Should truncate gene list
        assert name == "HK1 (+2)"
    
    def test_extract_reaction_name_single_gene(self, enhancer):
        """Test extracting single gene name."""
        entry = Mock()
        entry.graphics = Mock()
        entry.graphics.name = "HK1"
        entry.get_kegg_ids.return_value = []
        
        name = enhancer._extract_reaction_name(entry, None)
        assert name == "HK1"
    
    def test_extract_reaction_name_from_reaction(self, enhancer, mock_reaction):
        """Test extracting name from reaction."""
        entry = Mock()
        entry.graphics = None
        entry.get_kegg_ids.return_value = []
        
        name = enhancer._extract_reaction_name(entry, mock_reaction)
        assert name == "rn:R01786"
    
    def test_extract_reaction_name_default(self, enhancer):
        """Test default reaction name."""
        entry = Mock()
        entry.graphics = None
        entry.get_kegg_ids.return_value = []
        
        name = enhancer._extract_reaction_name(entry, None)
        assert name == "Reaction"


# Compound Type Detection Tests

class TestCompoundTypeDetection:
    """Test compound type detection."""
    
    def test_detect_metabolite(self, enhancer, mock_entry):
        """Test detecting metabolite."""
        compound_type = enhancer._get_compound_type(mock_entry)
        assert compound_type == "metabolite"
    
    def test_detect_cofactor_atp(self, enhancer, mock_cofactor_entry):
        """Test detecting ATP as cofactor."""
        compound_type = enhancer._get_compound_type(mock_cofactor_entry)
        assert compound_type == "cofactor"
    
    def test_detect_cofactor_water(self, enhancer):
        """Test detecting H2O as cofactor."""
        entry = Mock()
        entry.get_kegg_ids.return_value = ["cpd:C00001"]
        
        compound_type = enhancer._get_compound_type(entry)
        assert compound_type == "cofactor"
    
    def test_detect_cofactor_nad(self, enhancer):
        """Test detecting NAD+ as cofactor."""
        entry = Mock()
        entry.get_kegg_ids.return_value = ["cpd:C00003"]
        
        compound_type = enhancer._get_compound_type(entry)
        assert compound_type == "cofactor"
    
    def test_unknown_type_no_kegg_id(self, enhancer):
        """Test unknown type when no KEGG ID."""
        entry = Mock()
        entry.get_kegg_ids.return_value = []
        
        compound_type = enhancer._get_compound_type(entry)
        assert compound_type == "unknown"


# KEGG ID Extraction Tests

class TestKEGGIDExtraction:
    """Test KEGG ID extraction."""
    
    def test_store_compound_kegg_ids(self, enhancer, document, mock_pathway):
        """Test storing compound KEGG IDs."""
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_compound_ids' in place.metadata
        assert place.metadata['kegg_compound_ids'] == ["cpd:C00031"]
    
    def test_store_gene_kegg_ids(self, enhancer, document, mock_pathway):
        """Test storing gene KEGG IDs."""
        transition = document.create_transition(200, 200)
        transition.metadata = {'kegg_entry_id': '2'}
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_gene_ids' in transition.metadata
        assert len(transition.metadata['kegg_gene_ids']) == 3


# Color Extraction Tests

class TestColorExtraction:
    """Test color extraction."""
    
    def test_extract_place_colors(self, enhancer, document, mock_pathway):
        """Test extracting place colors."""
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_bgcolor' in place.metadata
        assert place.metadata['kegg_bgcolor'] == "#BFFFBF"
        assert 'kegg_fgcolor' in place.metadata
        assert place.metadata['kegg_fgcolor'] == "#000000"
    
    def test_extract_transition_colors(self, enhancer, document, mock_pathway):
        """Test extracting transition colors."""
        transition = document.create_transition(200, 200)
        transition.metadata = {'kegg_entry_id': '2'}
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_bgcolor' in transition.metadata
        assert transition.metadata['kegg_bgcolor'] == "#BFBFFF"
    
    def test_skip_colors_when_disabled(self, document, mock_pathway):
        """Test skipping colors when disabled."""
        options = EnhancementOptions(
            enable_metadata_enhancement=True,
            metadata_extract_colors=False
        )
        enhancer = MetadataEnhancer(options)
        
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_bgcolor' not in place.metadata


# Label Update Tests

class TestLabelUpdates:
    """Test label updates."""
    
    def test_update_place_label(self, enhancer, document, mock_pathway):
        """Test updating place label."""
        place = document.create_place(100, 100)
        place.label = place.name  # Set label to match default name
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, mock_pathway)
        
        assert place.label == "Glucose"
    
    def test_update_transition_label(self, enhancer, document, mock_pathway):
        """Test updating transition label."""
        transition = document.create_transition(200, 200)
        transition.label = transition.name  # Set label to match default name
        transition.metadata = {'kegg_entry_id': '2'}
        
        enhancer.process(document, mock_pathway)
        
        assert transition.label == "HK1 (+2)"
    
    def test_preserve_custom_label(self, enhancer, document, mock_pathway):
        """Test preserving custom labels."""
        place = document.create_place(100, 100)
        place.label = "Custom Label"  # Set custom label (different from name)
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, mock_pathway)
        
        # Should not overwrite custom label
        assert place.label == "Custom Label"


# Reaction Metadata Tests

class TestReactionMetadata:
    """Test reaction metadata extraction."""
    
    def test_store_reaction_info(self, enhancer, document, mock_pathway, mock_reaction):
        """Test storing reaction information."""
        transition = document.create_transition(200, 200)
        transition.metadata = {
            'kegg_entry_id': '2',
            'kegg_reaction_id': '1'
        }
        
        enhancer.process(document, mock_pathway)
        
        assert 'kegg_reaction_name' in transition.metadata
        assert transition.metadata['kegg_reaction_name'] == "rn:R01786"
        assert 'kegg_reaction_type' in transition.metadata
        assert transition.metadata['kegg_reaction_type'] == "irreversible"
        assert 'is_reversible' in transition.metadata
        assert transition.metadata['is_reversible'] is False


# Statistics Tests

class TestMetadataEnhancerStatistics:
    """Test statistics tracking."""
    
    def test_statistics_with_enhancements(self, enhancer, document, mock_pathway):
        """Test statistics after enhancement."""
        # Add places
        place1 = document.create_place(100, 100)
        place1.metadata = {'kegg_entry_id': '1'}
        place2 = document.create_place(150, 100)
        place2.metadata = {'kegg_entry_id': '1'}
        
        # Add transition
        transition = document.create_transition(200, 200)
        transition.metadata = {'kegg_entry_id': '2'}
        
        enhancer.process(document, mock_pathway)
        
        stats = enhancer.get_stats()
        assert stats['places_enhanced'] == 2
        assert stats['transitions_enhanced'] == 1
        assert stats['kegg_ids_added'] >= 4  # 2 places + 3 genes + 1 reaction
        assert stats['implemented'] is True
    
    def test_statistics_no_matching_entries(self, enhancer, document, mock_pathway):
        """Test statistics with no matching entries."""
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': 'nonexistent'}
        
        enhancer.process(document, mock_pathway)
        
        stats = enhancer.get_stats()
        assert stats['places_enhanced'] == 0
    
    def test_statistics_without_pathway(self, enhancer, document):
        """Test statistics without pathway data."""
        document.create_place(100, 100)
        
        enhancer.process(document, None)
        
        stats = enhancer.get_stats()
        assert stats['places_enhanced'] == 0
        assert stats['transitions_enhanced'] == 0
        assert stats['kegg_ids_added'] == 0


# Edge Cases

class TestMetadataEnhancerEdgeCases:
    """Test edge cases."""
    
    def test_no_metadata_dict(self, enhancer, document, mock_pathway):
        """Test handling places without metadata dict."""
        place = document.create_place(100, 100)
        # No metadata dict
        
        # Should not crash
        enhancer.process(document, mock_pathway)
        
        # Should create metadata dict
        assert hasattr(place, 'metadata')
    
    def test_partial_graphics_data(self, enhancer, document):
        """Test handling entry with partial graphics."""
        pathway = Mock()
        entry = Mock()
        entry.graphics = Mock()
        entry.graphics.name = "Glucose"
        entry.graphics.bgcolor = None  # Missing bgcolor
        entry.graphics.fgcolor = None
        entry.get_kegg_ids.return_value = ["cpd:C00031"]
        pathway.entries = {'1': entry}
        pathway.reactions = []
        
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': '1'}
        
        enhancer.process(document, pathway)
        
        # Should handle gracefully
        assert 'compound_name' in place.metadata
        assert 'kegg_bgcolor' not in place.metadata
    
    def test_empty_pathway(self, enhancer, document):
        """Test with empty pathway."""
        pathway = Mock()
        pathway.entries = {}
        pathway.reactions = []
        
        place = document.create_place(100, 100)
        place.metadata = {'kegg_entry_id': '1'}
        
        # Should not crash
        enhancer.process(document, pathway)
        
        stats = enhancer.get_stats()
        assert stats['places_enhanced'] == 0
