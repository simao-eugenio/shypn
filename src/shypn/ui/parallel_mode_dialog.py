"""
Parallel Mode Configuration Dialog

Provides UI for configuring parallel execution modes for topology analyzers.
Uses OOP principles with Gtk dialog and proper encapsulation.

Author: shypn
Date: 2025-01-XX
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from shypn.ui.topology_analysis_config import TopologyAnalysisConfig


class ParallelModeDialog(Gtk.Dialog):
    """
    Dialog for configuring parallel execution mode for topology analyzers.
    
    Provides options for:
    - Sequential (single-threaded)
    - Basic Parallel (work-stealing)
    - Maximal Parallel (concurrent independent transitions)
    - Worker count configuration
    """
    
    def __init__(self, parent, analyzer_name: str):
        """
        Initialize parallel mode configuration dialog.
        
        Args:
            parent: Parent window
            analyzer_name: Name of analyzer to configure
        """
        super().__init__(
            title=f"Parallel Mode: {analyzer_name}",
            parent=parent,
            flags=0
        )
        
        self.analyzer_name = analyzer_name
        self.config = TopologyAnalysisConfig.get_instance()
        
        # Add dialog buttons
        self.add_button("Cancel", Gtk.ResponseType.CANCEL)
        self.add_button("Apply", Gtk.ResponseType.OK)
        
        # Build UI
        self._build_ui()
        self._load_current_settings()
        
        self.set_default_size(400, 250)
    
    def _build_ui(self):
        """Build the dialog UI."""
        content_area = self.get_content_area()
        content_area.set_spacing(10)
        content_area.set_margin_start(10)
        content_area.set_margin_end(10)
        content_area.set_margin_top(10)
        content_area.set_margin_bottom(10)
        
        # Mode selection section
        mode_frame = Gtk.Frame(label="Execution Mode")
        mode_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        mode_box.set_margin_start(10)
        mode_box.set_margin_end(10)
        mode_box.set_margin_top(10)
        mode_box.set_margin_bottom(10)
        
        # Radio buttons for mode selection
        self.sequential_radio = Gtk.RadioButton.new_with_label_from_widget(
            None, "Sequential (Single-threaded)"
        )
        self.sequential_radio.connect("toggled", self._on_mode_changed)
        mode_box.pack_start(self.sequential_radio, False, False, 0)
        
        self.basic_parallel_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.sequential_radio, "Basic Parallel (Work-stealing)"
        )
        self.basic_parallel_radio.connect("toggled", self._on_mode_changed)
        mode_box.pack_start(self.basic_parallel_radio, False, False, 0)
        
        self.maximal_parallel_radio = Gtk.RadioButton.new_with_label_from_widget(
            self.sequential_radio, "Maximal Parallel (Concurrent independent transitions)"
        )
        self.maximal_parallel_radio.connect("toggled", self._on_mode_changed)
        mode_box.pack_start(self.maximal_parallel_radio, False, False, 0)
        
        mode_frame.add(mode_box)
        content_area.pack_start(mode_frame, False, False, 0)
        
        # Worker count section
        worker_frame = Gtk.Frame(label="Worker Configuration")
        worker_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        worker_box.set_margin_start(10)
        worker_box.set_margin_end(10)
        worker_box.set_margin_top(10)
        worker_box.set_margin_bottom(10)
        
        worker_label = Gtk.Label(label="Number of workers:")
        worker_box.pack_start(worker_label, False, False, 0)
        
        # Spinbutton for worker count (1-32, or 0 for auto)
        adjustment = Gtk.Adjustment(
            value=0,  # 0 means auto
            lower=0,
            upper=32,
            step_increment=1,
            page_increment=4,
            page_size=0
        )
        self.worker_spinbutton = Gtk.SpinButton()
        self.worker_spinbutton.set_adjustment(adjustment)
        self.worker_spinbutton.set_value(0)
        worker_box.pack_start(self.worker_spinbutton, False, False, 0)
        
        auto_label = Gtk.Label(label="(0 = auto)")
        auto_label.set_markup("<i><small>(0 = auto)</small></i>")
        worker_box.pack_start(auto_label, False, False, 0)
        
        worker_frame.add(worker_box)
        content_area.pack_start(worker_frame, False, False, 0)
        
        # Description label
        self.description_label = Gtk.Label()
        self.description_label.set_line_wrap(True)
        self.description_label.set_max_width_chars(50)
        content_area.pack_start(self.description_label, False, False, 10)
        
        self.show_all()
    
    def _load_current_settings(self):
        """Load current configuration for this analyzer."""
        parallel_mode = self.config.get_parallel_mode(self.analyzer_name)
        num_workers = self.config.get_num_workers(self.analyzer_name)
        
        # Set radio button
        if parallel_mode == 'maximal':
            self.maximal_parallel_radio.set_active(True)
        elif parallel_mode in [True, 'basic']:
            self.basic_parallel_radio.set_active(True)
        else:
            self.sequential_radio.set_active(True)
        
        # Set worker count
        if num_workers is None:
            self.worker_spinbutton.set_value(0)
        else:
            self.worker_spinbutton.set_value(num_workers)
    
    def _on_mode_changed(self, button):
        """Update description when mode changes."""
        if not button.get_active():
            return
        
        # Get analyzer-specific descriptions
        analyzer_type = self._get_analyzer_type()
        
        if button == self.sequential_radio:
            descriptions = {
                'state_space': "Sequential mode uses a single thread. Best for small networks or debugging.",
                'matrix': "Sequential mode. NumPy/BLAS still uses optimized libraries internally.",
                'enumeration': "Sequential subset checking. Best for small networks (<15 places).",
                'degree': "Sequential degree calculation. Fast even without parallelization."
            }
            self.description_label.set_text(descriptions.get(analyzer_type, descriptions['state_space']))
            self.worker_spinbutton.set_sensitive(False)
        elif button == self.basic_parallel_radio:
            descriptions = {
                'state_space': "Basic parallel mode uses work-stealing for load balancing. Good general-purpose parallel algorithm.",
                'matrix': "Uses NumPy/BLAS threading. Configure thread count for matrix operations.",
                'enumeration': "Partition-based parallel checking. Distributes subset enumeration across workers.",
                'degree': "Parallel node processing. Each node's degree computed independently."
            }
            self.description_label.set_text(descriptions.get(analyzer_type, descriptions['state_space']))
            self.worker_spinbutton.set_sensitive(True)
        elif button == self.maximal_parallel_radio:
            descriptions = {
                'state_space': "Maximal parallel mode fires multiple independent transitions concurrently. Best performance for networks with many independent transitions.",
                'matrix': "Maximum NumPy threading. Uses all CPU cores for matrix operations.",
                'enumeration': "Aggressive parallel enumeration. Best for medium networks (15-20 places).",
                'degree': "Maximum parallelization. All nodes processed simultaneously."
            }
            self.description_label.set_text(descriptions.get(analyzer_type, descriptions['state_space']))
            self.worker_spinbutton.set_sensitive(True)
    
    def _get_analyzer_type(self):
        """Get analyzer type category for context-specific descriptions."""
        state_space = ['reachability', 'boundedness', 'liveness', 'deadlocks']
        matrix = ['p_invariants', 't_invariants']
        enumeration = ['siphons', 'traps']
        degree = ['hubs']
        
        if self.analyzer_name in state_space:
            return 'state_space'
        elif self.analyzer_name in matrix:
            return 'matrix'
        elif self.analyzer_name in enumeration:
            return 'enumeration'
        elif self.analyzer_name in degree:
            return 'degree'
        return 'state_space'
    
    def get_selected_mode(self):
        """
        Get the selected parallel mode.
        
        Returns:
            str or bool: 'maximal', 'basic', or False (sequential)
        """
        if self.maximal_parallel_radio.get_active():
            return 'maximal'
        elif self.basic_parallel_radio.get_active():
            return 'basic'
        else:
            return False
    
    def get_worker_count(self):
        """
        Get the selected worker count.
        
        Returns:
            int or None: Number of workers, or None for auto
        """
        count = int(self.worker_spinbutton.get_value())
        return None if count == 0 else count
    
    def apply_settings(self):
        """Apply the selected settings to configuration."""
        mode = self.get_selected_mode()
        workers = self.get_worker_count()
        
        self.config.set_parallel_mode(self.analyzer_name, mode)
        self.config.set_num_workers(self.analyzer_name, workers)


class ParallelModeButton(Gtk.Button):
    """
    Toolbar button for opening parallel mode configuration.
    
    Provides quick access to parallel configuration dialog from topology panel.
    Wayland-safe: Programmatic GTK only, no UI files.
    """
    
    def __init__(self):
        """
        Initialize parallel mode button.
        """
        super().__init__(label="⚙ Parallel")
        self.connect("clicked", self._on_clicked)
        self.set_tooltip_text("Configure parallel execution mode")
    
    def _on_clicked(self, button):
        """Show parallel mode configuration selector."""
        # Show selection dialog for which analyzer to configure
        selection_dialog = Gtk.Dialog(
            title="Select Analyzer",
            parent=self.get_toplevel(),
            flags=0
        )
        selection_dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        selection_dialog.add_button("Configure", Gtk.ResponseType.OK)
        selection_dialog.set_default_size(350, 250)
        
        content = selection_dialog.get_content_area()
        content.set_spacing(10)
        content.set_margin_start(15)
        content.set_margin_end(15)
        content.set_margin_top(15)
        content.set_margin_bottom(15)
        
        label = Gtk.Label()
        label.set_markup("<b>Configure parallel execution:</b>")
        label.set_halign(Gtk.Align.START)
        content.pack_start(label, False, False, 0)
        
        # Radio buttons for analyzer selection (grouped by category)
        radio_group = None
        analyzers = [
            # Behavioral (state space)
            ('reachability', 'Reachability (State Space)'),
            ('boundedness', 'Boundedness (State Space)'),
            ('liveness', 'Liveness (State Space)'),
            ('deadlocks', 'Deadlocks (State Space)'),
            # Structural
            ('p_invariants', 'P-Invariants (Matrix)'),
            ('t_invariants', 'T-Invariants (Matrix)'),
            ('siphons', 'Siphons (Enumeration)'),
            # Network
            ('hubs', 'Network Hubs (Degree)')
        ]
        
        radio_buttons = {}
        for name, display in analyzers:
            radio = Gtk.RadioButton.new_with_label_from_widget(radio_group, display)
            if radio_group is None:
                radio_group = radio
                radio.set_active(True)
            radio_buttons[name] = radio
            content.pack_start(radio, False, False, 0)
        
        content.show_all()
        response = selection_dialog.run()
        
        if response == Gtk.ResponseType.OK:
            # Find selected analyzer
            selected = None
            for name, radio in radio_buttons.items():
                if radio.get_active():
                    selected = name
                    break
            
            selection_dialog.destroy()
            
            if selected:
                # Show configuration dialog for selected analyzer
                config_dialog = ParallelModeDialog(self.get_toplevel(), selected)
                config_response = config_dialog.run()
                
                if config_response == Gtk.ResponseType.OK:
                    config_dialog.apply_settings()
                
                config_dialog.destroy()
        else:
            selection_dialog.destroy()
