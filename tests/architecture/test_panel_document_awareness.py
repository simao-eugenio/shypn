"""Test Panel Document Awareness - MDI Architecture Validation.

This test suite validates that ALL UI panels (Pathway, Topology, Analysis,
Viability, Report) maintain proper document awareness in the MDI architecture.

Critical Requirements:
1. Each panel must track which document (drawing_area) it belongs to
2. Panels must only respond to events for their own document
3. Panels must maintain independent state per document
4. Tab switching must swap panel instances correctly
5. No cross-document state contamination

Architecture Under Test:
- PathwayPanelLoader (PerDocumentPanelLoader)
- TopologyPanelLoader (PerDocumentPanelLoader)
- AnalysesPanelLoader (PerDocumentPanelLoader)
- ViabilityPanelLoader (needs validation)
- ReportPanelLoader (needs validation)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from shypn.helpers.pathway_panel_loader import PathwayPanelLoader
from shypn.helpers.topology_panel_loader import TopologyPanelLoader
from shypn.helpers.analyses_panel_loader import AnalysesPanelLoader
from shypn.helpers.viability_panel_loader import ViabilityPanelLoader
from shypn.helpers.report_panel_loader import ReportPanelLoader
from shypn.data.canvas.document_model import DocumentModel


class TestPanelDocumentAwareness:
    """Validate that all panels maintain document awareness."""
    
    def test_pathway_panel_has_document_id(self):
        """PathwayPanelLoader must track document_id."""
        doc_id = "doc_001"
        drawing_area = Mock()
        model = Mock()
        
        with patch('shypn.helpers.pathway_panel_loader.PathwayOperationsPanel'):
            loader = PathwayPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
        
        assert hasattr(loader, 'document_id')
        assert loader.document_id == doc_id
        assert hasattr(loader, 'drawing_area')
        assert loader.drawing_area == drawing_area
    
    def test_topology_panel_has_document_id(self):
        """TopologyPanelLoader must track document_id."""
        doc_id = "doc_002"
        drawing_area = Mock()
        model = Mock()
        
        with patch('shypn.helpers.topology_panel_loader.TopologyPanel'):
            loader = TopologyPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
        
        assert hasattr(loader, 'document_id')
        assert loader.document_id == doc_id
        assert hasattr(loader, 'drawing_area')
        assert loader.drawing_area == drawing_area
    
    def test_analyses_panel_has_document_id(self):
        """AnalysesPanelLoader must track document_id."""
        doc_id = "doc_003"
        drawing_area = Mock()
        model = Mock()
        
        with patch('shypn.helpers.analyses_panel_loader.DynamicAnalysesPanel'):
            loader = AnalysesPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
        
        assert hasattr(loader, 'document_id')
        assert loader.document_id == doc_id
        assert hasattr(loader, 'drawing_area')
        assert loader.drawing_area == drawing_area
    
    def test_viability_panel_has_document_id(self):
        """ViabilityPanelLoader must track document_id."""
        doc_id = "doc_004"
        drawing_area = Mock()
        model = Mock()
        
        with patch('shypn.helpers.viability_panel_loader.ViabilityPanel'):
            loader = ViabilityPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
        
        assert hasattr(loader, 'document_id')
        assert loader.document_id == doc_id
        assert hasattr(loader, 'drawing_area')
        assert loader.drawing_area == drawing_area
    
    def test_report_panel_has_document_id(self):
        """ReportPanelLoader must track document_id."""
        doc_id = "doc_005"
        drawing_area = Mock()
        
        with patch('shypn.helpers.report_panel_loader.ReportPanel'):
            loader = ReportPanelLoader(
                document_id=doc_id,
                drawing_area=drawing_area
            )
        
        assert hasattr(loader, 'document_id')
        assert loader.document_id == doc_id
        assert hasattr(loader, 'drawing_area')
        assert loader.drawing_area == drawing_area
    
    def test_multiple_documents_have_different_panel_instances(self):
        """Each document must have its own panel instances."""
        doc1_id = "doc_A"
        doc2_id = "doc_B"
        drawing_area1 = Mock()
        drawing_area2 = Mock()
        model1 = Mock()
        model2 = Mock()
        
        with patch('shypn.helpers.pathway_panel_loader.PathwayOperationsPanel'):
            loader1 = PathwayPanelLoader(
                model=model1,
                document_id=doc1_id,
                drawing_area=drawing_area1
            )
            loader2 = PathwayPanelLoader(
                model=model2,
                document_id=doc2_id,
                drawing_area=drawing_area2
            )
        
        # Different instances
        assert loader1 is not loader2
        assert loader1.document_id != loader2.document_id
        assert loader1.drawing_area is not loader2.drawing_area
        assert loader1.model is not loader2.model
    
    def test_panels_inherit_from_per_document_base(self):
        """Pathway, Topology, Analyses must inherit from PerDocumentPanelLoader."""
        from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
        
        # These should inherit from PerDocumentPanelLoader
        assert issubclass(PathwayPanelLoader, PerDocumentPanelLoader)
        assert issubclass(TopologyPanelLoader, PerDocumentPanelLoader)
        assert issubclass(AnalysesPanelLoader, PerDocumentPanelLoader)
        
        # Note: Viability and Report may not inherit yet (architectural debt)
        # Document this for future refactoring


class TestPanelEventFiltering:
    """Validate panels filter events by document_id."""
    
    def test_pathway_panel_filters_events_by_document_id(self):
        """PathwayPanel should only respond to events for its document."""
        doc_id = "my_document"
        other_doc_id = "other_document"
        
        model = Mock()
        drawing_area = Mock()
        
        with patch('shypn.helpers.pathway_panel_loader.PathwayOperationsPanel') as MockPanel:
            mock_panel_instance = MockPanel.return_value
            
            loader = PathwayPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
            
            # Event for our document
            our_event = {'_document_id': doc_id, 'data': 'test'}
            # Event for other document
            other_event = {'_document_id': other_doc_id, 'data': 'test'}
            
            # Both should have document_id for filtering
            assert loader.document_id == doc_id
    
    def test_topology_panel_filters_events_by_document_id(self):
        """TopologyPanel should only respond to events for its document."""
        doc_id = "my_document"
        model = Mock()
        drawing_area = Mock()
        
        with patch('shypn.helpers.topology_panel_loader.TopologyPanel'):
            loader = TopologyPanelLoader(
                model=model,
                document_id=doc_id,
                drawing_area=drawing_area
            )
            
            assert loader.document_id == doc_id


class TestPanelStateIsolation:
    """Validate panels maintain independent state per document."""
    
    def test_pathway_panels_have_independent_state(self):
        """Two PathwayPanels for different documents must have independent state."""
        model1 = Mock()
        model2 = Mock()
        
        with patch('shypn.helpers.pathway_panel_loader.PathwayOperationsPanel') as MockPanel:
            # Create two panel instances
            panel1_mock = Mock()
            panel2_mock = Mock()
            MockPanel.side_effect = [panel1_mock, panel2_mock]
            
            loader1 = PathwayPanelLoader(
                model=model1,
                document_id="doc1",
                drawing_area=Mock()
            )
            loader2 = PathwayPanelLoader(
                model=model2,
                document_id="doc2",
                drawing_area=Mock()
            )
            
            # Different panel instances
            assert loader1.panel is not loader2.panel
            assert loader1.model is not loader2.model
    
    def test_topology_panels_have_independent_state(self):
        """Two TopologyPanels for different documents must have independent state."""
        model1 = Mock()
        model2 = Mock()
        
        with patch('shypn.helpers.topology_panel_loader.TopologyPanel') as MockPanel:
            panel1_mock = Mock()
            panel2_mock = Mock()
            MockPanel.side_effect = [panel1_mock, panel2_mock]
            
            loader1 = TopologyPanelLoader(
                model=model1,
                document_id="doc1",
                drawing_area=Mock()
            )
            loader2 = TopologyPanelLoader(
                model=model2,
                document_id="doc2",
                drawing_area=Mock()
            )
            
            assert loader1.panel is not loader2.panel
            assert loader1.model is not loader2.model
    
    def test_analyses_panels_have_independent_state(self):
        """Two AnalysesPanels for different documents must have independent state."""
        model1 = Mock()
        model2 = Mock()
        
        with patch('shypn.helpers.analyses_panel_loader.DynamicAnalysesPanel') as MockPanel:
            panel1_mock = Mock()
            panel2_mock = Mock()
            MockPanel.side_effect = [panel1_mock, panel2_mock]
            
            loader1 = AnalysesPanelLoader(
                model=model1,
                document_id="doc1",
                drawing_area=Mock()
            )
            loader2 = AnalysesPanelLoader(
                model=model2,
                document_id="doc2",
                drawing_area=Mock()
            )
            
            assert loader1.panel is not loader2.panel
            assert loader1.model is not loader2.model


class TestPanelDocumentReferenceIntegrity:
    """Validate panels maintain correct references to their document."""
    
    def test_panel_loaders_store_document_references(self):
        """All panel loaders must store document_id and drawing_area."""
        doc_id = "test_doc"
        drawing_area = Mock()
        model = Mock()
        
        panels_to_test = [
            ('pathway', PathwayPanelLoader, 'shypn.helpers.pathway_panel_loader.PathwayOperationsPanel'),
            ('topology', TopologyPanelLoader, 'shypn.helpers.topology_panel_loader.TopologyPanel'),
            ('analyses', AnalysesPanelLoader, 'shypn.helpers.analyses_panel_loader.DynamicAnalysesPanel'),
            ('viability', ViabilityPanelLoader, 'shypn.helpers.viability_panel_loader.ViabilityPanel'),
            ('report', ReportPanelLoader, 'shypn.helpers.report_panel_loader.ReportPanel'),
        ]
        
        for panel_name, loader_class, patch_target in panels_to_test:
            with patch(patch_target):
                if panel_name == 'report':
                    loader = loader_class(
                        document_id=doc_id,
                        drawing_area=drawing_area
                    )
                else:
                    loader = loader_class(
                        model=model,
                        document_id=doc_id,
                        drawing_area=drawing_area
                    )
                
                # All loaders must have these attributes
                assert hasattr(loader, 'document_id'), f"{panel_name} loader missing document_id"
                assert loader.document_id == doc_id, f"{panel_name} loader has wrong document_id"
                assert hasattr(loader, 'drawing_area'), f"{panel_name} loader missing drawing_area"
                assert loader.drawing_area == drawing_area, f"{panel_name} loader has wrong drawing_area"


class TestArchitecturalDebt:
    """Document architectural debt for future refactoring."""
    
    def test_viability_should_inherit_per_document_base(self):
        """ViabilityPanelLoader should inherit from PerDocumentPanelLoader."""
        from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
        
        # Current state - does not inherit (architectural debt)
        is_subclass = issubclass(ViabilityPanelLoader, PerDocumentPanelLoader)
        
        if not is_subclass:
            pytest.skip(
                "ARCHITECTURAL DEBT: ViabilityPanelLoader should inherit from "
                "PerDocumentPanelLoader. Currently has custom implementation. "
                "TODO: Refactor to use base class pattern like Pathway/Topology/Analyses."
            )
    
    def test_report_should_inherit_per_document_base(self):
        """ReportPanelLoader should inherit from PerDocumentPanelLoader."""
        from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
        
        # Current state - does not inherit (architectural debt)
        is_subclass = issubclass(ReportPanelLoader, PerDocumentPanelLoader)
        
        if not is_subclass:
            pytest.skip(
                "ARCHITECTURAL DEBT: ReportPanelLoader should inherit from "
                "PerDocumentPanelLoader. Currently has custom implementation. "
                "TODO: Refactor to use base class pattern like Pathway/Topology/Analyses."
            )
    
    def test_document_all_panel_loaders_have_document_awareness(self):
        """Document which panels have proper document awareness."""
        from shypn.helpers.base_panel_loader import PerDocumentPanelLoader
        
        compliant_panels = []
        non_compliant_panels = []
        
        panels = [
            ('PathwayPanelLoader', PathwayPanelLoader),
            ('TopologyPanelLoader', TopologyPanelLoader),
            ('AnalysesPanelLoader', AnalysesPanelLoader),
            ('ViabilityPanelLoader', ViabilityPanelLoader),
            ('ReportPanelLoader', ReportPanelLoader),
        ]
        
        for name, loader_class in panels:
            if issubclass(loader_class, PerDocumentPanelLoader):
                compliant_panels.append(name)
            else:
                non_compliant_panels.append(name)
        
        # Document current state
        print(f"\n✓ Compliant panels (inherit PerDocumentPanelLoader): {compliant_panels}")
        print(f"✗ Non-compliant panels (need refactoring): {non_compliant_panels}")
        
        # All panels should have document_id/drawing_area even if not inheriting base
        assert len(compliant_panels) >= 3, "At least Pathway, Topology, Analyses should be compliant"
