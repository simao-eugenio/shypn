"""Validation section for triggering thermodynamic validation.

Provides UI for running validation and displaying results summary.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import logging

from .base_section import ThermodynamicsSectionBase


logger = logging.getLogger(__name__)


class ValidationSection(ThermodynamicsSectionBase):
    """Thermodynamic validation trigger section.
    
    Provides:
    - Validate button (runs validation)
    - Progress indicator
    - Results summary (total, valid, warnings, violations)
    - Link to Report Panel for detailed results
    """
    
    def __init__(self, model_canvas=None):
        """Initialize validation section.
        
        Args:
            model_canvas: ModelCanvasManager instance (optional)
        """
        super().__init__(model_canvas)
        
        # Widgets (created in build_widget)
        self.validate_button = None
        self.progress_bar = None
        self.results_label = None
        self.status_label = None
        
        # Validation state
        self.validation_running = False
        self.last_results = None
        
        # Simulation controller (for storing results)
        self.simulation_controller = None
        
        # Report panel callback (for refreshing after validation)
        self.report_panel_refresh_callback = None
    
    def build_widget(self) -> Gtk.Widget:
        """Build validation section widget.
        
        Returns:
            Gtk.Frame: Validation controls frame
        """
        frame = Gtk.Frame()
        frame.set_label("Validation")
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        # Info text
        info_label = Gtk.Label()
        info_label.set_markup(
            "<small>Validates that kinetic rate constants are thermodynamically consistent.</small>"
        )
        info_label.set_line_wrap(True)
        info_label.set_halign(Gtk.Align.START)
        vbox.pack_start(info_label, False, False, 0)
        
        # Validate button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        self.validate_button = Gtk.Button(label="Run Validation")
        self.validate_button.connect("clicked", self._on_validate_clicked)
        button_box.pack_start(self.validate_button, False, False, 0)
        
        view_report_button = Gtk.Button(label="View Report")
        view_report_button.set_tooltip_text("Open Report Panel for detailed results")
        view_report_button.connect("clicked", self._on_view_report_clicked)
        button_box.pack_start(view_report_button, False, False, 0)
        
        vbox.pack_start(button_box, False, False, 0)
        
        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.set_no_show_all(True)  # Hidden by default
        vbox.pack_start(self.progress_bar, False, False, 0)
        
        # Status label
        self.status_label = Gtk.Label(label="Ready to validate")
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.get_style_context().add_class("dim-label")
        vbox.pack_start(self.status_label, False, False, 0)
        
        # Results summary
        self.results_label = Gtk.Label()
        self.results_label.set_markup("<small>No validation results yet</small>")
        self.results_label.set_line_wrap(True)
        self.results_label.set_halign(Gtk.Align.START)
        vbox.pack_start(self.results_label, False, False, 0)
        
        frame.add(vbox)
        return frame
    
    def refresh_data(self):
        """Refresh validation status from document."""
        # Get current document from canvas manager
        manager = self._get_canvas_manager()
        if not manager or not hasattr(manager, 'document'):
            self.status_label.set_text("")
            self.results_label.set_markup("")
            return
        
        document = manager.document
        if not document:
            self.status_label.set_text("")
            self.results_label.set_markup("")
            return
        
        # Update cached document reference
        self.document = document
        
        # Check if validation is enabled
        if hasattr(document, 'thermodynamic_settings'):
            enabled = document.thermodynamic_settings.get('enable_validation', True)
            if not enabled:
                self.status_label.set_text("Validation disabled in settings")
                self.validate_button.set_sensitive(False)
                return
        
        self.validate_button.set_sensitive(True)
        
        # Check for reversible transitions
        reversible_count = sum(
            1 for t in self.document.transitions
            if t.properties.get('is_reversible', False)
        ) if hasattr(self.document, 'transitions') else 0
        
        if reversible_count == 0:
            self.status_label.set_text("No reversible transitions to validate")
            self.results_label.set_markup("<small>Model has no reversible reactions</small>")
        else:
            self.status_label.set_text(f"Ready to validate {reversible_count} reversible reactions")
    
    def save_to_document(self):
        """Save validation results to document (if any)."""
        # Validation results are already stored in transition properties
        # by the validator, so nothing to save here
        pass
    
    def set_simulation_controller(self, controller):
        """Set simulation controller for storing validation results.
        
        Args:
            controller: SimulationController instance
        """
        self.simulation_controller = controller
    
    def set_report_panel_refresh_callback(self, callback):
        """Set callback to refresh Report Panel after validation.
        
        Args:
            callback: Function to call when validation completes
        """
        self.report_panel_refresh_callback = callback
    
    def _on_validate_clicked(self, button):
        """Handle validate button click."""
        # Get current document from canvas manager
        manager = self._get_canvas_manager()
        if not manager or not hasattr(manager, 'document') or not manager.document:
            self._show_error("No document loaded")
            return
        
        document = manager.document
        self.document = document  # Update cached reference
        
        if self.validation_running:
            return
        
        # Disable button and show progress
        self.validate_button.set_sensitive(False)
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("Initializing...")
        self.progress_bar.show()
        self.status_label.set_text("Validation in progress...")
        
        def run_validation():
            try:
                # Import validator
                from shypn.thermodynamics.simulation_integration import ThermodynamicSimulationValidator
                
                # Create validator with document settings
                validator = ThermodynamicSimulationValidator(document=self.document)
                
                # Get reversible transitions
                reversible_transitions = [
                    t for t in self.document.transitions
                    if t.properties.get('is_reversible', False)
                ]
                
                if not reversible_transitions:
                    GLib.idle_add(self._on_validation_complete, {
                        'total': 0,
                        'valid': 0,
                        'warnings': 0,
                        'violations': 0,
                        'message': 'No reversible transitions found'
                    })
                    return
                
                # Validate each transition
                results = {
                    'total': len(reversible_transitions),
                    'valid': 0,
                    'warnings': 0,
                    'violations': 0,
                    'details': []
                }
                
                for i, transition in enumerate(reversible_transitions):
                    # Update progress on main thread
                    progress = (i + 1) / len(reversible_transitions)
                    GLib.idle_add(self._update_progress, progress, f"Validating {i+1}/{len(reversible_transitions)}")
                    
                    # Get rate constants
                    k_forward = transition.properties.get('k_forward', 1.0)
                    k_reverse = transition.properties.get('k_reverse', 1.0)
                    
                    # Get reactants/products from compound mappings
                    reactants = {}
                    products = {}
                    
                    # Input places (reactants)
                    for arc in self.document.arcs:
                        if arc.target == transition and arc.source.id in self.document.compound_mappings:
                            compound_id = self.document.compound_mappings[arc.source.id]
                            stoich = arc.weight if hasattr(arc, 'weight') else 1
                            reactants[compound_id] = reactants.get(compound_id, 0) + stoich
                    
                    # Output places (products)
                    for arc in self.document.arcs:
                        if arc.source == transition and arc.target.id in self.document.compound_mappings:
                            compound_id = self.document.compound_mappings[arc.target.id]
                            stoich = arc.weight if hasattr(arc, 'weight') else 1
                            products[compound_id] = products.get(compound_id, 0) + stoich
                    
                    if not reactants or not products:
                        # Skip transitions without mapped compounds
                        continue
                    
                    # Validate
                    try:
                        validation = validator.validate_reversible_reaction(
                            reaction_id=transition.id,
                            k_forward=k_forward,
                            k_reverse=k_reverse,
                            reactants=reactants,
                            products=products
                        )
                        
                        if validation.is_valid:
                            results['valid'] += 1
                        else:
                            if 'warning' in validation.message.lower():
                                results['warnings'] += 1
                            else:
                                results['violations'] += 1
                        
                        results['details'].append({
                            'transition_id': transition.id,
                            'is_valid': validation.is_valid,
                            'message': validation.message
                        })
                    except Exception as e:
                        logger.warning(f"Validation failed for {transition.id}: {e}")
                
                GLib.idle_add(self._on_validation_complete, results)
                
            except Exception as e:
                GLib.idle_add(self._on_validation_error, str(e))
        
        # Run in background thread
        import threading
        thread = threading.Thread(target=run_validation)
        thread.daemon = True
        thread.start()
        self.validation_running = True
    
    def _update_progress(self, fraction: float, text: str):
        """Update progress bar (on main thread)."""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
        return False  # Remove from idle
    
    def _on_validation_complete(self, results: dict):
        """Handle validation completion (on main thread)."""
        self.validation_running = False
        self.last_results = results
        
        # Store results in simulation controller for Report Panel access
        if self.simulation_controller:
            # Parse details to categorize by validation status
            violations_list = []
            warnings_list = []
            valid_list = []
            
            logger.info(f"Processing {len(results.get('details', []))} validation details")
            
            for detail in results.get('details', []):
                transition_id = detail.get('transition_id')
                is_valid = detail.get('is_valid', False)
                message = detail.get('message', '')
                
                logger.info(f"  {transition_id}: valid={is_valid}, message={message[:50]}...")
                
                if is_valid:
                    valid_list.append({
                        'transition': transition_id,
                        'message': message
                    })
                else:
                    # Invalid reactions are violations (regardless of whether they "exceed" tolerance)
                    # Check if it's a soft warning vs hard violation based on message severity
                    if 'warning' in message.lower() and 'invalid' not in message.lower():
                        warnings_list.append({
                            'transition': transition_id,
                            'message': message
                        })
                    else:
                        violations_list.append({
                            'transition': transition_id,
                            'message': message
                        })
            
            logger.info(f"Categorized: {len(valid_list)} valid, {len(warnings_list)} warnings, {len(violations_list)} violations")
            
            # Include compound_mappings in results for Report Panel access
            compound_mappings = getattr(self.document, 'compound_mappings', {})
            
            self.simulation_controller.thermodynamic_results = {
                'summary': {
                    'total': results['total'],
                    'valid': results['valid'],
                    'warnings': results['warnings'],
                    'violations': results['violations'],
                },
                'violations': violations_list,
                'warnings': warnings_list,
                'valid': valid_list,
                'insufficient_data': [],
                'compound_mappings': compound_mappings,
            }
        
        # Hide progress bar
        self.progress_bar.hide()
        
        # Re-enable button
        self.validate_button.set_sensitive(True)
        self.validate_button.set_label("Run Validation")
        
        # Update status
        total = results['total']
        if total == 0:
            self.status_label.set_text(results.get('message', 'No reversible transitions found'))
            self.results_label.set_markup("<small>Model has no reversible reactions</small>")
        else:
            valid = results['valid']
            warnings = results['warnings']
            violations = results['violations']
            
            self.status_label.set_text(f"Validation complete: {total} reactions checked")
            
            # Build results summary with color coding
            summary_parts = []
            if valid > 0:
                summary_parts.append(f"<span foreground='green'><b>{valid} valid</b></span>")
            if warnings > 0:
                summary_parts.append(f"<span foreground='orange'><b>{warnings} warnings</b></span>")
            if violations > 0:
                summary_parts.append(f"<span foreground='red'><b>{violations} violations</b></span>")
            
            summary_text = " • ".join(summary_parts) if summary_parts else "No results"
            self.results_label.set_markup(summary_text)
            
            # Log results
            logger.info(f"Thermodynamic validation: {valid}/{total} valid, {warnings} warnings, {violations} violations")
        
        # Notify Report Panel to refresh (if callback is set)
        if self.report_panel_refresh_callback:
            try:
                self.report_panel_refresh_callback()
            except Exception as e:
                logger.warning(f"Failed to refresh report panel: {e}")
        
        return False  # Remove from idle
    
    def _on_validation_error(self, error_msg: str):
        """Handle validation error (on main thread)."""
        self.validation_running = False
        
        # Hide progress bar
        self.progress_bar.hide()
        
        # Re-enable button
        self.validate_button.set_sensitive(True)
        self.validate_button.set_label("Run Validation")
        
        # Show error
        self.status_label.set_text("Validation failed")
        self.results_label.set_markup(f"<span foreground='red'>Error: {error_msg}</span>")
        self._show_error(f"Validation failed: {error_msg}")
        
        return False  # Remove from idle
    
    def _on_view_report_clicked(self, button):
        """Handle view report button click."""
        # TODO: Switch to Report Panel and show thermodynamics category
        pass
