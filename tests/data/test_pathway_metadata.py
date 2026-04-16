#!/usr/bin/env python3
"""Unit tests for PathwayDocument and EnrichmentDocument.

Tests the pathway metadata schema implementation including:
- PathwayDocument creation and serialization
- EnrichmentDocument creation and serialization
- Project integration with pathway manager
- Migration from old format
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from shypn.data.pathway_document import PathwayDocument
from shypn.data.enrichment_document import EnrichmentDocument
from shypn.data.project_models import Project, ModelDocument


class TestPathwayDocument(unittest.TestCase):
    """Test PathwayDocument class."""
    
    def test_create_pathway_document(self):
        """Test creating a PathwayDocument."""
        pathway = PathwayDocument(
            name="Glycolysis",
            source_type="kegg",
            source_id="hsa00010",
            source_organism="Homo sapiens"
        )
        
        self.assertEqual(pathway.name, "Glycolysis")
        self.assertEqual(pathway.source_type, "kegg")
        self.assertEqual(pathway.source_id, "hsa00010")
        self.assertEqual(pathway.source_organism, "Homo sapiens")
        self.assertIsNotNone(pathway.id)
        self.assertIsNotNone(pathway.imported_date)
        self.assertEqual(len(pathway.enrichments), 0)
        self.assertIsNone(pathway.model_id)
    
    def test_pathway_serialization(self):
        """Test PathwayDocument to_dict and from_dict."""
        original = PathwayDocument(
            name="TCA Cycle",
            source_type="sbml",
            source_id="tca_cycle.xml",
            source_organism="Saccharomyces cerevisiae"
        )
        original.raw_file = "tca_cycle.sbml"
        original.metadata_file = "tca_cycle.meta.json"
        original.tags = ["metabolism", "mitochondria"]
        original.notes = "Test pathway"
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = PathwayDocument.from_dict(data)
        
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.source_type, original.source_type)
        self.assertEqual(restored.source_id, original.source_id)
        self.assertEqual(restored.raw_file, original.raw_file)
        self.assertEqual(restored.metadata_file, original.metadata_file)
        self.assertEqual(restored.tags, original.tags)
        self.assertEqual(restored.notes, original.notes)
    
    def test_pathway_enrichment_operations(self):
        """Test adding/removing enrichments."""
        pathway = PathwayDocument(name="Test Pathway", source_type="kegg")
        
        # Add enrichment
        enrichment = EnrichmentDocument(source="brenda")
        pathway.add_enrichment(enrichment)
        
        self.assertEqual(pathway.get_enrichment_count(), 1)
        self.assertTrue(pathway.has_enrichments())
        
        # Get enrichment
        retrieved = pathway.get_enrichment(enrichment.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, enrichment.id)
        
        # Remove enrichment
        result = pathway.remove_enrichment(enrichment.id)
        self.assertTrue(result)
        self.assertEqual(pathway.get_enrichment_count(), 0)
    
    def test_pathway_model_linking(self):
        """Test linking pathway to model."""
        pathway = PathwayDocument(name="Test", source_type="kegg")
        
        self.assertFalse(pathway.is_converted())
        
        pathway.link_to_model("model-123")
        self.assertTrue(pathway.is_converted())
        self.assertEqual(pathway.model_id, "model-123")
        
        pathway.unlink_from_model()
        self.assertFalse(pathway.is_converted())
        self.assertIsNone(pathway.model_id)


class TestEnrichmentDocument(unittest.TestCase):
    """Test EnrichmentDocument class."""
    
    def test_create_enrichment_document(self):
        """Test creating an EnrichmentDocument."""
        enrichment = EnrichmentDocument(
            type="kinetics",
            source="brenda"
        )
        
        self.assertEqual(enrichment.type, "kinetics")
        self.assertEqual(enrichment.source, "brenda")
        self.assertIsNotNone(enrichment.id)
        self.assertIsNotNone(enrichment.applied_date)
        self.assertEqual(len(enrichment.transitions_enriched), 0)
        self.assertEqual(len(enrichment.parameters_added), 0)
    
    def test_enrichment_serialization(self):
        """Test EnrichmentDocument to_dict and from_dict."""
        original = EnrichmentDocument(type="kinetics", source="brenda")
        original.source_query = {"ec_number": "2.7.1.1", "organism": "Homo sapiens"}
        original.data_file = "brenda_hsa00010.json"
        original.add_transition("R01")
        original.add_transition("R02")
        original.add_parameter("km_values", 5)
        original.add_parameter("kcat_values", 3)
        original.add_citation("PMID:12345678")
        original.set_confidence("high")
        
        # Serialize
        data = original.to_dict()
        
        # Deserialize
        restored = EnrichmentDocument.from_dict(data)
        
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.type, original.type)
        self.assertEqual(restored.source, original.source)
        self.assertEqual(restored.source_query, original.source_query)
        self.assertEqual(restored.data_file, original.data_file)
        self.assertEqual(len(restored.transitions_enriched), 2)
        self.assertEqual(restored.get_total_parameters(), 8)
        self.assertEqual(restored.confidence, "high")
    
    def test_enrichment_operations(self):
        """Test enrichment data operations."""
        enrichment = EnrichmentDocument()
        
        # Add transitions
        enrichment.add_transition("T1")
        enrichment.add_transition("T2")
        enrichment.add_transition("T1")  # Duplicate should not add
        self.assertEqual(enrichment.get_transition_count(), 2)
        
        # Add parameters
        enrichment.add_parameter("km_values", 3)
        enrichment.add_parameter("kcat_values", 2)
        enrichment.add_parameter("km_values", 1)  # Increment existing
        self.assertEqual(enrichment.get_total_parameters(), 6)
        self.assertEqual(enrichment.parameters_added["km_values"], 4)
        
        # Add citations
        enrichment.add_citation("PMID:111")
        enrichment.add_citation("PMID:222")
        enrichment.add_citation("PMID:111")  # Duplicate should not add
        self.assertEqual(enrichment.get_citation_count(), 2)
        
        # Confidence
        enrichment.set_confidence("high")
        self.assertTrue(enrichment.is_high_confidence())


class TestProjectPathwayIntegration(unittest.TestCase):
    """Test Project integration with pathway manager."""
    
    def setUp(self):
        """Create temporary project directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.project = Project(
            name="Test Project",
            base_path=self.temp_dir
        )
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_add_pathway_to_project(self):
        """Test adding pathway to project."""
        pathway = PathwayDocument(
            name="Glycolysis",
            source_type="kegg",
            source_id="hsa00010"
        )
        
        self.project.add_pathway(pathway)
        
        # Verify pathway was added
        retrieved = self.project.get_pathway(pathway.id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "Glycolysis")
    
    def test_remove_pathway_from_project(self):
        """Test removing pathway from project."""
        pathway = PathwayDocument(name="Test", source_type="kegg")
        self.project.add_pathway(pathway)
        
        result = self.project.remove_pathway(pathway.id)
        self.assertTrue(result)
        
        # Verify pathway was removed
        retrieved = self.project.get_pathway(pathway.id)
        self.assertIsNone(retrieved)
    
    def test_find_pathway_by_model_id(self):
        """Test finding pathway by linked model ID."""
        pathway = PathwayDocument(name="Test", source_type="kegg")
        pathway.link_to_model("model-123")
        self.project.add_pathway(pathway)
        
        found = self.project.find_pathway_by_model_id("model-123")
        self.assertIsNotNone(found)
        self.assertEqual(found.id, pathway.id)
        
        not_found = self.project.find_pathway_by_model_id("model-999")
        self.assertIsNone(not_found)
    
    def test_pathway_file_operations(self):
        """Test saving and loading pathway files."""
        pathway = PathwayDocument(name="Test", source_type="kegg")
        pathway.raw_file = "test.kgml"
        self.project.add_pathway(pathway)
        
        # Save file
        content = "<kgml>test content</kgml>"
        saved_path = self.project.pathways.save_pathway_file("test.kgml", content)
        
        self.assertTrue(saved_path.exists())
        
        # Load file
        loaded_content = self.project.pathways.load_pathway_file("test.kgml")
        self.assertEqual(loaded_content, content)
    
    def test_project_serialization_with_pathways(self):
        """Test Project serialization with pathways."""
        # Add pathway
        pathway = PathwayDocument(
            name="Glycolysis",
            source_type="kegg",
            source_id="hsa00010"
        )
        pathway.raw_file = "hsa00010.kgml"
        
        enrichment = EnrichmentDocument(source="brenda")
        enrichment.add_transition("R01")
        pathway.add_enrichment(enrichment)
        
        self.project.add_pathway(pathway)
        
        # Serialize
        data = self.project.to_dict()
        
        # Verify pathways in dict
        self.assertIn('pathways', data['content'])
        pathways_data = data['content']['pathways']
        self.assertIsInstance(pathways_data, dict)
        self.assertEqual(len(pathways_data), 1)
        
        # Deserialize
        restored_project = Project.from_dict(data)
        
        # Verify pathway restored
        restored_pathway = restored_project.get_pathway(pathway.id)
        self.assertIsNotNone(restored_pathway)
        self.assertEqual(restored_pathway.name, "Glycolysis")
        self.assertEqual(restored_pathway.source_type, "kegg")
        self.assertEqual(len(restored_pathway.enrichments), 1)
    
    def test_migration_from_old_format(self):
        """Test migration from old flat list format."""
        # Create project data in old format (v1.0)
        old_data = {
            'document_type': 'project',
            'version': '1.0',
            'identity': {
                'id': 'proj-123',
                'name': 'Old Project',
                'description': '',
                'created_date': '2025-01-01T00:00:00',
                'modified_date': '2025-01-01T00:00:00'
            },
            'location': {
                'base_path': self.temp_dir
            },
            'content': {
                'models': [],
                'pathways': ['hsa00010.kgml', 'hsa00020.kgml'],  # Old flat list
                'simulations': []
            },
            'metadata': {
                'tags': [],
                'settings': {}
            }
        }
        
        # Load with migration
        project = Project.from_dict(old_data)
        
        # Verify migration
        pathways = project.pathways.list_pathways()
        self.assertEqual(len(pathways), 2)
        
        # Check migrated pathways
        for pathway in pathways:
            self.assertIn('migrated', pathway.tags)
            self.assertIn('.kgml', pathway.raw_file)


if __name__ == '__main__':
    unittest.main()
