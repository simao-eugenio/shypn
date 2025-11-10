#!/usr/bin/env python3
"""Base class for topology analysis categories.

All topology categories inherit from BaseTopologyCategory and implement
the _build_content() method to populate their specific analysis views.

Each category contains:
1. Analysis Summary section (overview of all analyzers in category)
2. Individual analyzer expanders (one per analyzer)

Author: Simão Eugénio
Date: 2025-10-29
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.ui.category_frame import CategoryFrame


# ============================================================================
# ANALYZER PERFORMANCE CONFIGURATION
# ============================================================================

# Algorithm complexity and execution priority metadata
# Priority 1 = Fastest (O(n) to O(n²)), run first
# Priority 2 = Fast (O(n²) to O(n³)), run second
# Priority 3 = Moderate (O(n³) to exponential with limits), run third
# Priority 4 = Slow (exponential without limits), run last or manual only
#
# Timeout values prevent UI hanging when algorithms get stuck on complex models
ANALYZER_METADATA = {
    # FAST ALGORITHMS - Priority 1 (< 1 second typically)
    'hubs': {
        'priority': 1,
        'complexity': 'O(n+e)',
        'description': 'Linear - degree calculation',
        'safe_for_auto_run': True,
        'typical_time': '<0.5s',
        'timeout_seconds': 30  # Liberal timeout for safety
    },
    'paths': {
        'priority': 1,
        'complexity': 'O(n+e)',
        'description': 'Linear - graph traversal',
        'safe_for_auto_run': True,
        'typical_time': '<0.5s',
        'timeout_seconds': 30
    },
    'boundedness': {
        'priority': 1,
        'complexity': 'O(n)',
        'description': 'Linear - token counting',
        'safe_for_auto_run': True,
        'typical_time': '<0.5s',
        'timeout_seconds': 30
    },
    'fairness': {
        'priority': 1,
        'complexity': 'O(n+e)',
        'description': 'Linear - conflict analysis',
        'safe_for_auto_run': True,
        'typical_time': '<0.5s',
        'timeout_seconds': 30
    },
    
    # MODERATE ALGORITHMS - Priority 2 (1-3 seconds typically)
    'p_invariants': {
        'priority': 2,
        'complexity': 'O(n²m)',
        'description': 'Quadratic - matrix operations',
        'safe_for_auto_run': True,
        'typical_time': '1-2s',
        'timeout_seconds': 60
    },
    't_invariants': {
        'priority': 2,
        'complexity': 'O(nm²)',
        'description': 'Quadratic - matrix operations',
        'safe_for_auto_run': True,
        'typical_time': '1-2s',
        'timeout_seconds': 60
    },
    'cycles': {
        'priority': 2,
        'complexity': 'O((n+e)(c+1))',
        'description': 'Efficient cycle detection',
        'safe_for_auto_run': True,
        'typical_time': '1-3s',
        'timeout_seconds': 60
    },
    'dependency_coupling': {
        'priority': 2,
        'complexity': 'O(t²)',
        'description': 'Quadratic - transition pairs',
        'safe_for_auto_run': True,
        'typical_time': '1-3s',
        'timeout_seconds': 60
    },
    'regulatory_structure': {
        'priority': 2,
        'complexity': 'O(a)',
        'description': 'Linear - arc analysis',
        'safe_for_auto_run': True,
        'typical_time': '0.5-1s',
        'timeout_seconds': 30
    },
    
    # SLOW ALGORITHMS - Priority 3 (5-30 seconds, limited exploration)
    'reachability': {
        'priority': 3,
        'complexity': 'O(k^n)',
        'description': 'State explosion (bounded)',
        'safe_for_auto_run': False,
        'typical_time': '5-30s',
        'timeout_seconds': 90,  # 90s timeout
        'warning': '⚠️ <b>CAUTION:</b> State space exploration can take 30-90s on complex models.',
        'risk': 'HIGH'
    },
    'liveness': {
        'priority': 3,
        'complexity': 'O(k^n)',
        'description': 'Depends on reachability',
        'safe_for_auto_run': False,
        'typical_time': '5-30s',
        'timeout_seconds': 90,
        'warning': '⚠️ <b>CAUTION:</b> Can take 10-90s on complex models.',
        'risk': 'MEDIUM-HIGH'
    },
    'deadlocks': {
        'priority': 3,
        'complexity': 'O(2^n)',
        'description': 'Depends on siphon detection',
        'safe_for_auto_run': False,
        'typical_time': '5-30s',
        'timeout_seconds': 90,
        'warning': '⚠️ <b>CAUTION:</b> Can take 10-90s if siphon checking enabled.',
        'risk': 'MEDIUM-HIGH'
    },
    
    # VERY SLOW ALGORITHMS - Priority 4 (>60 seconds, exponential)
    'siphons': {
        'priority': 4,
        'complexity': 'O(2^n)',
        'description': 'Exponential - subset enumeration',
        'safe_for_auto_run': False,
        'typical_time': '>60s',
        'timeout_seconds': 120,  # 2 minutes max
        'warning': '⚠️ <b>CRITICAL:</b> Can take >60s or freeze on models with >25 places. Use on small models only.',
        'risk': 'CRITICAL'
    },
    'traps': {
        'priority': 4,
        'complexity': 'O(2^n)',
        'description': 'Exponential - subset enumeration',
        'safe_for_auto_run': False,
        'typical_time': '>60s',
        'timeout_seconds': 120,
        'warning': '⚠️ <b>CRITICAL:</b> Can take >60s or freeze on models with >25 places. Use on small models only.',
        'risk': 'CRITICAL'
    }
}

# Quick lookups for backward compatibility
SAFE_FOR_AUTO_RUN = {
    name for name, meta in ANALYZER_METADATA.items() 
    if meta.get('safe_for_auto_run', False)
}

DANGEROUS_ANALYZERS = {
    name: {
        'complexity': meta['complexity'],
        'warning': meta.get('warning', ''),
        'risk': meta.get('risk', 'UNKNOWN')
    }
    for name, meta in ANALYZER_METADATA.items()
    if not meta.get('safe_for_auto_run', False)
}


class BaseTopologyCategory:
    """Base class for topology analysis category controllers.
    
    Each category is responsible for:
    1. Building its content view (Summary + Analyzer expanders)
    2. Running analyzers when requested
    3. Displaying results in expanders
    4. Caching results per model/tab
    5. Showing spinners during analysis
    
    Subclasses must implement:
    - _build_content(): Create and return the content widget
    - _get_analyzers(): Return dict of {name: AnalyzerClass}
    - refresh(): Update analysis results when model changes
    """
    
    def __init__(self, title, model_canvas=None, expanded=False, use_grouped_table=False):
        """Initialize base topology category.
        
        Args:
            title: Category title displayed in expander
            model_canvas: ModelCanvas instance (optional)
            expanded: Whether category starts expanded
            use_grouped_table: If True, use single grouped table instead of expanders
        """
        self.title = title
        self.model_canvas = model_canvas
        self.expanded = expanded
        self.use_grouped_table = use_grouped_table
        self.parent_panel = None  # Will be set by TopologyPanel
        
        # Analyzer instances (lazy initialized)
        self.analyzers = {}
        
        # Results cache per drawing_area (tab)
        # Format: {drawing_area: {analyzer_name: result}}
        self.results_cache = {}
        
        # Track which analyzers are currently running
        self.analyzing = set()
        
        # Track analyzer execution times and timeouts
        self.analyzer_start_times = {}  # {analyzer_name: timestamp}
        self.analyzer_timeouts = {}     # {analyzer_name: GLib timeout_id}
        
        # Track which expanders have been analyzed (per drawing area)
        # Format: {drawing_area: set(analyzer_names)}
        self.analyzed = {}
        
        # Widgets
        self.summary_label = None
        self.analyzer_expanders = {}  # {analyzer_name: Gtk.Expander}
        self.analyzer_labels = {}     # {analyzer_name: Gtk.Label}
        self.analyzer_containers = {} # {analyzer_name: Gtk.Box} - container for label or table
        self.spinner_boxes = {}       # {analyzer_name: Gtk.Box with spinner}
        
        # Grouped table widgets (when use_grouped_table=True)
        self.grouped_table_store = None  # Gtk.ListStore
        self.grouped_table_view = None   # Gtk.TreeView
        self.run_all_button = None       # Gtk.Button
        self.grouped_spinner = None      # Gtk.Spinner for "Run All"
        
        # Create category frame
        self.category_frame = CategoryFrame(
            title=self.title,
            expanded=self.expanded
        )
        
        # Build content (implemented by subclasses)
        content_widget = self._build_content()
        if content_widget:
            content_widget.show_all()
            self.category_frame.set_content(content_widget)
    
    def get_knowledge_base(self):
        """Get the knowledge base for the current model.
        
        Returns:
            ModelKnowledgeBase or None: Knowledge base instance
        """
        if self.parent_panel and hasattr(self.parent_panel, 'get_knowledge_base'):
            return self.parent_panel.get_knowledge_base()
        elif self.model_canvas and hasattr(self.model_canvas, 'get_current_knowledge_base'):
            return self.model_canvas.get_current_knowledge_base()
        return None
    
    def _build_content(self):
        """Build and return the content widget.
        
        Must be implemented by subclasses.
        
        Returns:
            Gtk.Widget: The content to display in this category
        """
        raise NotImplementedError("Subclasses must implement _build_content()")
    
    def _get_analyzers(self):
        """Get dict of analyzer name -> AnalyzerClass.
        
        Must be implemented by subclasses.
        
        Returns:
            dict: {analyzer_name: AnalyzerClass}
        """
        raise NotImplementedError("Subclasses must implement _get_analyzers()")
    
    def _build_summary_section(self):
        """Build the Analysis Summary section.
        
        Returns:
            Gtk.Box: Box containing summary label
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Summary header
        header = Gtk.Label()
        header.set_markup("<b>Analysis Summary</b>")
        header.set_xalign(0)
        box.pack_start(header, False, False, 0)
        
        # Summary content
        self.summary_label = Gtk.Label()
        self.summary_label.set_markup("<i>Not yet analyzed. Expand an analyzer below to run analysis.</i>")
        self.summary_label.set_xalign(0)
        self.summary_label.set_line_wrap(True)
        box.pack_start(self.summary_label, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        box.pack_start(separator, False, False, 6)
        
        return box
    
    def _build_analyzer_expanders(self):
        """Build Gtk.Expander sub-expanders for each analyzer (indented with >).
        
        Returns:
            Gtk.Box: Box containing all analyzer expanders
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        analyzers = self._get_analyzers()
        
        for analyzer_name, analyzer_class in analyzers.items():
            # Create indented Gtk.Expander (like Report Panel sub-categories)
            analyzer_expander = Gtk.Expander(
                label=self._format_analyzer_title(analyzer_name)
            )
            analyzer_expander.set_expanded(False)
            analyzer_expander.set_margin_start(20)  # Indent to show hierarchy
            
            # Create content with result label and spinner
            content = self._build_analyzer_content(analyzer_name)
            analyzer_expander.add(content)
            
            # Connect expansion event
            analyzer_expander.connect(
                'activate',
                lambda w, name=analyzer_name: self._on_analyzer_expand(name)
            )
            
            self.analyzer_expanders[analyzer_name] = analyzer_expander
            box.pack_start(analyzer_expander, False, False, 0)
        
        return box
    
    def _build_analyzer_content(self, analyzer_name):
        """Build content area for an analyzer expander.
        
        Args:
            analyzer_name: Name of the analyzer
        
        Returns:
            Gtk.Box: Box with result table/label and spinner
        """
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Spinner box (hidden initially)
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        spinner = Gtk.Spinner()
        spinner.set_size_request(16, 16)
        spinner_box.pack_start(spinner, False, False, 0)
        
        spinner_label = Gtk.Label(label="Analyzing...")
        spinner_box.pack_start(spinner_label, False, False, 0)
        spinner_box.set_no_show_all(True)
        spinner_box.hide()
        
        self.spinner_boxes[analyzer_name] = (spinner_box, spinner)
        box.pack_start(spinner_box, False, False, 0)
        
        # Scrolled window for results
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(100)
        scrolled.set_max_content_height(400)
        
        # Create container that will hold either table or label
        result_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Default: Result label (will be replaced with table if needed)
        result_label = Gtk.Label()
        
        # Check if this is a dangerous analyzer that needs a warning
        initial_text = "<i>Not yet analyzed.</i>"
        if analyzer_name in DANGEROUS_ANALYZERS:
            warning_info = DANGEROUS_ANALYZERS[analyzer_name]
            warning_text = warning_info['warning']
            complexity = warning_info['complexity']
            
            initial_text = f"<i>Not yet analyzed.</i>\n\n{warning_text}\n\n<small><i>Complexity: {complexity}</i></small>"
        
        result_label.set_markup(initial_text)
        result_label.set_xalign(0)
        result_label.set_yalign(0)
        result_label.set_line_wrap(True)
        result_label.set_selectable(True)
        result_label.set_margin_start(6)
        result_label.set_margin_end(6)
        result_label.set_margin_top(6)
        result_label.set_margin_bottom(6)
        
        result_container.pack_start(result_label, True, True, 0)
        
        self.analyzer_labels[analyzer_name] = result_label
        self.analyzer_containers[analyzer_name] = result_container
        scrolled.add(result_container)
        
        box.pack_start(scrolled, True, True, 0)
        
        return box
    
    def _format_analyzer_title(self, analyzer_name):
        """Format analyzer name to title case.
        
        Args:
            analyzer_name: Analyzer name (e.g., 'p_invariants')
        
        Returns:
            str: Formatted title (e.g., 'P-Invariants')
        """
        # Handle special cases
        special_cases = {
            'p_invariants': 'P-Invariants',
            't_invariants': 'T-Invariants',
        }
        
        if analyzer_name in special_cases:
            return special_cases[analyzer_name]
        
        # Default: title case with spaces
        return analyzer_name.replace('_', ' ').title()
    
    def _get_analyzer_metadata_text(self, analyzer_name):
        """Get human-readable metadata text for an analyzer.
        
        Args:
            analyzer_name: Name of analyzer
            
        Returns:
            str: Formatted metadata (complexity, time, priority)
        """
        metadata = ANALYZER_METADATA.get(analyzer_name, {})
        
        if not metadata:
            return "No metadata available"
        
        parts = []
        
        # Priority
        priority = metadata.get('priority', '?')
        priority_label = {
            1: 'Priority 1 (Fastest)',
            2: 'Priority 2 (Fast)',
            3: 'Priority 3 (Moderate)',
            4: 'Priority 4 (Slow)'
        }.get(priority, f'Priority {priority}')
        parts.append(f"🚀 {priority_label}")
        
        # Complexity
        complexity = metadata.get('complexity', 'Unknown')
        parts.append(f"📊 Complexity: {complexity}")
        
        # Description
        description = metadata.get('description', '')
        if description:
            parts.append(f"📝 {description}")
        
        # Typical time
        typical_time = metadata.get('typical_time', '')
        if typical_time:
            parts.append(f"⏱️ Typical: {typical_time}")
        
        # Warning if exists
        warning = metadata.get('warning', '')
        if warning:
            parts.append(f"\n{warning}")
        
        return '\n'.join(parts)
    
    # ========================================================================
    # GROUPED TABLE MODE METHODS
    # ========================================================================
    
    def _build_grouped_table(self):
        """Build single table combining all analyzers in category.
        
        This is an alternative to individual expanders - shows all results
        in one sortable table with a Type column.
        
        Returns:
            Gtk.Box: Box with toolbar, table, and "Run All" button
        """
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        
        # Toolbar with Run All button and spinner
        toolbar = self._build_grouped_toolbar()
        main_box.pack_start(toolbar, False, False, 0)
        
        # Scrolled window with table
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_vexpand(True)
        
        # Create table
        table = self._create_grouped_table()
        scrolled.add(table)
        
        main_box.pack_start(scrolled, True, True, 0)
        
        return main_box
    
    def _build_grouped_toolbar(self):
        """Build toolbar for grouped table mode.
        
        Returns:
            Gtk.Box: Toolbar with buttons
        """
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        # Run All button
        self.run_all_button = Gtk.Button(label="Run All Analyzers")
        self.run_all_button.connect('clicked', self._on_run_all_clicked)
        self.run_all_button.set_tooltip_text(
            "Run all safe analyzers in priority order:\n"
            "• Priority 1 (Fastest): O(n) algorithms run first\n"
            "• Priority 2 (Fast): O(n²) algorithms run second\n"
            "• Priority 3-4: Slower algorithms skipped (run manually)\n\n"
            "Fast algorithms display results immediately while slower ones complete."
        )
        toolbar.pack_start(self.run_all_button, False, False, 0)
        
        # Spinner (hidden initially)
        self.grouped_spinner = Gtk.Spinner()
        self.grouped_spinner.set_size_request(16, 16)
        self.grouped_spinner.set_no_show_all(True)
        self.grouped_spinner.hide()
        toolbar.pack_start(self.grouped_spinner, False, False, 0)
        
        # Status label
        self.grouped_status_label = Gtk.Label()
        self.grouped_status_label.set_xalign(0)
        self.grouped_status_label.set_markup("<i>No analyses run yet</i>")
        toolbar.pack_start(self.grouped_status_label, False, False, 6)
        
        return toolbar
    
    def _create_grouped_table(self):
        """Create TreeView table for grouped results.
        
        Returns:
            Gtk.TreeView: Table widget
        """
        # Get column definitions from subclass
        columns = self._define_table_columns()
        
        # Create ListStore with column types
        column_types = [col_type for _, col_type in columns]
        self.grouped_table_store = Gtk.ListStore(*column_types)
        
        # Create TreeView
        self.grouped_table_view = Gtk.TreeView(model=self.grouped_table_store)
        self.grouped_table_view.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Add columns
        for i, (col_name, col_type) in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_name, renderer, text=i)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            
            # Set alignment based on type
            if col_type in (int, float):
                renderer.set_property('xalign', 1.0)  # Right-align numbers
            
            self.grouped_table_view.append_column(column)
        
        return self.grouped_table_view
    
    def _define_table_columns(self):
        """Define columns for grouped table.
        
        Must be implemented by subclasses that use grouped tables.
        
        Returns:
            list: List of (column_name, column_type) tuples
                  Example: [('Type', str), ('Name', str), ('Size', int)]
        """
        # Default implementation - subclasses should override
        return [
            ('Type', str),
            ('Name', str),
            ('Value', str),
        ]
    
    def _on_run_all_clicked(self, button):
        """Handle Run All button click with prioritized execution.
        
        Fast algorithms run first to provide immediate feedback,
        slower algorithms run last to prevent blocking.
        
        Args:
            button: Button that was clicked
        """
        print(f"[{self.__class__.__name__}] Run All clicked")
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            print(f"[{self.__class__.__name__}] No drawing area!")
            return
        
        print(f"[{self.__class__.__name__}] Drawing area: {drawing_area}")
        
        # Disable button and show spinner
        self.run_all_button.set_sensitive(False)
        self.grouped_spinner.show()
        self.grouped_spinner.start()
        self.grouped_status_label.set_markup("<i>Running analyses...</i>")
        
        # Clear table
        if hasattr(self, 'grouped_table_store') and self.grouped_table_store:
            self.grouped_table_store.clear()
        
        # Get all analyzers and sort by priority (Priority 1 = fastest)
        analyzers = self._get_analyzers()
        print(f"[{self.__class__.__name__}] Got {len(analyzers)} analyzers: {list(analyzers.keys())}")
        analyzer_list = []
        
        for analyzer_name in analyzers.keys():
            # Skip dangerous analyzers unless already analyzed
            if analyzer_name in DANGEROUS_ANALYZERS:
                analyzed_set = self.analyzed.get(drawing_area, set())
                if analyzer_name not in analyzed_set:
                    # Skip dangerous analyzers in "Run All"
                    continue
            
            # Get priority from metadata (default to 5 if not found)
            metadata = ANALYZER_METADATA.get(analyzer_name, {})
            priority = metadata.get('priority', 5)
            analyzer_list.append((priority, analyzer_name))
        
        # Sort by priority (ascending: 1, 2, 3, 4...)
        analyzer_list.sort(key=lambda x: x[0])
        
        print(f"[{self.__class__.__name__}] Sorted analyzer list ({len(analyzer_list)} to run):")
        for priority, name in analyzer_list:
            print(f"  Priority {priority}: {name}")
        
        # Run analyzers in priority order with staggered delays
        # This ensures fast algorithms complete and display results first
        for i, (priority, analyzer_name) in enumerate(analyzer_list):
            # Stagger execution: Priority 1 runs immediately, Priority 2 after 100ms, etc.
            delay_ms = i * 50  # 50ms between each analyzer start
            GLib.timeout_add(
                delay_ms,
                self._run_analyzer_for_grouped_table,
                analyzer_name,
                drawing_area
            )
    
    def _run_analyzer_for_grouped_table(self, analyzer_name, drawing_area):
        """Run analyzer and update grouped table with results.
        
        Args:
            analyzer_name: Name of analyzer to run
            drawing_area: Current drawing area
        """
        print(f"[{self.__class__.__name__}] Running analyzer: {analyzer_name}")
        
        if analyzer_name in self.analyzing:
            print(f"[{self.__class__.__name__}] {analyzer_name} already analyzing, skipping")
            return False  # Already analyzing, stop GLib.timeout_add from repeating
        
        self.analyzing.add(analyzer_name)
        print(f"[{self.__class__.__name__}] Added {analyzer_name} to analyzing set")
        
        # Record start time
        import time
        self.analyzer_start_times[analyzer_name] = time.time()
        
        # Setup timeout watchdog
        metadata = ANALYZER_METADATA.get(analyzer_name, {})
        timeout_seconds = metadata.get('timeout_seconds', 60)  # Default 60s
        
        def on_timeout():
            """Called when analyzer exceeds timeout."""
            if analyzer_name in self.analyzing:
                # Analyzer still running after timeout
                self.analyzing.discard(analyzer_name)
                
                # Show timeout message in UI
                GLib.idle_add(self._show_timeout_message, analyzer_name, timeout_seconds)
                GLib.idle_add(self._check_grouped_analysis_complete)
            
            # Return False to stop timeout from repeating
            return False
        
        # Start timeout watchdog (runs on GTK main thread)
        timeout_id = GLib.timeout_add_seconds(timeout_seconds, on_timeout)
        self.analyzer_timeouts[analyzer_name] = timeout_id
        
        # Notify subclasses that analyzer is starting (hook for UI updates)
        if hasattr(self, '_on_analyzer_start'):
            GLib.idle_add(self._on_analyzer_start, analyzer_name)
        
        # Extract model on main thread
        try:
            manager = None
            if self.model_canvas:
                if hasattr(self.model_canvas, 'get_canvas_manager'):
                    manager = self.model_canvas.get_canvas_manager(drawing_area)
                elif hasattr(self.model_canvas, 'canvas_managers'):
                    manager = self.model_canvas.canvas_managers.get(drawing_area)
            
            if not manager:
                self.analyzing.discard(analyzer_name)
                return False  # Stop GLib.timeout_add from repeating
            
            if hasattr(manager, 'to_document_model'):
                model = manager.to_document_model()
            else:
                self.analyzing.discard(analyzer_name)
                return False  # Stop GLib.timeout_add from repeating
            
            if not model or model.is_empty():
                self.analyzing.discard(analyzer_name)
                return False  # Stop GLib.timeout_add from repeating
            
            analyzers = self._get_analyzers()
            analyzer_class = analyzers.get(analyzer_name)
            if not analyzer_class:
                self.analyzing.discard(analyzer_name)
                return False  # Stop GLib.timeout_add from repeating
                
        except Exception as e:
            self.analyzing.discard(analyzer_name)
            return False  # Stop GLib.timeout_add from repeating
        
        # Run analysis in background thread
        def analyze_thread():
            try:
                analyzer = analyzer_class(model)
                result = analyzer.analyze()
                
                # Cache result
                if drawing_area not in self.results_cache:
                    self.results_cache[drawing_area] = {}
                self.results_cache[drawing_area][analyzer_name] = result
                
                # Mark as analyzed
                if drawing_area not in self.analyzed:
                    self.analyzed[drawing_area] = set()
                self.analyzed[drawing_area].add(analyzer_name)
                
                # Update Knowledge Base (on GTK main thread to ensure thread safety)
                GLib.idle_add(self._update_knowledge_base, analyzer_name, result)
                
                # Update table (on GTK main thread)
                GLib.idle_add(self._add_result_to_grouped_table, analyzer_name, result)
                
            except Exception as e:
                print(f"Error analyzing {analyzer_name}: {e}")
                # Show error in UI
                GLib.idle_add(self._show_error_message, analyzer_name, str(e))
            finally:
                # Cancel timeout if analyzer completed
                if analyzer_name in self.analyzer_timeouts:
                    GLib.source_remove(self.analyzer_timeouts[analyzer_name])
                    del self.analyzer_timeouts[analyzer_name]
                
                self.analyzing.discard(analyzer_name)
                # Check if all done
                GLib.idle_add(self._check_grouped_analysis_complete)
        
        import threading
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()
        
        # Return False to prevent GLib.timeout_add from calling this again
        return False
    
    def _update_knowledge_base(self, analyzer_name, result):
        """Update knowledge base with analysis results.
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result
            
        Returns:
            False: Prevent GLib.idle_add from repeating
        """
        try:
            kb = self.get_knowledge_base()
            if not kb:
                print(f"[KB UPDATE] ⚠️ No KB available for {analyzer_name} - get_knowledge_base() returned None")
                print(f"  - self.parent_panel: {self.parent_panel}")
                print(f"  - self.model_canvas: {self.model_canvas}")
                if self.model_canvas:
                    print(f"  - has get_current_knowledge_base: {hasattr(self.model_canvas, 'get_current_knowledge_base')}")
                return False  # No KB available
            
            print(f"[KB UPDATE] Processing {analyzer_name}...")
            
            # Handle AnalysisResult objects
            if hasattr(result, 'success'):
                if not result.success:
                    print(f"[KB UPDATE] ⚠️ {analyzer_name} analysis failed, skipping KB update")
                    return False  # Skip failed analyses
                result_data = result.data if hasattr(result, 'data') else {}
            else:
                result_data = result
            
            # Import dataclasses for conversion
            from shypn.viability.knowledge.data_structures import (
                PInvariant, TInvariant, Siphon
            )
            
            # Route to appropriate KB update method based on analyzer type
            if analyzer_name == 'p_invariants':
                # Result format: {'p_invariants': [{'vector': [1, 0, 1], 'places': ['P1', 'P3'], ...}]}
                invariants_raw = result_data.get('p_invariants', [])
                if invariants_raw:
                    # Convert to PInvariant objects
                    invariants = []
                    for inv_data in invariants_raw:
                        inv = PInvariant(
                            vector=inv_data.get('vector', []),
                            place_ids=inv_data.get('places', inv_data.get('place_ids', [])),
                            conserved_value=inv_data.get('conserved_value', 0),
                            biological_meaning=inv_data.get('meaning', None)
                        )
                        invariants.append(inv)
                    kb.update_p_invariants(invariants)
                    print(f"✓ Knowledge Base updated: {len(invariants)} P-invariants")
            
            elif analyzer_name == 't_invariants':
                # Result format: {'t_invariants': [{'vector': [1, 2], 'transitions': ['T1', 'T2'], ...}]}
                invariants_raw = result_data.get('t_invariants', [])
                if invariants_raw:
                    # Convert to TInvariant objects
                    invariants = []
                    for inv_data in invariants_raw:
                        inv = TInvariant(
                            vector=inv_data.get('vector', []),
                            transition_ids=inv_data.get('transitions', inv_data.get('transition_ids', [])),
                            biological_meaning=inv_data.get('meaning', None)
                        )
                        invariants.append(inv)
                    kb.update_t_invariants(invariants)
                    print(f"✓ Knowledge Base updated: {len(invariants)} T-invariants")
            
            elif analyzer_name == 'liveness':
                # Result format: {'liveness_levels': {tid: 'L1', tid2: 'L2', ...}}
                liveness_levels = result_data.get('liveness_levels', {})
                if liveness_levels:
                    # Already in correct format: dict mapping tid -> level string
                    kb.update_liveness(liveness_levels)
                    print(f"✓ Knowledge Base updated: Liveness for {len(liveness_levels)} transitions")
            
            elif analyzer_name == 'siphons':
                # Result format: {'siphons': [{place_ids: [...], is_minimal: bool, ...}]}
                siphons_raw = result_data.get('siphons', [])
                if siphons_raw:
                    # Convert to Siphon objects
                    siphons = []
                    for siphon_data in siphons_raw:
                        siphon = Siphon(
                            place_ids=siphon_data.get('place_ids', siphon_data.get('places', [])),
                            is_minimal=siphon_data.get('is_minimal', True),
                            suggested_source=None,
                            suggested_rate=None
                        )
                        siphons.append(siphon)
                    kb.update_siphons_traps(siphons, [])  # Only siphons for now
                    print(f"✓ Knowledge Base updated: {len(siphons)} siphons")
            
            elif analyzer_name == 'traps':
                # Result format: {'traps': [{place_ids: [...], is_minimal: bool, ...}]}
                traps_raw = result_data.get('traps', [])
                if traps_raw:
                    # Convert to Siphon objects (traps use same structure)
                    traps = []
                    for trap_data in traps_raw:
                        trap = Siphon(
                            place_ids=trap_data.get('place_ids', trap_data.get('places', [])),
                            is_minimal=trap_data.get('is_minimal', True),
                            suggested_source=None,
                            suggested_rate=None
                        )
                        traps.append(trap)
                    kb.update_siphons_traps([], traps)  # Only traps for now
                    print(f"✓ Knowledge Base updated: {len(traps)} traps")
            
            elif analyzer_name == 'deadlocks':
                # Result format: {'deadlock_states': [...], 'has_deadlocks': bool}
                deadlock_states = result_data.get('deadlock_states', [])
                has_deadlocks = result_data.get('has_deadlocks', False)
                if deadlock_states or has_deadlocks:
                    kb.update_deadlocks(deadlock_states)
                    print(f"✓ Knowledge Base updated: Deadlocks ({len(deadlock_states)} states)")
            
            elif analyzer_name == 'boundedness':
                # Result format: {'bounded': bool, 'unbounded_places': [...], 'bounds': {...}}
                bounds = result_data.get('bounds', {})
                if not bounds and result_data.get('bounded', True):
                    # All places bounded to default (e.g., 1)
                    bounds = {}  # Empty means all bounded
                kb.update_boundedness(bounds)
                print(f"✓ Knowledge Base updated: Boundedness")
            
        except Exception as e:
            import traceback
            print(f"Warning: Failed to update Knowledge Base for {analyzer_name}: {e}")
            traceback.print_exc()
        
        return False  # Don't repeat
    
    def _add_result_to_grouped_table(self, analyzer_name, result):
        """Add analyzer result to grouped table.
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result
        """
        # Handle AnalysisResult objects
        if hasattr(result, 'success'):
            if not result.success:
                return  # Skip failed analyses
            result_data = result.data if hasattr(result, 'data') else {}
        else:
            result_data = result
        
        # Format result as table row(s) - subclass implements this
        rows = self._format_analyzer_row(analyzer_name, result_data)
        
        # Add rows to table
        if rows:
            for row in rows:
                self.grouped_table_store.append(row)
    
    def _show_timeout_message(self, analyzer_name, timeout_seconds):
        """Show timeout message for an analyzer that exceeded time limit.
        
        Args:
            analyzer_name: Name of analyzer that timed out
            timeout_seconds: Timeout value that was exceeded
        """
        metadata = ANALYZER_METADATA.get(analyzer_name, {})
        complexity = metadata.get('complexity', 'Unknown')
        
        # Format timeout message
        timeout_row = self._format_timeout_row(analyzer_name, timeout_seconds, complexity)
        
        if timeout_row:
            if isinstance(timeout_row, list):
                for row in timeout_row:
                    self.grouped_table_store.append(row)
            else:
                self.grouped_table_store.append(timeout_row)
    
    def _show_error_message(self, analyzer_name, error_message):
        """Show error message for an analyzer that failed.
        
        Args:
            analyzer_name: Name of analyzer that failed
            error_message: Error message
        """
        error_row = self._format_error_row(analyzer_name, error_message)
        
        if error_row:
            if isinstance(error_row, list):
                for row in error_row:
                    self.grouped_table_store.append(row)
            else:
                self.grouped_table_store.append(error_row)
    
    def _format_timeout_row(self, analyzer_name, timeout_seconds, complexity):
        """Format timeout message as table row.
        
        Subclasses can override for custom timeout display.
        
        Args:
            analyzer_name: Name of analyzer
            timeout_seconds: Timeout value
            complexity: Algorithm complexity
            
        Returns:
            tuple or list: Row(s) for table
        """
        # Default implementation
        title = self._format_analyzer_title(analyzer_name)
        message = f"⏱️ Timeout ({timeout_seconds}s) - Model too complex for {complexity} algorithm"
        return (title, message, '⚠️ TIMEOUT')
    
    def _format_error_row(self, analyzer_name, error_message):
        """Format error message as table row.
        
        Subclasses can override for custom error display.
        
        Args:
            analyzer_name: Name of analyzer
            error_message: Error message
            
        Returns:
            tuple or list: Row(s) for table
        """
        # Default implementation
        title = self._format_analyzer_title(analyzer_name)
        message = f"❌ Error: {error_message[:100]}"
        return (title, message, '⚠️ ERROR')
    
    def _format_analyzer_row(self, analyzer_name, result):
        """Format analyzer result as table row(s).
        
        Must be implemented by subclasses that use grouped tables.
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result data (dict or structured data)
        
        Returns:
            list: List of row tuples matching table columns
                  Example: [('P-Invariant', 'P_Inv_1', 5), ...]
        """
        # Default implementation - subclasses should override
        return [(analyzer_name, str(result), '')]
    
    def _check_grouped_analysis_complete(self):
        """Check if all analyses are complete and update UI with priority info.
        """
        if not self.analyzing:
            # All done
            self.grouped_spinner.stop()
            self.grouped_spinner.hide()
            self.run_all_button.set_sensitive(True)
            
            # Count results only if table store exists
            row_count = len(self.grouped_table_store) if self.grouped_table_store else 0
            self.grouped_status_label.set_markup(
                f"<i>Analysis complete: {row_count} results (prioritized execution)</i>"
            )
        else:
            # Update progress - show which analyzers are still running
            running_names = [name.replace('_', ' ').title() for name in self.analyzing]
            if len(running_names) == 1:
                status = f"Running: {running_names[0]}..."
            elif len(running_names) <= 3:
                status = f"Running: {', '.join(running_names)}..."
            else:
                status = f"Running {len(running_names)} analyses..."
            
            self.grouped_status_label.set_markup(f"<i>{status}</i>")
        
        # Return False to prevent GLib.idle_add from calling again
        return False
    
    # ========================================================================
    # END GROUPED TABLE MODE METHODS
    # ========================================================================
    
    def _on_analyzer_expand(self, analyzer_name):
        """Handle analyzer expander expansion.
        
        Args:
            analyzer_name: Name of the analyzer being expanded
        """
        expander = self.analyzer_expanders.get(analyzer_name)
        if not expander:
            return True
        
        # Check if expander is being expanded (will be expanded after this event)
        # Note: 'activate' signal is emitted before the expansion state changes
        is_expanding = not expander.get_expanded()
        
        # If expanding and not yet analyzed, run analysis
        if is_expanding:
            drawing_area = self._get_current_drawing_area()
            if drawing_area:
                analyzed_set = self.analyzed.get(drawing_area, set())
                if analyzer_name not in analyzed_set:
                    # Run analysis in background
                    GLib.idle_add(self._run_analyzer, analyzer_name, drawing_area)
        
        return False  # Allow default expansion behavior
    
    def _get_current_drawing_area(self):
        """Get current drawing area from model canvas.
        
        Returns:
            DrawingArea or None
        """
        if not self.model_canvas:
            return None
        
        if hasattr(self.model_canvas, 'get_current_document'):
            return self.model_canvas.get_current_document()
        elif hasattr(self.model_canvas, 'current_document'):
            return self.model_canvas.current_document
        
        return None
    
    def _run_analyzer(self, analyzer_name, drawing_area):
        """Run analyzer in background thread (non-blocking, UI-safe).
        
        The analyzer computation happens in a separate daemon thread.
        All UI updates (spinner, results, errors) are posted to the main
        GTK thread via GLib.idle_add() for thread safety.
        
        This ensures the UI remains responsive while analyses run.
        
        Args:
            analyzer_name: Name of analyzer to run
            drawing_area: Current drawing area
        """
        if analyzer_name in self.analyzing:
            return  # Already analyzing
        
        self.analyzing.add(analyzer_name)
        
        # ========================================================================
        # EXTRACT MODEL ON MAIN THREAD (before starting background thread)
        # GTK objects must be accessed from the main GTK thread only!
        # ========================================================================
        try:
            # Get manager from model_canvas (on main thread)
            manager = None
            if self.model_canvas:
                if hasattr(self.model_canvas, 'get_canvas_manager'):
                    manager = self.model_canvas.get_canvas_manager(drawing_area)
                elif hasattr(self.model_canvas, 'canvas_managers'):
                    manager = self.model_canvas.canvas_managers.get(drawing_area)
            
            if not manager:
                self._show_error(analyzer_name, "Canvas manager not available")
                self.analyzing.discard(analyzer_name)
                return
            
            # Convert manager to DocumentModel (on main thread)
            if hasattr(manager, 'to_document_model'):
                model = manager.to_document_model()
            else:
                self._show_error(analyzer_name, "Cannot convert to DocumentModel")
                self.analyzing.discard(analyzer_name)
                return
            
            if not model or model.is_empty():
                self._show_error(analyzer_name, "Model is empty")
                self.analyzing.discard(analyzer_name)
                return
            
            # Get analyzer class (on main thread)
            analyzers = self._get_analyzers()
            analyzer_class = analyzers.get(analyzer_name)
            if not analyzer_class:
                self._show_error(analyzer_name, f"Analyzer {analyzer_name} not found")
                self.analyzing.discard(analyzer_name)
                return
                
        except Exception as e:
            self._show_error(analyzer_name, f"Setup error: {str(e)}")
            self.analyzing.discard(analyzer_name)
            return
        
        # Show spinner (on main thread)
        spinner_box, spinner = self.spinner_boxes.get(analyzer_name, (None, None))
        if spinner_box:
            spinner_box.show()
            spinner.start()
        
        # Define background computation thread
        def analyze_thread():
            """Background thread - does NOT access GTK objects or model_canvas."""
            try:
                # ===================================================================
                # COMPUTATION HAPPENS HERE (in background thread, UI-decoupled)
                # Model was extracted on main thread, so this is safe
                # ===================================================================
                analyzer = analyzer_class(model)
                result = analyzer.analyze()  # This can take seconds - UI stays responsive!
                # ===================================================================
                
                # Cache result
                if drawing_area not in self.results_cache:
                    self.results_cache[drawing_area] = {}
                self.results_cache[drawing_area][analyzer_name] = result
                
                # Mark as analyzed
                if drawing_area not in self.analyzed:
                    self.analyzed[drawing_area] = set()
                self.analyzed[drawing_area].add(analyzer_name)
                
                # Display result (scheduled on GTK main thread)
                GLib.idle_add(self._display_result, analyzer_name, result)
                
            except Exception as e:
                # Show error (scheduled on GTK main thread)
                GLib.idle_add(self._show_error, analyzer_name, str(e))
            finally:
                self.analyzing.discard(analyzer_name)
                if spinner_box:
                    # Stop spinner (scheduled on GTK main thread)
                    GLib.idle_add(spinner.stop)
                    GLib.idle_add(spinner_box.hide)
                # Update summary (scheduled on GTK main thread)
                GLib.idle_add(self._update_summary)
        
        # Start background thread (daemon=True means it won't block app exit)
        import threading
        thread = threading.Thread(target=analyze_thread, daemon=True)
        thread.start()  # Returns immediately - UI never blocks!
    
    def _display_result(self, analyzer_name, result):
        """Display analysis result in expander (as table if structured data).
        
        Args:
            analyzer_name: Name of analyzer
            result: Analysis result (AnalysisResult object or data dict)
        """
        container = self.analyzer_containers.get(analyzer_name)
        label = self.analyzer_labels.get(analyzer_name)
        
        if not container or not label:
            return
        
        # Handle AnalysisResult objects
        if hasattr(result, 'success'):
            # Check if analysis was blocked (size guard)
            if not result.success and result.metadata.get('blocked', False):
                # Display block message prominently
                errors = '\n'.join(result.errors) if result.errors else "Analysis blocked"
                warnings = '\n'.join(result.warnings) if result.warnings else ""
                
                formatted = f"<span foreground='orange'><b>⛔ Analysis Blocked</b></span>\n\n"
                formatted += f"<span foreground='red'>{errors}</span>\n\n"
                if warnings:
                    formatted += f"<span foreground='blue'><i>{warnings}</i></span>"
                
                label.set_markup(formatted)
                return
            
            # Check for other errors
            if not result.success:
                self._show_error(analyzer_name, '\n'.join(result.errors))
                return
            
            # Success - extract data for display
            result_data = result.data if hasattr(result, 'data') else {}
        else:
            # Legacy: raw data dict
            result_data = result
        
        # Check if result is tabular (list of dicts or dict with lists)
        if self._is_tabular_result(result_data):
            # Remove label and create table
            label.destroy()
            table = self._create_result_table(result_data)
            container.pack_start(table, True, True, 0)
            container.show_all()
        else:
            # Keep using label for simple results
            if isinstance(result_data, dict):
                formatted = self._format_dict_result(result_data)
            elif isinstance(result_data, list):
                formatted = self._format_list_result(result_data)
            elif isinstance(result_data, str):
                formatted = result_data
            else:
                formatted = str(result_data)
            
            label.set_markup(formatted)
    
    def _is_tabular_result(self, result):
        """Check if result should be displayed as table.
        
        Args:
            result: Analysis result
        
        Returns:
            bool: True if result is tabular data
        """
        # List of dicts (rows)
        if isinstance(result, list) and len(result) > 0:
            if isinstance(result[0], dict):
                return True
        
        # Dict with list values (columns)
        if isinstance(result, dict):
            values = list(result.values())
            if values and isinstance(values[0], list) and len(values[0]) > 0:
                return True
        
        return False
    
    def _create_result_table(self, result):
        """Create TreeView table for tabular results.
        
        Args:
            result: Tabular result (list of dicts or dict of lists)
        
        Returns:
            Gtk.TreeView: Table widget
        """
        # Determine columns and data
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            # List of dicts: each dict is a row
            columns = list(result[0].keys())
            rows = [[str(row.get(col, '')) for col in columns] for row in result]
        elif isinstance(result, dict):
            # Dict of lists/scalars: keys are columns
            columns = list(result.keys())
            
            # Determine number of rows: find max length of list values (scalars count as 1)
            num_rows = 0
            for value in result.values():
                if isinstance(value, (list, tuple)):
                    num_rows = max(num_rows, len(value))
                else:
                    num_rows = max(num_rows, 1)  # Scalar = 1 row
            
            # Transpose: each index becomes a row
            rows = []
            for i in range(num_rows):
                row = []
                for col in columns:
                    col_value = result[col]
                    if isinstance(col_value, (list, tuple)):
                        # List/tuple: get element at index i if exists
                        row.append(str(col_value[i]) if i < len(col_value) else '')
                    else:
                        # Scalar: show on first row only
                        row.append(str(col_value) if i == 0 else '')
                rows.append(row)
        else:
            columns = ['Value']
            rows = [[str(result)]]
        
        # Create ListStore (all columns are strings)
        store = Gtk.ListStore(*([str] * len(columns)))
        
        # Add rows
        for row in rows:
            store.append(row)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_grid_lines(Gtk.TreeViewGridLines.BOTH)
        
        # Add columns
        for i, col_name in enumerate(columns):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(col_name.replace('_', ' ').title(), renderer, text=i)
            column.set_resizable(True)
            column.set_sort_column_id(i)
            treeview.append_column(column)
        
        return treeview
    
    def _format_dict_result(self, result):
        """Format dict result as markup (for simple non-tabular dicts).
        
        Args:
            result: Dict result
        
        Returns:
            str: Formatted markup
        """
        lines = []
        for key, value in result.items():
            key_formatted = key.replace('_', ' ').title()
            if isinstance(value, list):
                lines.append(f"<b>{key_formatted}:</b> {len(value)} items")
            elif isinstance(value, (int, float)):
                lines.append(f"<b>{key_formatted}:</b> {value}")
            else:
                # Limit string length
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                lines.append(f"<b>{key_formatted}:</b> {value_str}")
        return '\n'.join(lines) if lines else "<i>Empty result</i>"
    
    def _format_list_result(self, result):
        """Format list result as markup (for simple non-tabular lists).
        
        Args:
            result: List result
        
        Returns:
            str: Formatted markup
        """
        if not result:
            return "<i>No results found.</i>"
        
        # If list is very long, just show count
        if len(result) > 20:
            return f"<b>Found {len(result)} results</b>\n<i>Results are best viewed in tabular format.</i>"
        
        lines = [f"<b>Found {len(result)} results:</b>\n"]
        for i, item in enumerate(result[:10], 1):  # Show first 10
            item_str = str(item)
            if len(item_str) > 80:
                item_str = item_str[:77] + "..."
            lines.append(f"{i}. {item_str}")
        
        if len(result) > 10:
            lines.append(f"\n<i>... and {len(result) - 10} more</i>")
        
        return '\n'.join(lines)
    
    def _show_error(self, analyzer_name, error_msg):
        """Show error message in analyzer expander.
        
        Args:
            analyzer_name: Name of analyzer
            error_msg: Error message
        """
        label = self.analyzer_labels.get(analyzer_name)
        if label:
            label.set_markup(f"<span foreground='red'><b>Error:</b> {error_msg}</span>")
    
    def _update_summary(self):
        """Update the Analysis Summary section."""
        if not self.summary_label:
            return
        
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        analyzed_set = self.analyzed.get(drawing_area, set())
        total_analyzers = len(self._get_analyzers())
        
        if not analyzed_set:
            self.summary_label.set_markup("<i>Not yet analyzed. Expand an analyzer below to run analysis.</i>")
        else:
            summary = f"<b>Analyzed:</b> {len(analyzed_set)} of {total_analyzers} analyzers\n\n"
            summary += "<b>Results:</b>\n"
            
            for analyzer_name in analyzed_set:
                result = self.results_cache.get(drawing_area, {}).get(analyzer_name)
                if result:
                    summary += f"• {self._format_analyzer_title(analyzer_name)}: ✓\n"
            
            self.summary_label.set_markup(summary)
        
        # Notify report panel that analyses have been updated
        if self.parent_panel:
            self.parent_panel.notify_report_panel()
    
    def auto_run_all_analyzers(self):
        """Auto-run SAFE analyzers in background without requiring user expansion.
        
        This is called when a model is loaded to pre-compute analyses.
        Results are cached and displayed instantly when user expands an analyzer.
        
        IMPORTANT: Only runs analyzers in SAFE_FOR_AUTO_RUN set.
        Dangerous analyzers (exponential complexity) must be manually expanded
        to prevent system freezes on medium/large models.
        
        Safe analyzers (auto-run):
        - P-Invariants, T-Invariants (polynomial matrix operations)
        - Cycles, Paths, Hubs (efficient graph algorithms)
        - Boundedness, Fairness (simple checks)
        
        Dangerous analyzers (manual only):
        - Siphons, Traps (exponential O(2^n) - can freeze on 25+ places)
        - Reachability (state explosion - can take 60s+ on complex models)
        - Liveness, Deadlocks (depend on above)
        
        All analyzers run in background threads with staggered delays to:
        - Avoid blocking the UI
        - Prevent system overload
        - Allow user to interact with the model immediately
        """
        drawing_area = self._get_current_drawing_area()
        if not drawing_area:
            return
        
        # Check if manager exists and has a model
        manager = None
        if self.model_canvas:
            if hasattr(self.model_canvas, 'get_canvas_manager'):
                manager = self.model_canvas.get_canvas_manager(drawing_area)
            elif hasattr(self.model_canvas, 'canvas_managers'):
                manager = self.model_canvas.canvas_managers.get(drawing_area)
        
        if not manager:
            return
        
        # Check if model has content
        if hasattr(manager, 'is_empty') and manager.is_empty():
            return
        
        # Check if already analyzed for this drawing area
        analyzed_set = self.analyzed.get(drawing_area, set())
        
        # Queue ONLY SAFE analyzers with staggered delays
        # Start after 500ms to ensure file loading is complete
        analyzers = self._get_analyzers()
        delay = 500  # Initial delay to let UI settle
        for analyzer_name in analyzers.keys():
            # ONLY auto-run safe analyzers
            if analyzer_name in SAFE_FOR_AUTO_RUN:
                if analyzer_name not in analyzed_set and analyzer_name not in self.analyzing:
                    # Schedule analyzer in background with staggered delays
                    GLib.timeout_add(delay, self._auto_run_single_analyzer, analyzer_name, drawing_area)
                    delay += 200  # 200ms between each analyzer start
    
    def _auto_run_single_analyzer(self, analyzer_name, drawing_area):
        """Helper to run a single analyzer (for GLib.timeout_add).
        
        Args:
            analyzer_name: Name of analyzer to run
            drawing_area: Current drawing area
        
        Returns:
            False: Don't repeat the timeout
        """
        self._run_analyzer(analyzer_name, drawing_area)
        return False  # Don't repeat
    
    def refresh(self):
        """Refresh the category content.
        
        Called when model changes or tab switches.
        Clears cache for old drawing area and updates summary.
        """
        # Update summary for current model
        self._update_summary()
    
    def set_model_canvas(self, model_canvas):
        """Set model canvas and refresh.
        
        Args:
            model_canvas: ModelCanvas instance
        """
        self.model_canvas = model_canvas
        self.refresh()
    
    def get_widget(self):
        """Get the category frame widget.
        
        Returns:
            CategoryFrame: The category widget to add to parent container
        """
        return self.category_frame
