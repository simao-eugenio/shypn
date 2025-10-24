#!/usr/bin/env python3
"""Pathway Panel Loader/Controller.

This module is responsible for loading and managing the Pathway Operations panel.
The panel can exist in two states:
  - Detached: standalone floating window
  - Attached: content embedded in main window container

The panel contains a notebook with multiple tabs:
  - Import: KEGG pathway import interface
  - Browse: Browse available pathways (future)
  - History: Recently imported pathways (future)
"""
import os
import sys

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, GLib
except Exception as e:
    print('ERROR: GTK3 not available in pathway_panel loader:', e, file=sys.stderr)
    sys.exit(1)


class PathwayPanelLoader:
    """Loader and controller for the Pathway Operations panel (attachable window)."""
    
    def __init__(self, ui_path=None, model_canvas=None, workspace_settings=None):
        """Initialize the pathway panel loader.
        
        Args:
            ui_path: Optional path to pathway_panel.ui. If None, uses default location.
            model_canvas: Optional ModelCanvasManager for loading imported pathways
            workspace_settings: Optional WorkspaceSettings for remembering user preferences
        """
        if ui_path is None:
            # Default: ui/panels/pathway_panel.ui
            # This loader file is in: src/shypn/helpers/pathway_panel_loader.py
            # UI file is in: ui/panels/pathway_panel.ui
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'panels', 'pathway_panel.ui')
        
        self.ui_path = ui_path
        self.model_canvas = model_canvas
        self.workspace_settings = workspace_settings
        self.builder = None
        self.window = None
        self.content = None
        self.is_hanged = False  # Simple state flag (skeleton pattern)
        self.parent_container = None
        self.parent_window = None  # Track parent window for float button
        self._updating_button = False  # Flag to prevent recursive toggle events
        self.on_float_callback = None  # Callback to notify when panel floats
        self.on_attach_callback = None  # Callback to notify when panel attaches
        
        # Import tab controllers (will be instantiated after loading UI)
        self.kegg_import_controller = None
        self.sbml_import_controller = None
    
    def load(self):
        """Load the panel UI and return the window.
        
        Returns:
            Gtk.Window: The pathway panel window.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If window or content not found in UI file.
        """
        # Validate UI file exists
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f"Pathway panel UI file not found: {self.ui_path}")
        
        # Load the UI
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Extract window and content
        self.window = self.builder.get_object('pathway_panel_window')
        self.content = self.builder.get_object('pathway_panel_content')
        
        if self.window is None:
            raise ValueError("Object 'pathway_panel_window' not found in pathway_panel.ui")
        if self.content is None:
            raise ValueError("Object 'pathway_panel_content' not found in pathway_panel.ui")
        
        # Get float button and connect callback
        float_button = self.builder.get_object('float_button')
        if float_button:
            float_button.connect('toggled', self._on_float_toggled)
            self.float_button = float_button
        else:
            self.float_button = None
        
        # Connect delete-event to prevent window destruction
        # When X button is clicked, just hide the window instead of destroying it
        self.window.connect('delete-event', self._on_delete_event)
        
        # Initialize tab controllers
        self._setup_import_tab()
        self._setup_sbml_tab()
        self._setup_brenda_tab()
        
        # Wire up unified UI signals (radio buttons, browse buttons)
        self._setup_unified_ui_signals()
        
        # WAYLAND FIX: Don't realize window early - let GTK do it naturally
        # Realizing too early can cause protocol errors on Wayland
        # self.window.realize()
        # if self.window.get_window():
        #     try:
        #         from gi.repository import Gdk
        #         self.window.get_window().set_events(
        #             self.window.get_window().get_events() | 
        #             Gdk.EventMask.STRUCTURE_MASK |
        #             Gdk.EventMask.PROPERTY_CHANGE_MASK
        #         )
        #     except Exception as e:
        #         print(f"[PATHWAY_PANEL] Could not set window event mask: {e}", file=sys.stderr)
        
        # Hide window by default (will be shown when toggled)
        self.window.set_visible(False)
        
        return self.window
    
    def _setup_import_tab(self):
        """Set up the Import tab controllers.
        
        This method instantiates the KEGG import controller and wires it to the UI.
        """
        # Import the KEGG import controller (from helpers, not ui)
        try:
            from shypn.helpers.kegg_import_panel import KEGGImportPanel
            
            # Instantiate controller with builder and model_canvas
            self.kegg_import_controller = KEGGImportPanel(
                self.builder,
                self.model_canvas
            )
            
        except ImportError as e:
            print(f"Warning: Could not load KEGG import controller: {e}", file=sys.stderr)
            pass
    
    def _setup_sbml_tab(self):
        """Set up the SBML tab controllers.
        
        This method instantiates the SBML import controller and wires it to the UI.
        """
        # Import the SBML import controller (from helpers)
        try:
            from shypn.helpers.sbml_import_panel import SBMLImportPanel
            
            # Instantiate controller with builder and model_canvas
            # WAYLAND FIX: Pass None for parent_window initially, will be set when panel attaches
            self.sbml_import_controller = SBMLImportPanel(
                self.builder,
                self.model_canvas,
                self.workspace_settings,
                parent_window=None
            )
            
        except ImportError as e:
            print(f"Warning: Could not load SBML import controller: {e}", file=sys.stderr)
            pass
    
    def _setup_brenda_tab(self):
        """Set up the BRENDA tab controllers.
        
        This method will instantiate the BRENDA connector when implemented.
        For now, it's a placeholder.
        """
        # TODO: Import and instantiate BRENDA connector
        # try:
        #     from shypn.data.brenda.brenda_connector import BRENDAConnector
        #     self.brenda_connector = BRENDAConnector(...)
        # except ImportError as e:
        #     print(f"Warning: Could not load BRENDA connector: {e}", file=sys.stderr)
        pass
    
    def _setup_unified_ui_signals(self):
        """Wire up signals for the unified UI pattern (radio buttons, browse buttons).
        
        This handles the External/Local source selection and file browsing
        for all three tabs: KEGG, SBML, BRENDA.
        """
        # ===== KEGG Tab Signals =====
        kegg_database_radio = self.builder.get_object('kegg_database_radio')
        kegg_local_radio = self.builder.get_object('kegg_local_radio')
        kegg_browse_button = self.builder.get_object('kegg_browse_button')
        kegg_import_button = self.builder.get_object('kegg_import_button')
        
        if kegg_database_radio:
            kegg_database_radio.connect('toggled', self._on_kegg_source_toggled)
        if kegg_browse_button:
            kegg_browse_button.connect('clicked', self._on_kegg_browse_clicked)
        if kegg_import_button:
            kegg_import_button.connect('clicked', self._on_kegg_import_clicked)
        
        # ===== SBML Tab Signals =====
        sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
        sbml_local_radio = self.builder.get_object('sbml_local_radio')
        sbml_browse_button = self.builder.get_object('sbml_browse_button')
        sbml_import_button = self.builder.get_object('sbml_import_button')
        
        if sbml_biomodels_radio:
            sbml_biomodels_radio.connect('toggled', self._on_sbml_source_toggled)
        if sbml_browse_button:
            sbml_browse_button.connect('clicked', self._on_sbml_browse_clicked)
        if sbml_import_button:
            sbml_import_button.connect('clicked', self._on_sbml_import_clicked)
        
        # ===== BRENDA Tab Signals =====
        brenda_external_radio = self.builder.get_object('brenda_external_radio')
        brenda_local_radio = self.builder.get_object('brenda_local_radio')
        brenda_browse_button = self.builder.get_object('brenda_browse_button')
        brenda_configure_button = self.builder.get_object('brenda_configure_button')
        brenda_enrich_button = self.builder.get_object('brenda_enrich_button')
        
        if brenda_external_radio:
            brenda_external_radio.connect('toggled', self._on_brenda_source_toggled)
        if brenda_browse_button:
            brenda_browse_button.connect('clicked', self._on_brenda_browse_clicked)
        if brenda_configure_button:
            brenda_configure_button.connect('clicked', self._on_brenda_configure_clicked)
        if brenda_enrich_button:
            brenda_enrich_button.connect('clicked', self._on_brenda_enrich_clicked)
    
    # ========================================================================
    # KEGG Tab Signal Handlers
    # ========================================================================
    
    def _on_kegg_source_toggled(self, radio):
        """Handle KEGG source selection (Database/Local) radio button toggle."""
        if not radio.get_active():
            return  # Only handle activation, not deactivation
        
        kegg_database_box = self.builder.get_object('kegg_database_box')
        kegg_local_box = self.builder.get_object('kegg_local_box')
        
        # Get which radio is active
        kegg_database_radio = self.builder.get_object('kegg_database_radio')
        is_database = kegg_database_radio.get_active()
        
        # Show/hide appropriate box
        if kegg_database_box:
            kegg_database_box.set_visible(is_database)
        if kegg_local_box:
            kegg_local_box.set_visible(not is_database)
    
    def _on_kegg_browse_clicked(self, button):
        """Handle KEGG Browse button - open file chooser for KGML files."""
        dialog = Gtk.FileChooserDialog(
            title="Select KGML File",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filter for XML files
        filter_xml = Gtk.FileFilter()
        filter_xml.set_name("KGML Files (*.xml)")
        filter_xml.add_pattern("*.xml")
        dialog.add_filter(filter_xml)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            kegg_file_entry = self.builder.get_object('kegg_file_entry')
            if kegg_file_entry:
                kegg_file_entry.set_text(filename)
        
        dialog.destroy()
    
    def _on_kegg_import_clicked(self, button):
        """Handle unified KEGG Import to Canvas button.
        
        Routes to either database (fetch from API) or local (load file) workflow.
        """
        kegg_database_radio = self.builder.get_object('kegg_database_radio')
        
        if kegg_database_radio and kegg_database_radio.get_active():
            # Database source: fetch from KEGG API, then import
            if self.kegg_import_controller:
                # First fetch the pathway
                self.kegg_import_controller._on_fetch_clicked(button)
                # Import will be triggered automatically after fetch completes
                # (the controller will enable import button and user clicks it,
                # or we could auto-import after fetch - TBD based on UX preference)
        else:
            # Local source: load from file
            kegg_file_entry = self.builder.get_object('kegg_file_entry')
            if kegg_file_entry:
                file_path = kegg_file_entry.get_text()
                if file_path and os.path.exists(file_path):
                    # TODO: Implement local KGML file loading
                    # For now, show info message
                    self._show_info(
                        f"Local KGML file import is under development.\n\n"
                        f"Selected file: {os.path.basename(file_path)}\n\n"
                        f"This will load the KGML file directly without fetching from KEGG API."
                    )
                else:
                    self._show_error("Please select a valid KGML file")
    
    # ========================================================================
    # SBML Tab Signal Handlers
    # ========================================================================
    
    def _on_sbml_source_toggled(self, radio):
        """Handle SBML source selection (BioModels/Local) radio button toggle."""
        if not radio.get_active():
            return  # Only handle activation, not deactivation
        
        sbml_biomodels_box = self.builder.get_object('sbml_biomodels_box')
        sbml_local_box = self.builder.get_object('sbml_local_box')
        
        # Get which radio is active
        sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
        is_biomodels = sbml_biomodels_radio.get_active()
        
        # Show/hide appropriate box
        if sbml_biomodels_box:
            sbml_biomodels_box.set_visible(is_biomodels)
        if sbml_local_box:
            sbml_local_box.set_visible(not is_biomodels)
    
    def _on_sbml_browse_clicked(self, button):
        """Handle SBML Browse button - open file chooser for SBML files."""
        if self.sbml_import_controller:
            # Delegate to existing controller's browse method
            self.sbml_import_controller._on_browse_clicked(button)
    
    def _on_sbml_import_clicked(self, button):
        """Handle unified SBML Import to Canvas button.
        
        Routes to either BioModels (fetch from database) or local (load file) workflow.
        """
        sbml_biomodels_radio = self.builder.get_object('sbml_biomodels_radio')
        
        if sbml_biomodels_radio and sbml_biomodels_radio.get_active():
            # BioModels source: fetch from database
            if self.sbml_import_controller:
                # Delegate to existing controller's fetch method
                self.sbml_import_controller._on_fetch_clicked(button)
        else:
            # Local source: parse and load (controller handles file selection)
            if self.sbml_import_controller:
                # Delegate to existing controller's parse method
                self.sbml_import_controller._on_parse_clicked(button)
    
    # ========================================================================
    # BRENDA Tab Signal Handlers
    # ========================================================================
    
    def _on_brenda_source_toggled(self, radio):
        """Handle BRENDA source selection (External/Local) radio button toggle."""
        if not radio.get_active():
            return  # Only handle activation, not deactivation
        
        brenda_external_box = self.builder.get_object('brenda_external_box')
        brenda_local_box = self.builder.get_object('brenda_local_box')
        
        # Get which radio is active
        brenda_external_radio = self.builder.get_object('brenda_external_radio')
        is_external = brenda_external_radio.get_active()
        
        # Show/hide appropriate box
        if brenda_external_box:
            brenda_external_box.set_visible(is_external)
        if brenda_local_box:
            brenda_local_box.set_visible(not is_external)
    
    def _on_brenda_browse_clicked(self, button):
        """Handle BRENDA Browse button - open file chooser for CSV/JSON files."""
        dialog = Gtk.FileChooserDialog(
            title="Select BRENDA Data File",
            parent=self.parent_window,
            action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK
        )
        
        # Add filters for CSV and JSON
        filter_csv = Gtk.FileFilter()
        filter_csv.set_name("CSV Files (*.csv)")
        filter_csv.add_pattern("*.csv")
        dialog.add_filter(filter_csv)
        
        filter_json = Gtk.FileFilter()
        filter_json.set_name("JSON Files (*.json)")
        filter_json.add_pattern("*.json")
        dialog.add_filter(filter_json)
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All Files")
        filter_all.add_pattern("*")
        dialog.add_filter(filter_all)
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            brenda_file_entry = self.builder.get_object('brenda_file_entry')
            if brenda_file_entry:
                brenda_file_entry.set_text(filename)
        
        dialog.destroy()
    
    def _on_brenda_configure_clicked(self, button):
        """Handle BRENDA Configure button - open User Profile dialog.
        
        TODO: Implement User Profile dialog with BRENDA credentials section.
        """
        # Placeholder for now
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="BRENDA Credentials Configuration"
        )
        dialog.format_secondary_text(
            "This feature will open the User Profile dialog where you can:\n\n"
            "• Enter your BRENDA email and password\n"
            "• Test connection to BRENDA API\n"
            "• View account activation status\n\n"
            "Registration: https://www.brenda-enzymes.org/register.php\n"
            "Approval takes 1-2 business days."
        )
        dialog.run()
        dialog.destroy()
    
    def _on_brenda_enrich_clicked(self, button):
        """Handle BRENDA Analyze and Enrich Canvas button.
        
        Workflow:
        1. Scan canvas for all transitions (potential enzymes)
        2. Query BRENDA for kinetic data (external API or local file)
        3. Generate enrichment report
        4. User reviews and selects which data to apply
        5. Apply selected enrichments to canvas
        
        This respects existing data in SBML models while enriching KEGG pathways.
        """
        brenda_external_radio = self.builder.get_object('brenda_external_radio')
        
        if brenda_external_radio and brenda_external_radio.get_active():
            # External source: query BRENDA API
            # Check options
            brenda_override_check = self.builder.get_object('brenda_override_check')
            override_existing = brenda_override_check.get_active() if brenda_override_check else False
            
            if override_existing:
                # Warn user about overriding SBML data
                dialog = Gtk.MessageDialog(
                    transient_for=self.parent_window,
                    message_type=Gtk.MessageType.WARNING,
                    buttons=Gtk.ButtonsType.YES_NO,
                    text="Override Existing Parameters?"
                )
                dialog.format_secondary_text(
                    "You have enabled 'Override existing parameters'.\n\n"
                    "This will replace kinetic data in curated SBML models.\n\n"
                    "Recommended:\n"
                    "• KEGG pathways: YES (no kinetics to lose)\n"
                    "• SBML models: NO (preserve curated data)\n\n"
                    "Continue with override enabled?"
                )
                response = dialog.run()
                dialog.destroy()
                
                if response != Gtk.ResponseType.YES:
                    return  # User cancelled
            
            # TODO: Implement BRENDA enrichment workflow
            self._show_info(
                "BRENDA Canvas Enrichment Workflow:\n\n"
                "1. Scan canvas for transitions (enzymes)\n"
                "2. Query BRENDA API for kinetic data\n"
                "3. Generate enrichment report\n"
                "4. Review and select data to apply\n"
                "5. Enrich canvas with selected parameters\n\n"
                "This feature is under development.\n\n"
                "Override existing: " + ("YES ⚠️" if override_existing else "NO ✓")
            )
        else:
            # Local source: load from CSV/JSON file
            brenda_file_entry = self.builder.get_object('brenda_file_entry')
            if brenda_file_entry:
                file_path = brenda_file_entry.get_text()
                if file_path and os.path.exists(file_path):
                    # TODO: Implement local BRENDA file enrichment
                    self._show_info(
                        f"Local BRENDA enrichment workflow:\n\n"
                        f"1. Load data from: {os.path.basename(file_path)}\n"
                        f"2. Match to canvas transitions\n"
                        f"3. Generate enrichment report\n"
                        f"4. Review and apply selected data\n\n"
                        f"This feature is under development."
                    )
                else:
                    self._show_error("Please select a valid BRENDA data file (CSV or JSON)")
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _show_error(self, message):
        """Show error dialog to user."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_info(self, message):
        """Show info dialog to user."""
        dialog = Gtk.MessageDialog(
            transient_for=self.parent_window,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Information"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas for loading imported pathways.
        
        Args:
            model_canvas: ModelCanvasManager instance
        """
        self.model_canvas = model_canvas
        
        # Update import controllers if they exist
        if self.kegg_import_controller:
            self.kegg_import_controller.set_model_canvas(model_canvas)
        
        if self.sbml_import_controller:
            self.sbml_import_controller.set_model_canvas(model_canvas)
        
        # Wire SBML panel to model canvas so Swiss Palette can read layout parameters
        if model_canvas and self.sbml_import_controller:
            model_canvas.sbml_panel = self.sbml_import_controller
    
    def get_sbml_controller(self):
        """Get the SBML import controller instance.
        
        Returns:
            SBMLImportPanel instance or None
        """
        return self.sbml_import_controller
    
    def _on_float_toggled(self, button):
        """Internal callback when float toggle button is clicked."""
        # Prevent recursive calls when we update the button state programmatically
        if self._updating_button:
            return
            
        is_active = button.get_active()
        if is_active:
            # Button is now active → detach the panel (float)
            self.detach()
        else:
            # Button is now inactive → attach the panel back
            if self.parent_container:
                self.hang_on(self.parent_container)
    
    def _on_delete_event(self, window, event):
        """Handle window close button (X) - hide instead of destroy.
        
        When user clicks X on floating window, we don't want to destroy
        the window (which causes segfault), just hide it and dock it back.
        
        Args:
            window: The window being closed
            event: The delete event
            
        Returns:
            bool: True to prevent default destroy behavior
        """
        # Hide the window
        self.hide()
        
        # Update float button to inactive state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Dock back if we have a container
        if self.parent_container:
            self.attach_to(self.parent_container, self.parent_window)
        
        # Return True to prevent window destruction
        return True
    
    def detach(self):
        """Detach from container and restore as independent window (skeleton pattern)."""
        print(f"[PATHWAY_PANEL] Detaching from container...")
        
        if not self.is_hanged:
            print(f"[PATHWAY_PANEL] Already detached")
            return
        
        # Remove from container
        if self.parent_container:
            self.parent_container.remove(self.content)
            # Hide the container after unattaching
            self.parent_container.set_visible(False)
        
        # Hide the stack if this was the active panel
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(False)
        
        # Return content to independent window
        self.window.add(self.content)
        
        # Set transient for main window if available
        if self.parent_window:
            self.window.set_transient_for(self.parent_window)
        
        # Update state
        self.is_hanged = False
        
        # Update float button state
        if self.float_button and not self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(True)
            self._updating_button = False
        
        # Notify that panel is floating
        if self.on_float_callback:
            self.on_float_callback()
        
        # Show window - WAYLAND FIX: Don't use show_all()
        self.window.show()
        
        print(f"[PATHWAY_PANEL] Detached successfully")
    
    def float(self, parent_window=None):
        """Float panel as a separate window (alias for detach for backward compatibility).
        
        Args:
            parent_window: Optional parent window to set as transient.
        """
        if parent_window:
            self.parent_window = parent_window
            # Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        self.detach()
    
    def hang_on(self, container):
        """Hang this panel on a container (attach - skeleton pattern).
        
        Args:
            container: Gtk.Box or other container to embed content into.
        """
        print(f"[PATHWAY_PANEL] Hanging on container...")
        
        if self.is_hanged:
            print(f"[PATHWAY_PANEL] Already hanged, just showing")
            if not self.content.get_visible():
                self.content.show()  # WAYLAND FIX: Don't use show_all()
            # Make sure container is visible when re-showing
            if not container.get_visible():
                container.set_visible(True)
            return
        
        # Hide independent window
        self.window.hide()
        
        # Remove content from window
        self.window.remove(self.content)
        
        # Hang content on container
        container.pack_start(self.content, True, True, 0)
        self.content.show()  # WAYLAND FIX: Don't use show_all()
        
        # Make container visible (it was hidden when detached)
        container.set_visible(True)
        
        self.is_hanged = True
        self.parent_container = container
        
        # Update float button state
        if self.float_button and self.float_button.get_active():
            self._updating_button = True
            self.float_button.set_active(False)
            self._updating_button = False
        
        # Show the stack if available
        if hasattr(self, '_stack') and self._stack:
            self._stack.set_visible(True)
            if hasattr(self, '_stack_panel_name'):
                self._stack.set_visible_child_name(self._stack_panel_name)
        
        # Notify that panel is attached
        if self.on_attach_callback:
            self.on_attach_callback()
        
        print(f"[PATHWAY_PANEL] Hanged successfully")
    
    def attach_to(self, container, parent_window=None):
        """Attach panel to container (alias for hang_on for backward compatibility).
        
        Args:
            container: Gtk.Box or other container to embed content into.
            parent_window: Optional parent window (stored for float button).
        """
        if parent_window:
            self.parent_window = parent_window
            # Update SBML controller's parent window for FileChooser dialogs
            if self.sbml_import_controller:
                self.sbml_import_controller.set_parent_window(parent_window)
            # Update KEGG controller's parent window if needed
            if self.kegg_import_controller and hasattr(self.kegg_import_controller, 'set_parent_window'):
                self.kegg_import_controller.set_parent_window(parent_window)
        
        self.hang_on(container)
    
    def unattach(self):
        """Unattach panel from container (alias for detach for backward compatibility)."""
        self.detach()
    
    def hide(self):
        """Hide the panel (keep hanged but invisible - skeleton pattern)."""
        print(f"[PATHWAY_PANEL] Hiding panel...")
        
        if self.is_hanged and self.parent_container:
            # Hide content while keeping it hanged
            self.content.set_no_show_all(True)  # Prevent show_all from revealing it
            self.content.hide()
            print(f"[PATHWAY_PANEL] Hidden (still hanged)")
        else:
            # Hide floating window
            self.window.hide()
            print(f"[PATHWAY_PANEL] Window hidden")
    
    def show(self):
        """Show the panel (reveal if hanged, show window if floating - skeleton pattern).
        
        WAYLAND FIX: Use show() instead of show_all() to avoid Error 71.
        """
        print(f"[PATHWAY_PANEL] Showing panel...")
        
        if self.is_hanged and self.parent_container:
            # Re-enable show_all and show content (reveal)
            self.content.set_no_show_all(False)
            self.content.show()  # WAYLAND FIX: Don't use show_all()
            print(f"[PATHWAY_PANEL] Revealed (hanged)")
        else:
            # Show floating window
            self.window.show()  # WAYLAND FIX: Don't use show_all()
            print(f"[PATHWAY_PANEL] Window shown")
    
    # ========================================================================
    # PHASE 4: GtkStack Integration Methods
    # New architecture: Panels live in GtkStack, controlled by Master Palette
    # ========================================================================
    
    def add_to_stack(self, stack, container, panel_name='pathways'):
        """Add panel content to a GtkStack container (Phase 4: new architecture).
        
        WAYLAND FIX: Don't load window first, load content directly to avoid widget reparenting.
        
        Args:
            stack: GtkStack widget that will contain all panels
            container: GtkBox container within the stack for this panel
            panel_name: Name identifier for this panel in the stack ('pathways')
        """
        
        # WAYLAND FIX: Don't create window at all in stack mode
        # Just load the content widget directly
        if self.builder is None:
            # Validate UI file exists
            if not os.path.exists(self.ui_path):
                raise FileNotFoundError(f"Pathway panel UI file not found: {self.ui_path}")
            
            # Load the UI
            self.builder = Gtk.Builder.new_from_file(self.ui_path)
            
            # Extract ONLY the content (not the window)
            self.content = self.builder.get_object('pathway_panel_content')
            
            if self.content is None:
                raise ValueError("Object 'pathway_panel_content' not found in pathway_panel.ui")
            
            # Initialize controllers (but skip window-related stuff)
            self._setup_import_tab()
            self._setup_sbml_tab()
            self._setup_brenda_tab()
            self._setup_unified_ui_signals()
            
            # Get float button (won't work in stack mode, but keep reference)
            self.float_button = self.builder.get_object('float_button')
        
        # Add content directly to stack container (no reparenting needed)
        if self.content.get_parent() != container:
            # Remove from any previous parent
            current_parent = self.content.get_parent()
            if current_parent:
                current_parent.remove(self.content)
            container.add(self.content)
        
        # Mark as hanged in stack mode
        self.is_hanged = True
        self.parent_container = container
        self._stack = stack
        self._stack_panel_name = panel_name
        
    
    def show_in_stack(self):
        """Show this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        if not hasattr(self, '_stack') or not self._stack:
            return
        
        # Make stack visible
        if not self._stack.get_visible():
            self._stack.set_visible(True)
        
        # Set this panel as active child
        self._stack.set_visible_child_name(self._stack_panel_name)
        
        # WAYLAND FIX: Use show() on container, but explicitly show child widgets
        # that should be visible (to avoid show_all() protocol errors)
        if self.content:
            self.content.set_no_show_all(False)  # Re-enable show_all
            self.content.show()  # Show just the container
            
            # Explicitly show notebook and tabs (but not hidden dynamic boxes)
            notebook = self.builder.get_object('pathway_notebook')
            if notebook and not notebook.get_visible():
                notebook.show()
                
                # Show current tab's content (not all tabs)
                current_page_num = notebook.get_current_page()
                if current_page_num >= 0:
                    current_page = notebook.get_nth_page(current_page_num)
                    if current_page and not current_page.get_visible():
                        # Show the page container
                        current_page.show()
                        
                        # Show visible children (respect visible="False" in UI)
                        # This ensures radio buttons, entries, etc. that start visible are shown
                        self._show_visible_children(current_page)
        
        # Make container visible too
        if self.parent_container:
            self.parent_container.set_visible(True)
    
    def _show_visible_children(self, widget):
        """Recursively show children that have visible=True in their properties.
        
        This respects the initial visibility state from the UI file and avoids
        calling show_all() which causes Wayland Error 71.
        """
        if hasattr(widget, 'get_children'):
            for child in widget.get_children():
                # Check if child wants to be visible
                # get_no_show_all() returns True if widget should NOT be shown by show_all()
                # get_visible() returns current visibility
                # We want to show widgets that are marked visible in UI but not yet shown
                if child.get_visible():
                    # Widget is already visible, check its children
                    self._show_visible_children(child)
                elif not child.get_no_show_all():
                    # Widget wants to be visible but isn't yet
                    child.show()
                    self._show_visible_children(child)
                # else: widget has no_show_all=True or visible=False, leave it hidden
        
    
    def hide_in_stack(self):
        """Hide this panel in the GtkStack (Phase 4: Master Palette control)."""
        
        # Hide the content using no_show_all to prevent show_all from revealing it
        if self.content:
            self.content.set_no_show_all(True)
            self.content.hide()
        
        # Hide container too
        if self.parent_container:
            self.parent_container.set_visible(False)

        


def create_pathway_panel(ui_path=None, model_canvas=None, workspace_settings=None):
    """Convenience function to create and load the pathway panel loader.
    
    Args:
        ui_path: Optional path to pathway_panel.ui.
        model_canvas: Optional ModelCanvasManager for loading imported pathways.
        workspace_settings: Optional WorkspaceSettings for remembering user preferences.
        
    Returns:
        PathwayPanelLoader: The loaded pathway panel loader instance.
        
    Example:
        loader = create_pathway_panel(model_canvas=canvas_manager, workspace_settings=settings)
        loader.detach(main_window)  # Show as floating
        # or
        loader.attach_to(container)  # Attach to container
    """
    loader = PathwayPanelLoader(ui_path, model_canvas, workspace_settings)
    loader.load()
    return loader
