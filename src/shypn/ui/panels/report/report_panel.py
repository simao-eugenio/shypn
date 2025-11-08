#!/usr/bin/env python3
"""Report Panel - Main container for scientific reports.

Displays comprehensive project reports organized by the 4 main panels.

DATA FLOW:
1. KEGG/SBML Import → Saves .shy file (does NOT auto-load to canvas)
2. User opens file via File → Open or double-click
3. File loads to canvas → on_file_opened() event fired
4. Report panel populates with raw imported data (green cells)
5. User clicks Enrich → BRENDA data added (blue cells)
6. User manually edits → Fields marked as edited (orange cells)

KEY BEHAVIOR:
- Report does NOT populate immediately after KEGG/SBML import
- Report populates only AFTER user explicitly opens the saved file
- This is intentional: import saves file, user controls when to load
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .model_structure_category import ModelsCategory
from .provenance_category import ProvenanceCategory
from .parameters_category import DynamicAnalysesCategory
from .topology_analyses_category import TopologyAnalysesCategory


class ReportPanel(Gtk.Box):
    """Main report panel with scientific categories.
    
    Organizes report into categories aligned with SHYpn panels:
    - Models (from Model Canvas Panel)
    - Pathway Operations → Dynamic Analyses (from Pathway Operations Panel)
    - Topology Analyses (from Analyses Panel)
    - Provenance & Lineage (from all panels)
    
    Each category is collapsible and can export its content.
    """
    
    def __init__(self, project=None, model_canvas=None):
        """Initialize report panel.
        
        Args:
            project: Project instance
            model_canvas: ModelCanvasLoader instance (not a specific manager)
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        self.project = project
        # Store the loader for accessing get_current_model()
        self.model_canvas_loader = model_canvas
        self.topology_panel = None  # Will be set via set_topology_panel()
        self.dynamic_analyses_panel = None  # Will be set via set_dynamic_analyses_panel()
        self.pathway_operations_panel = None  # Will be set via set_pathway_operations_panel()
        self.controller = None  # Will be set via set_controller()
        
        # Category controllers
        self.categories = []
        
        # Float button (for loader float/detach functionality)
        self.float_button = None
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build the report panel UI."""
        print("[REPORT_PANEL] Building UI...")
        
        # ===== PANEL HEADER =====
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header_box.set_margin_start(6)
        header_box.set_margin_end(6)
        header_box.set_margin_top(6)
        header_box.set_margin_bottom(6)
        
        # Title label
        title_label = Gtk.Label()
        title_label.set_markup("<b>REPORT</b>")
        title_label.set_xalign(0)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.pack_start(title_label, True, True, 0)
        
        # Float button
        self.float_button = Gtk.ToggleButton(label="⇱")
        self.float_button.set_tooltip_text("Float/Dock panel toggle")
        self.float_button.set_halign(Gtk.Align.END)
        self.float_button.get_style_context().add_class("flat")
        header_box.pack_start(self.float_button, False, False, 0)
        
        self.pack_start(header_box, False, False, 0)
        
        # Separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(separator, False, False, 0)
        
        # ===== MAIN CONTENT =====
        # Main container with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        print(f"[REPORT_PANEL] Created ScrolledWindow: {scrolled}")
        
        # Content box for categories
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        print(f"[REPORT_PANEL] Created content_box: {content_box}")
        
        # Create all categories
        self._create_categories(content_box)
        
        print(f"[REPORT_PANEL] content_box children: {content_box.get_children()}")
        
        scrolled.add(content_box)
        self.pack_start(scrolled, True, True, 0)
        
        print(f"[REPORT_PANEL] self.get_children(): {self.get_children()}")
        print(f"[REPORT_PANEL] scrolled.get_child(): {scrolled.get_child()}")
        
        # Make everything visible
        print("[REPORT_PANEL] Calling show_all()...")
        content_box.show_all()
        scrolled.show_all()
        self.show_all()
        
        print(f"[REPORT_PANEL] After show_all() - self.get_visible(): {self.get_visible()}")
        print(f"[REPORT_PANEL] After show_all() - scrolled.get_visible(): {scrolled.get_visible()}")
        print(f"[REPORT_PANEL] After show_all() - content_box.get_visible(): {content_box.get_visible()}")
        print("[REPORT_PANEL] UI build complete")
    
    def _create_categories(self, container):
        """Create all report categories aligned with panels.
        
        Args:
            container: Container to add categories to
        """
        print("[REPORT_PANEL] Creating categories...")
        
        # Get current model manager if available
        # Initially model_canvas_loader may not have a loaded model
        current_manager = None
        if self.model_canvas_loader and hasattr(self.model_canvas_loader, 'get_current_model'):
            current_manager = self.model_canvas_loader.get_current_model()
        
        print(f"[REPORT_PANEL] Current model manager: {current_manager}")
        
        # MODELS (from Model Canvas Panel)
        # Pass the specific manager if available, otherwise None
        print("[REPORT_PANEL] Creating ModelsCategory...")
        models = ModelsCategory(
            project=self.project,
            model_canvas=current_manager
        )
        self.categories.append(models)
        widget = models.get_widget()
        print(f"[REPORT_PANEL] ModelsCategory widget: {widget}, visible={widget.get_visible()}")
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        print("[REPORT_PANEL] ModelsCategory added to container")
        
        # DYNAMIC ANALYSES (from Pathway Operations Panel - enrichments)
        print("[REPORT_PANEL] Creating DynamicAnalysesCategory...")
        dynamic = DynamicAnalysesCategory(
            name='Dynamic Analyses',
            parent_panel=self
        )
        self.categories.append(dynamic)
        widget = dynamic.get_widget()
        print(f"[REPORT_PANEL] DynamicAnalysesCategory widget: {widget}, visible={widget.get_visible()}")
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        print("[REPORT_PANEL] DynamicAnalysesCategory added to container")
        
        # TOPOLOGY ANALYSES (from Analyses Panel)
        print("[REPORT_PANEL] Creating TopologyAnalysesCategory...")
        topology = TopologyAnalysesCategory(
            project=self.project,
            model_canvas=current_manager
        )
        self.categories.append(topology)
        widget = topology.get_widget()
        print(f"[REPORT_PANEL] TopologyAnalysesCategory widget: {widget}, visible={widget.get_visible()}")
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        print("[REPORT_PANEL] TopologyAnalysesCategory added to container")
        
        # PROVENANCE & LINEAGE (from all panels)
        print("[REPORT_PANEL] Creating ProvenanceCategory...")
        provenance = ProvenanceCategory(
            project=self.project,
            model_canvas=current_manager
        )
        self.categories.append(provenance)
        widget = provenance.get_widget()
        print(f"[REPORT_PANEL] ProvenanceCategory widget: {widget}, visible={widget.get_visible()}")
        widget.show_all()
        container.pack_start(widget, False, False, 0)
        print("[REPORT_PANEL] ProvenanceCategory added to container")
        
        print(f"[REPORT_PANEL] All {len(self.categories)} categories created")
    
    def _create_export_buttons(self):
        """Create export buttons bar.
        
        Returns:
            Gtk.Box: Box with export buttons
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        
        # Export PDF button
        pdf_btn = Gtk.Button(label="📤 Export PDF")
        pdf_btn.set_tooltip_text("Export full report as PDF")
        pdf_btn.connect('clicked', self._on_export_pdf)
        box.pack_start(pdf_btn, True, True, 0)
        
        # Export HTML button
        html_btn = Gtk.Button(label="📤 Export HTML")
        html_btn.set_tooltip_text("Export full report as HTML")
        html_btn.connect('clicked', self._on_export_html)
        box.pack_start(html_btn, True, True, 0)
        
        # Copy button
        copy_btn = Gtk.Button(label="📋 Copy Text")
        copy_btn.set_tooltip_text("Copy report as plain text")
        copy_btn.connect('clicked', self._on_copy_text)
        box.pack_start(copy_btn, True, True, 0)
        
        return box
    
    def _setup_exclusive_expansion(self):
        """Setup exclusive expansion - only one category at a time."""
        for category in self.categories:
            frame = category.get_widget()
            frame._title_event_box.connect('button-press-event',
                lambda w, e, cat=category: self._on_category_clicked(cat))
    
    def _on_category_clicked(self, clicked_category):
        """Handle category click - exclusive expansion.
        
        Args:
            clicked_category: The category that was clicked
        """
        frame = clicked_category.get_widget()
        
        # If clicked category is collapsed, expand it and collapse others
        if not frame.expanded:
            for category in self.categories:
                other_frame = category.get_widget()
                if category == clicked_category:
                    other_frame.set_expanded(True)
                else:
                    other_frame.set_expanded(False)
        
        return True
    
    def _on_refresh_clicked(self, button):
        """Handle refresh button click - update all categories with current data.
        
        Report is intended as a static summary that is manually refreshed.
        This prevents constant updates that could be distracting while working.
        """
        for category in self.categories:
            category.refresh()
    
    # ========================================================================
    # DEPRECATED: BRENDA Enrichment (moved to Pathway Operations → BRENDA)
    # ========================================================================
    # The following methods are deprecated. BRENDA enrichment is now handled
    # by the BRENDA category in the Pathway Operations panel.
    # Use: Pathway Ops → BRENDA → Quick Canvas Enrichment
    
    def _show_info_dialog(self, title, message):
        """Show information dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        dialog = Gtk.MessageDialog(
            transient_for=None,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def refresh_all(self):
        """Programmatically refresh all categories.
        
        Called when significant events occur (e.g., model loaded, analysis completed).
        """
        for category in self.categories:
            category.refresh()
    
    def set_project(self, project):
        """Set project for all categories.
        
        Does NOT auto-refresh - user must click refresh button.
        Report is a static summary, not live data.
        
        Args:
            project: Project instance
        """
        self.project = project
        for category in self.categories:
            category.set_project(project)
    
    def set_model_canvas(self, model_manager):
        """Set model manager for all categories.
        
        This is called with the actual ModelCanvasManager (has places, transitions, arcs).
        Auto-refreshes to immediately show model data.
        
        Args:
            model_manager: ModelCanvasManager instance with model data
        """
        print(f"[REPORT] set_model_canvas called with: {model_manager}")
        
        if model_manager:
            print(f"[REPORT] Model manager has {len(model_manager.places)} places, {len(model_manager.transitions)} transitions")
        
        # Pass the manager directly to all categories
        for category in self.categories:
            if hasattr(category, 'set_model_canvas'):
                category.set_model_canvas(model_manager)
                print(f"[REPORT] Set model_manager for {category.__class__.__name__}")
        
        # Wire up observer for property changes (real-time refresh)
        self._setup_model_observer(model_manager)
        
        # Auto-refresh to show imported data immediately
        if model_manager and hasattr(model_manager, 'transitions'):
            if len(model_manager.transitions) > 0 or len(model_manager.places) > 0:
                print(f"[REPORT] Auto-refreshing to show {len(model_manager.places)} places and {len(model_manager.transitions)} transitions")
                self.refresh_all()
            else:
                print(f"[REPORT] Skipping auto-refresh - model is empty")
        else:
            print(f"[REPORT] Skipping auto-refresh - no model_manager or no transitions attribute")
    
    def _setup_model_observer(self, model_manager):
        """Setup observer for model changes to enable real-time refresh.
        
        Hooks into the mark_dirty callback from ModelCanvasManager.
        When properties are edited (via property dialogs), document is marked dirty
        and report automatically refreshes to show updated data.
        
        Args:
            model_manager: ModelCanvasManager instance
        """
        if not model_manager:
            return
        
        # Hook into on_dirty_changed callback
        # This is triggered whenever document is modified (via property dialogs, etc.)
        if hasattr(model_manager, 'on_dirty_changed'):
            # Store original callback
            original_callback = model_manager.on_dirty_changed
            
            # Create wrapper that also refreshes report
            def on_dirty_with_refresh(is_dirty):
                # Call original callback first (updates tab labels, etc.)
                if original_callback:
                    original_callback(is_dirty)
                
                # If document was just marked dirty, refresh report
                # (Shows updated property values after edits)
                if is_dirty:
                    self.refresh_all()
            
            # Install our wrapped callback
            model_manager.on_dirty_changed = on_dirty_with_refresh
    
    def set_topology_panel(self, topology_panel):
        """Set topology panel reference for fetching analysis data.
        
        Args:
            topology_panel: TopologyPanel instance
        """
        self.topology_panel = topology_panel
        
        # Update topology analyses category with the panel reference
        for category in self.categories:
            if isinstance(category, TopologyAnalysesCategory):
                category.set_topology_panel(topology_panel)
                break
        
        # Set callback so topology panel can notify us when analyses update
        if hasattr(topology_panel, 'set_report_refresh_callback'):
            topology_panel.set_report_refresh_callback(self._on_topology_updated)
    
    def _on_topology_updated(self):
        """Called by topology panel when analyses are updated."""
        # Refresh the topology analyses category
        for category in self.categories:
            if isinstance(category, TopologyAnalysesCategory):
                category.refresh()
                break
    
    def set_dynamic_analyses_panel(self, dynamic_analyses_panel):
        """Set dynamic analyses panel reference for fetching real-time data.
        
        Args:
            dynamic_analyses_panel: DynamicAnalysesPanel instance
        """
        self.dynamic_analyses_panel = dynamic_analyses_panel
        
        # Update dynamic analyses category with the panel reference
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_dynamic_analyses_panel(dynamic_analyses_panel)
                break
        
        # Set callback so dynamic analyses panel can notify us when data updates
        if hasattr(dynamic_analyses_panel, 'set_report_refresh_callback'):
            dynamic_analyses_panel.set_report_refresh_callback(self._on_dynamic_analyses_updated)
    
    def _on_dynamic_analyses_updated(self):
        """Called by dynamic analyses panel when monitoring data is updated."""
        # Refresh the dynamic analyses category
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.refresh()
                break
    
    def set_pathway_operations_panel(self, pathway_operations_panel):
        """Set pathway operations panel reference for fetching pathway data.
        
        Args:
            pathway_operations_panel: PathwayOperationsPanel instance
        """
        self.pathway_operations_panel = pathway_operations_panel
        
        # Update dynamic analyses category with the panel reference
        # (it displays pathway enrichments and KEGG/SBML import data)
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_pathway_operations_panel(pathway_operations_panel)
                break
        
        # Set callback so pathway operations panel can notify us when pathways are imported
        if hasattr(pathway_operations_panel, 'set_report_refresh_callback'):
            pathway_operations_panel.set_report_refresh_callback(self._on_pathway_imported)
    
    def _on_pathway_imported(self):
        """Called by pathway operations panel when new pathway is imported."""
        print("[REPORT] _on_pathway_imported() called")
        
        # Get current model canvas manager
        if hasattr(self.model_canvas_loader, 'get_current_model'):
            current_manager = self.model_canvas_loader.get_current_model()
            print(f"[REPORT] Current model canvas manager: {current_manager}")
            
            if current_manager:
                # Check if current_manager has the model data
                if hasattr(current_manager, 'places'):
                    print(f"[REPORT] Current manager has {len(current_manager.places)} places, {len(current_manager.transitions)} transitions")
                else:
                    print(f"[REPORT] WARNING: Current manager has no places/transitions attributes!")
                
                # Update all categories with the current model canvas
                for category in self.categories:
                    if hasattr(category, 'set_model_canvas'):
                        print(f"[REPORT] Setting model_canvas for {category.__class__.__name__}")
                        category.set_model_canvas(current_manager)
                
                # Refresh all categories to show imported data
                print("[REPORT] Calling refresh_all()")
                self.refresh_all()
            else:
                print("[REPORT] ERROR: get_current_model() returned None!")
        else:
            print("[REPORT] ERROR: model_canvas_loader has no get_current_model() method!")
    
    def set_controller(self, controller):
        """Set simulation controller reference for dynamic analyses.
        
        Args:
            controller: SimulationController instance
        """
        self.controller = controller
        
        # Update dynamic analyses category with controller reference
        for category in self.categories:
            if isinstance(category, DynamicAnalysesCategory):
                category.set_controller(controller)
                break
    
    def on_file_opened(self, filepath):
        """Called when a file is opened (File → Open or double-click).
        
        Args:
            filepath: Path to the opened file
        """
        # Refresh Models category to show new model information
        for category in self.categories:
            if isinstance(category, ModelsCategory):
                category.refresh()
                break
    
    def on_file_new(self):
        """Called when a new file is created (File → New)."""
        # Refresh Models category to show new model
        for category in self.categories:
            if isinstance(category, ModelsCategory):
                category.refresh()
                break
    
    def on_tab_switched(self, drawing_area):
        """Called when user switches between model tabs.
        
        Args:
            drawing_area: The newly active drawing area
        """
        print(f"[REPORT_PANEL] on_tab_switched called, drawing_area={drawing_area}")
        
        # Refresh Models category to show current tab's model
        for category in self.categories:
            if isinstance(category, ModelsCategory):
                category.refresh()
            # Also refresh Dynamic Analyses to show current tab's simulation data
            elif hasattr(category, '_refresh_simulation_data'):
                print(f"[REPORT_PANEL] Refreshing Dynamic Analyses for tab switch")
                from gi.repository import GLib
                GLib.idle_add(category._refresh_simulation_data)
        
        print(f"[REPORT_PANEL] on_tab_switched completed")
    
    def on_project_opened(self, project):
        """Called when a project is opened.
        
        Args:
            project: Opened Project instance
        """
        self.set_project(project)
        # Refresh all categories with new project context
        self.refresh_all()
    
    def refresh_all(self):
        """Refresh all categories."""
        for category in self.categories:
            category.refresh()
    
    def _on_export_pdf(self, button):
        """Handle export to PDF."""
        # TODO: Implement PDF export
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="PDF Export"
        )
        dialog.format_secondary_text("PDF export not yet implemented")
        dialog.run()
        dialog.destroy()
    
    def _on_export_html(self, button):
        """Handle export to HTML."""
        # Build HTML from all categories
        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<meta charset='utf-8'>",
            "<title>SHYpn Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; margin: 40px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 2px solid #ddd; padding-bottom: 10px; }",
            "table { border-collapse: collapse; width: 100%; margin: 20px 0; }",
            "th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }",
            "th { background-color: #f2f2f2; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>SHYpn Project Report</h1>"
        ]
        
        if self.project:
            html_parts.append(f"<p><strong>Project:</strong> {self.project.name}</p>")
        
        # Export each category
        for category in self.categories:
            html_parts.append(category.export_to_html())
        
        html_parts.extend(["</body>", "</html>"])
        
        html_content = "\n".join(html_parts)
        
        # Save dialog
        dialog = Gtk.FileChooserDialog(
            title="Export Report as HTML",
            parent=self.get_toplevel(),
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK
        )
        dialog.set_current_name("report.html")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                info_dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    flags=0,
                    message_type=Gtk.MessageType.INFO,
                    buttons=Gtk.ButtonsType.OK,
                    text="Export Successful"
                )
                info_dialog.format_secondary_text(f"Report saved to:\n{filepath}")
                info_dialog.run()
                info_dialog.destroy()
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    flags=0,
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text="Export Failed"
                )
                error_dialog.format_secondary_text(str(e))
                error_dialog.run()
                error_dialog.destroy()
        
        dialog.destroy()
    
    def _on_copy_text(self, button):
        """Handle copy as plain text."""
        # Build text from all categories
        text_parts = ["SHYpn Project Report", "=" * 50, ""]
        
        if self.project:
            text_parts.append(f"Project: {self.project.name}")
            text_parts.append("")
        
        for category in self.categories:
            text_parts.append(category.export_to_text())
        
        text_content = "\n".join(text_parts)
        
        # Copy to clipboard
        clipboard = Gtk.Clipboard.get(Gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(text_content, -1)
        
        # Show confirmation
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Copied to Clipboard"
        )
        dialog.format_secondary_text("Report text copied to clipboard")
        dialog.run()
        dialog.destroy()
    
    # =========================================================================
    # MODEL LIFECYCLE EVENT HANDLERS
    # These are called by shypn.py when model-related events occur
    # =========================================================================
    
    def on_tab_switched(self, drawing_area):
        """Handle canvas tab switch event.
        
        Called when user switches between model tabs.
        Updates the model_canvas reference to the new active tab.
        
        Args:
            drawing_area: The newly active drawing area (GtkDrawingArea)
        """
        # Get the ModelCanvasManager for this drawing area
        if hasattr(self.model_canvas_loader, 'get_canvas_manager'):
            current_manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
            if current_manager:
                # Update the reference for all categories
                for category in self.categories:
                    if hasattr(category, 'set_model_canvas'):
                        category.set_model_canvas(current_manager)
                # Auto-refresh when switching tabs to show new model
                self.refresh_all()
    
    def on_file_opened(self, filepath):
        """Handle file open event.
        
        Called when user opens a .shypn file.
        Gets the current model canvas and refreshes the report.
        
        Args:
            filepath: Path to the opened file
        """
        print(f"[REPORT] on_file_opened: {filepath}")
        
        # Add a small delay to ensure model is fully loaded
        from gi.repository import GLib
        
        def delayed_refresh():
            # Get current model canvas after file load
            if hasattr(self.model_canvas_loader, 'get_current_model'):
                current_manager = self.model_canvas_loader.get_current_model()
                print(f"[REPORT] on_file_opened delayed: Got manager: {current_manager}")
                if current_manager:
                    print(f"[REPORT] Manager has {len(current_manager.places)} places, {len(current_manager.transitions)} transitions")
                    for category in self.categories:
                        if hasattr(category, 'set_model_canvas'):
                            category.set_model_canvas(current_manager)
                    # Auto-refresh on file open (major event)
                    print(f"[REPORT] Calling refresh_all()")
                    self.refresh_all()
            return False  # Don't repeat
        
        # Delay 100ms to let model finish loading
        GLib.timeout_add(100, delayed_refresh)
    
    def on_file_new(self):
        """Handle new file event.
        
        Called when user creates a new model.
        Gets the current model canvas and refreshes the report.
        """
        # Get current model canvas after new file creation
        if hasattr(self.model_canvas_loader, 'get_current_model'):
            current_manager = self.model_canvas_loader.get_current_model()
            if current_manager:
                for category in self.categories:
                    if hasattr(category, 'set_model_canvas'):
                        category.set_model_canvas(current_manager)
                # Auto-refresh on new file (major event)
                self.refresh_all()
    
    def on_model_imported(self, source_type):
        """Handle model import event.
        
        Called when user imports KEGG/SBML/BioPAX model.
        Gets the current model canvas and refreshes the report.
        
        Args:
            source_type: Type of import (KEGG, SBML, etc.)
        """
        # Get current model canvas after import
        if hasattr(self.model_canvas_loader, 'get_current_model'):
            current_manager = self.model_canvas_loader.get_current_model()
            if current_manager:
                for category in self.categories:
                    if hasattr(category, 'set_model_canvas'):
                        category.set_model_canvas(current_manager)
                # Auto-refresh on import (major event)
                self.refresh_all()
    
    def cleanup(self):
        """Clean up resources when panel is closed.
        
        Called by the loader when the panel is being destroyed.
        """
        # Clean up any resources held by categories
        for category in self.categories:
            if hasattr(category, 'cleanup'):
                category.cleanup()
        
        # Clear references
        self.categories.clear()
        self.project = None
        self.model_canvas_loader = None
        self.topology_panel = None
        self.dynamic_analyses_panel = None
        self.pathway_operations_panel = None
