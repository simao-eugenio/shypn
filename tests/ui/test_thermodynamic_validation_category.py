"""
Tests for ThermodynamicValidationCategory (Report Panel GUI)

Tests the GTK3 widget for displaying thermodynamic validation results.
Note: These are unit tests that don't require a running GTK main loop.
"""

import pytest
from unittest.mock import MagicMock, Mock


class TestThermodynamicValidationCategory:
    """Test suite for ThermodynamicValidationCategory."""
    
    def test_category_initialization(self):
        """Test that category can be initialized."""
        # Import here to avoid GTK initialization issues
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        assert category.title == "THERMODYNAMIC VALIDATION"
        assert category.controller is None
        assert category.category_frame is not None
    
    def test_set_controller(self):
        """Test setting controller reference."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = None
        
        category.set_controller(mock_controller)
        
        assert category.controller is mock_controller
    
    def test_refresh_no_controller(self):
        """Test refresh with no controller."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        # Should not crash
        category.refresh()
        
        # Status should indicate no controller
        assert "no simulation controller" in category.status_label.get_label().lower()
    
    def test_refresh_no_validation(self):
        """Test refresh when no validation performed."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = None
        category.set_controller(mock_controller)
        
        # Status should indicate no validation
        assert "no validation" in category.status_label.get_label().lower()
    
    def test_refresh_with_valid_results(self):
        """Test refresh with valid transitions."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = {
            'summary': {
                'total': 2,
                'valid': 2,
                'warnings': 0,
                'violations': 0,
                'insufficient_data': 0,
            },
            'violations': [],
            'warnings': [],
            'valid': [
                {
                    'transition': 'R1',
                    'k_ratio': 2.0,
                    'k_eq': 2.1,
                    'deviation': 0.05,
                }
            ],
            'insufficient_data': [],
        }
        
        category.set_controller(mock_controller)
        
        # Status should show all valid
        assert "all" in category.status_label.get_label().lower()
        assert "valid" in category.status_label.get_label().lower()
    
    def test_refresh_with_violations(self):
        """Test refresh with violations."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = {
            'summary': {
                'total': 1,
                'valid': 0,
                'warnings': 0,
                'violations': 1,
                'insufficient_data': 0,
            },
            'violations': [
                {
                    'transition': 'R_BAD',
                    'k_ratio': 10.0,
                    'k_eq': 2.0,
                    'deviation': 5.0,
                    'message': 'Rate constants inconsistent',
                }
            ],
            'warnings': [],
            'valid': [],
            'insufficient_data': [],
        }
        
        category.set_controller(mock_controller)
        
        # Status should show violations
        assert "violation" in category.status_label.get_label().lower()
        
        # Violations label should show details
        violations_text = category.violations_label.get_text()
        assert "R_BAD" in violations_text
    
    def test_refresh_with_warnings(self):
        """Test refresh with warnings."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = {
            'summary': {
                'total': 1,
                'valid': 0,
                'warnings': 1,
                'violations': 0,
                'insufficient_data': 0,
            },
            'violations': [],
            'warnings': [
                {
                    'transition': 'R_WARN',
                    'k_ratio': 3.0,
                    'k_eq': 2.0,
                    'deviation': 1.5,
                    'message': 'Deviation above threshold',
                }
            ],
            'valid': [],
            'insufficient_data': [],
        }
        
        category.set_controller(mock_controller)
        
        # Status should show warnings
        assert "warning" in category.status_label.get_label().lower()
        
        # Warnings label should show details
        warnings_text = category.warnings_label.get_text()
        assert "R_WARN" in warnings_text
    
    def test_refresh_with_insufficient_data(self):
        """Test refresh with insufficient data."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        mock_controller = Mock()
        mock_controller.thermodynamic_results = {
            'summary': {
                'total': 1,
                'valid': 0,
                'warnings': 0,
                'violations': 0,
                'insufficient_data': 1,
            },
            'violations': [],
            'warnings': [],
            'valid': [],
            'insufficient_data': [
                {
                    'transition': 'R_INCOMPLETE',
                    'status': 'no_rate_constants',
                    'message': 'Missing k_f and k_r',
                }
            ],
        }
        
        category.set_controller(mock_controller)
        
        # Insufficient data label should show details
        insufficient_text = category.insufficient_label.get_text()
        assert "R_INCOMPLETE" in insufficient_text
    
    def test_get_widget(self):
        """Test getting the widget."""
        from shypn.ui.panels.report.thermodynamic_validation_category import ThermodynamicValidationCategory
        
        category = ThermodynamicValidationCategory()
        
        widget = category.get_widget()
        
        assert widget is not None
        assert widget == category.category_frame


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
