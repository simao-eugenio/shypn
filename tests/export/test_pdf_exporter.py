"""Tests for PDF export functionality.

Tests the PDFExporter class and BaseExporter functionality:
- Bounding box calculation
- Export validation
- Error handling
- Cairo PDF surface creation

Author: Simão Eugénio
Date: December 30, 2025
"""

import pytest
import cairo
from pathlib import Path
from unittest.mock import Mock, MagicMock
from shypn.export import PDFExporter, BaseExporter, ExportError


class MockPetriNetObject:
    """Mock Petri Net object for testing."""
    
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
    
    def get_bounding_box(self):
        """Return bounding box dict."""
        return {
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height
        }
    
    def render(self, cr, zoom=1.0):
        """Mock render method."""
        # Draw a simple rectangle for testing
        cr.rectangle(self.x, self.y, self.width, self.height)
        cr.stroke()


class MockManager:
    """Mock ModelCanvasManager for testing."""
    
    def __init__(self, objects=None):
        self.objects = objects or []
        self.filename = "test_model"
    
    def get_all_objects(self):
        """Return all objects."""
        return self.objects


class TestBaseExporter:
    """Test BaseExporter functionality."""
    
    def test_calculate_bounds_empty(self):
        """Test bounding box calculation with empty model."""
        exporter = PDFExporter()
        manager = MockManager(objects=[])
        bounds = exporter.calculate_bounds(manager)
        assert bounds is None
    
    def test_calculate_bounds_single_object(self):
        """Test bounding box with single object."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=100, y=100, width=80, height=80)
        manager = MockManager(objects=[obj])
        
        bounds = exporter.calculate_bounds(manager)
        assert bounds is not None
        assert bounds['min_x'] == 100
        assert bounds['min_y'] == 100
        assert bounds['max_x'] == 180  # 100 + 80
        assert bounds['max_y'] == 180  # 100 + 80
        assert bounds['width'] == 80
        assert bounds['height'] == 80
    
    def test_calculate_bounds_multiple_objects(self):
        """Test bounding box with multiple objects."""
        exporter = PDFExporter()
        objects = [
            MockPetriNetObject(x=50, y=50, width=100, height=100),   # 50-150, 50-150
            MockPetriNetObject(x=200, y=100, width=50, height=150),  # 200-250, 100-250
            MockPetriNetObject(x=100, y=200, width=80, height=40),   # 100-180, 200-240
        ]
        manager = MockManager(objects=objects)
        
        bounds = exporter.calculate_bounds(manager)
        assert bounds is not None
        assert bounds['min_x'] == 50
        assert bounds['min_y'] == 50
        assert bounds['max_x'] == 250
        assert bounds['max_y'] == 250
        assert bounds['width'] == 200  # 250 - 50
        assert bounds['height'] == 200  # 250 - 50
    
    def test_get_content_dimensions(self):
        """Test content dimension calculation with padding."""
        exporter = PDFExporter()
        bounds = {
            'min_x': 50,
            'min_y': 50,
            'max_x': 250,
            'max_y': 250
        }
        padding = 20.0
        
        width, height = exporter.get_content_dimensions(bounds, padding)
        assert width == 240.0  # 200 + 2*20
        assert height == 240.0  # 200 + 2*20
    
    def test_file_extension(self):
        """Test file extension methods."""
        exporter = PDFExporter()
        assert exporter.get_file_extension() == '.pdf'
        assert exporter.get_format_name() == 'PDF'


class TestPDFExporter:
    """Test PDFExporter specific functionality."""
    
    def test_export_empty_model_raises_error(self):
        """Test export fails with empty model."""
        exporter = PDFExporter()
        manager = MockManager(objects=[])
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export(manager, "/tmp/test.pdf")
        
        assert "empty model" in str(exc_info.value).lower()
    
    def test_export_no_manager_raises_error(self):
        """Test export fails with no manager."""
        exporter = PDFExporter()
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export(None, "/tmp/test.pdf")
        
        assert "no model manager" in str(exc_info.value).lower()
    
    def test_export_no_filepath_raises_error(self):
        """Test export fails with no filepath."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=100, y=100, width=80, height=80)
        manager = MockManager(objects=[obj])
        
        with pytest.raises(ExportError) as exc_info:
            exporter.export(manager, "")
        
        assert "no output filepath" in str(exc_info.value).lower()
    
    def test_export_adds_extension(self, tmp_path):
        """Test export adds .pdf extension if missing."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=100, y=100, width=80, height=80)
        manager = MockManager(objects=[obj])
        
        filepath = tmp_path / "test_model"
        success = exporter.export(manager, str(filepath))
        
        assert success
        assert Path(str(filepath) + ".pdf").exists()
    
    def test_export_creates_pdf_file(self, tmp_path):
        """Test export creates a valid PDF file."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=100, y=100, width=80, height=80)
        manager = MockManager(objects=[obj])
        
        filepath = tmp_path / "test_model.pdf"
        success = exporter.export(manager, str(filepath))
        
        assert success
        assert filepath.exists()
        assert filepath.stat().st_size > 0
        
        # Check PDF header (should start with %PDF)
        with open(filepath, 'rb') as f:
            header = f.read(4)
            assert header == b'%PDF'
    
    def test_export_with_padding(self, tmp_path):
        """Test export applies padding correctly."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=0, y=0, width=100, height=100)
        manager = MockManager(objects=[obj])
        
        filepath = tmp_path / "test_padded.pdf"
        success = exporter.export(manager, str(filepath), padding_percent=20.0)
        
        assert success
        assert filepath.exists()
    
    def test_export_multiple_objects(self, tmp_path):
        """Test export with multiple objects."""
        exporter = PDFExporter()
        objects = [
            MockPetriNetObject(x=50, y=50, width=100, height=100),
            MockPetriNetObject(x=200, y=100, width=50, height=150),
            MockPetriNetObject(x=100, y=200, width=80, height=40),
        ]
        manager = MockManager(objects=objects)
        
        filepath = tmp_path / "test_multiple.pdf"
        success = exporter.export(manager, str(filepath))
        
        assert success
        assert filepath.exists()
        assert filepath.stat().st_size > 0


class TestCairoIntegration:
    """Test Cairo PDF surface integration."""
    
    def test_cairo_pdf_surface_creation(self, tmp_path):
        """Test Cairo PDFSurface can be created and written."""
        filepath = tmp_path / "cairo_test.pdf"
        
        # Create PDF surface
        surface = cairo.PDFSurface(str(filepath), 200, 200)
        cr = cairo.Context(surface)
        
        # Draw simple content
        cr.set_source_rgb(1, 0, 0)
        cr.rectangle(50, 50, 100, 100)
        cr.fill()
        
        # Finalize
        surface.finish()
        
        assert filepath.exists()
        assert filepath.stat().st_size > 0
    
    def test_cairo_renders_correctly(self, tmp_path):
        """Test Cairo rendering produces valid PDF."""
        filepath = tmp_path / "render_test.pdf"
        
        # Create exporter and mock objects
        exporter = PDFExporter()
        objects = [
            MockPetriNetObject(x=100, y=100, width=80, height=80),
        ]
        manager = MockManager(objects=objects)
        
        # Export
        success = exporter.export(manager, str(filepath))
        
        assert success
        assert filepath.exists()
        
        # Verify it's a valid PDF
        with open(filepath, 'rb') as f:
            content = f.read()
            assert b'%PDF' in content
            assert b'%%EOF' in content


class TestErrorHandling:
    """Test error handling in export process."""
    
    def test_invalid_filepath_raises_error(self):
        """Test export with invalid filepath raises error."""
        exporter = PDFExporter()
        obj = MockPetriNetObject(x=100, y=100, width=80, height=80)
        manager = MockManager(objects=[obj])
        
        # Invalid path (directory doesn't exist)
        with pytest.raises(ExportError):
            exporter.export(manager, "/nonexistent/directory/test.pdf")
    
    def test_export_handles_render_exception(self, tmp_path):
        """Test export handles rendering exceptions gracefully."""
        exporter = PDFExporter()
        
        # Mock object that raises exception during render
        bad_obj = Mock()
        bad_obj.get_bounding_box.return_value = {
            'x': 0, 'y': 0, 'width': 100, 'height': 100
        }
        bad_obj.render.side_effect = Exception("Render failed")
        
        manager = MockManager(objects=[bad_obj])
        filepath = tmp_path / "error_test.pdf"
        
        with pytest.raises(ExportError):
            exporter.export(manager, str(filepath))


# Integration test (requires full environment)
class TestIntegration:
    """Integration tests requiring full Petri Net objects."""
    
    @pytest.mark.integration
    def test_export_with_real_objects(self, tmp_path):
        """Test export with real Petri Net objects (requires imports)."""
        try:
            from shypn.netobjs import Place, Transition, Arc
            
            # Create real objects
            p1 = Place(x=100, y=100, id="P1", name="Place1")
            t1 = Transition(x=200, y=100, id="T1", name="Transition1")
            
            # Mock manager with real objects
            manager = MockManager(objects=[p1, t1])
            
            # Export
            exporter = PDFExporter()
            filepath = tmp_path / "integration_test.pdf"
            success = exporter.export(manager, str(filepath))
            
            assert success
            assert filepath.exists()
            
        except ImportError:
            pytest.skip("Full Petri Net imports not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
