"""Model Canvas Loader/Controller.

This module manages the multi-document Petri Net drawing canvas.
The canvas supports multiple tabs (documents), each with a scrollable
drawing area for creating and editing Petri Net models.

Architecture:
    pass
- GtkNotebook: Multi-document tab container
- GtkScrolledWindow: Scrollable viewport for each document
- GtkDrawingArea: Canvas for drawing Petri Net objects (Places, Transitions, Arcs)

Future extensions:
    pass
- Drawing primitives: Place (circle), Transition (rectangle), Arc (arrow)
- Edit operations: select, move, draw, undo, redo
- Model overlay support for floating palettes
"""
import os
import sys
import math
import logging
from typing import Optional
from shypn.helpers.canvas_interaction_context import CanvasInteractionContext
from shypn.helpers.canvas_input_handler import CanvasInputCallbacks, CanvasInputHandler
try:
    from shypn.events import EventBus
except ImportError:
    EventBus = None  # type: ignore[assignment]
try:
    import gi
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')
    from gi.repository import Gtk, Gdk, Gio, GLib
    import time
except Exception as e:
    print('ERROR: GTK3 not available in model_canvas loader:', e, file=sys.stderr)
    sys.exit(1)
try:
    from shypn.data.model_canvas_manager import ModelCanvasManager
except ImportError as e:
    print(f'ERROR: Cannot import ModelCanvasManager: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.rendering import ModuleRenderer
except ImportError as e:
    print(f'Warning: ModuleRenderer not available: {e}', file=sys.stderr, flush=True)
    ModuleRenderer = None
try:
    from shypn.netobjs import Place, Transition, Arc
except ImportError as e:
    print(f'ERROR: Cannot import Petri net objects: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.canvas import CanvasOverlayManager
except ImportError as e:
    print(f'ERROR: Cannot import CanvasOverlayManager: {e}', file=sys.stderr)
    sys.exit(1)
try:
    from shypn.edit.palette_manager import PaletteManager
    from shypn.edit.tools_palette_new import ToolsPalette
    from shypn.edit.operations_palette_new import OperationsPalette
    # SwissKnifePalette - unified palette replacing ToolsPalette + OperationsPalette
    # PHASE 3 COMPLETE: Using new modular architecture with constant height + parameter panels
    from shypn.helpers.swissknife_palette_new import SwissKnifePalette
    from shypn.helpers.swissknife_tool_registry import ToolRegistry
except ImportError as e:
    print(f'ERROR: Cannot import new OOP palettes: {e}', file=sys.stderr)
    sys.exit(1)

# Import simulation controller for state-based permissions
try:
    from shypn.engine.simulation.controller import SimulationController
    # Import IDManager lifecycle integration
    from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
except ImportError as e:
    print(f'ERROR: Cannot import SimulationController: {e}', file=sys.stderr)
    sys.exit(1)

from shypn.helpers.canvas_layout_controller import CanvasLayoutController
from shypn.core.document_id import alloc_doc_id, doc_id
from shypn.helpers.document_session import DocumentSession
from shypn.canvas.canvas_renderer import CanvasRenderer
from shypn.canvas.canvas_context_menu_controller import CanvasContextMenuController
from shypn.helpers.document_panel_setup import DocumentPanelSetup


class ModelCanvasLoader:
    """Loader and controller for the model canvas (multi-document Petri Net editor)."""

    def __init__(self, ui_path=None):
        """Initialize the model canvas loader.
        
        Args:
            ui_path: Optional path to model_canvas.ui. If None, uses default location.
        """
        self.logger = logging.getLogger(__name__)
        
        if ui_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.normpath(os.path.join(script_dir, '..', '..', '..'))
            ui_path = os.path.join(repo_root, 'ui', 'canvas', 'model_canvas.ui')
        self.ui_path = ui_path
        self.builder = None
        self.container = None
        self.notebook = None
        self.document_count = 0
        # ── Sprint 18 — SessionRegistry replaces four parallel legacy dicts ──
        # ``sessions`` IS the registry.  The four proxy attributes below are
        # live dict-like views backed by it, so all existing external callers
        # (ViabilityPanel, TopologyPanel, experiments, etc.) continue to work
        # without modification.
        from shypn.helpers.session_registry import SessionRegistry
        self.sessions: SessionRegistry = SessionRegistry()
        self.canvas_managers = self.sessions.canvas_managers
        self.overlay_managers = self.sessions.overlay_managers
        self.palette_managers = {}  # New OOP palette managers (keyed by da, not session-scoped)
        
        # ═══════════════════════════════════════════════════════════════════
        # PER-DOCUMENT COMPONENTS ARCHITECTURE
        # ═══════════════════════════════════════════════════════════════════
        # Each document (canvas/tab) maintains completely isolated state via:
        #
        # 1. CORE COMPONENTS (overlay_managers[drawing_area]):
        #    - canvas_manager: ModelCanvasManager for places/transitions/arcs
        #    - simulation_controller: SimulationController with data_collector
        #    - swissknife_palette: SwissKnifePalette for tool selection
        #    - context_menu_handler: ContextMenuHandler for "Add to Analysis"
        #    - report_data: DocumentReportData for simulation metrics
        #
        # 2. PANEL LOADERS (overlay_managers[drawing_area].*_panel_loader):
        #    - analyses_panel_loader: AnalysesPanelLoader (transitions/places plots)
        #    - report_panel_loader: ReportPanelLoader (simulation tables)
        #    - viability_panel_loader: ViabilityPanelLoader (model repair)
        #    - pathway_panel_loader: PathwayPanelLoader (KEGG/BiGG/BRENDA)
        #    - topology_panel_loader: TopologyPanelLoader (structural analysis)
        #
        # 3. TAB SWITCH BEHAVIOR (_on_notebook_page_changed):
        #    CRITICAL: When tabs switch, ALL per-document components must update:
        #    - Context menu handler → current document's handler
        #    - Simulation controller → current document's controller  
        #    - Panel loaders → swap to current document's panels
        #    - Canvas manager → update for locality detection
        #
        # 4. INITIALIZATION PATTERN (in _setup_edit_palettes):
        #    - Create component for this document
        #    - Store in overlay_managers[drawing_area].component_name
        #    - ALWAYS update global reference (don't check if None)
        #    - Wire callbacks and connections
        #
        # This ensures complete state isolation between documents and proper
        # context switching when users navigate between tabs.
        # ═══════════════════════════════════════════════════════════════════
        
        # Simulation controllers - one per canvas
        # Canvas-centric design: Controllers stored by drawing_area, not palette.
        # This ensures wiring survives SwissPalette refactoring.
        # Access pattern: drawing_area → controller → state_detector, interaction_guard
        # Sprint 18: proxy backed by SessionRegistry (live view).
        self.simulation_controllers = self.sessions.simulation_controllers
        
        # GLOBAL-SYNC: Canvas lifecycle management
        # Initialize lifecycle system for coordinated component management
        try:
            from shypn.canvas.lifecycle import enable_lifecycle_system
            self.lifecycle_manager, self.lifecycle_adapter = enable_lifecycle_system(self)
            
            # Connect global IDManager to lifecycle scoping
            # This makes all ID generation canvas-scoped automatically
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
        except Exception as e:
            self.lifecycle_manager = None
            self.lifecycle_adapter = None
        
        self.parent_window = None
        self.persistency = None
        self.right_panel_loader = None
        self.report_panel_loader = None  # PHASE 1-2: For simulation results tables
        # Pathway Operations panel loader (for KEGG/SBML/BRENDA heuristics)
        self.pathway_panel_loader = None
        self.context_menu_handler = None
        self._input_handler = CanvasInputHandler(
            callbacks=CanvasInputCallbacks(
                show_object_context_menu=self._show_object_context_menu,
                show_canvas_context_menu=self._show_canvas_context_menu,
                on_file_save=lambda: (
                    self.file_explorer_panel.save_current_document()
                    if getattr(self, 'file_explorer_panel', None) else None
                ),
                on_file_save_as=lambda: (
                    self.file_explorer_panel.save_current_document_as()
                    if getattr(self, 'file_explorer_panel', None) else None
                ),
                on_file_open=lambda: (
                    self.file_explorer_panel.open_document()
                    if getattr(self, 'file_explorer_panel', None) else None
                ),
                on_add_document=lambda: (
                    self.add_document(replace_empty_default=False)
                    if hasattr(self, 'add_document') else None
                ),
                on_close_tab=self.close_tab,
                get_page_num_for_widget=self._get_canvas_page_num,
                get_parent_window=lambda: self.parent_window,
                overlay_managers=self.overlay_managers,
                canvas_context_menu_popdown=self._popdown_canvas_context_menu,
            ),
            logger=self.logger,
        )
        
        # Knowledge bases for intelligent model repair (Viability Panel)
        # One ModelKnowledgeBase instance per drawing_area
        # Sprint 18: proxy backed by SessionRegistry (live view).
        self.knowledge_bases = self.sessions.knowledge_bases
        
        # Project reference for structured save paths (pathways/, models/, metadata/)
        self.project = None
        

        # Track whether we've fully initialized the first page (page 0)
        self._first_page_initialized = False

        # Layout sub-controller — owns all _on_layout_* / _apply_specific_layout logic
        # overlay_managers is passed by reference (dict), so the controller always sees
        # the live state even after pages are added.
        self.layout_ctrl = CanvasLayoutController(
            self.overlay_managers,
            get_sbml_panel=lambda: getattr(self, 'sbml_panel', None),
        )

        # Sprint 21: canvas rendering delegated to CanvasRenderer
        self._renderer = CanvasRenderer(canvas_ctx=self._input_handler.canvas_ctx)

        # Sprint 22: context-menu pipeline delegated to CanvasContextMenuController
        self._ctx_menu_ctrl = CanvasContextMenuController(loader=self)

        # Subscribe to 'editor.close_requested' so the Open Editors panel ✕ button
        # triggers a proper tab close (with unsaved-changes dialog etc.)
        try:
            from shypn.events import EventBus
            EventBus.subscribe('editor.close_requested', self._on_editor_close_requested)
        except Exception:
            self.logger.debug("EventBus subscribe for 'editor.close_requested' failed", exc_info=True)

    def _on_editor_close_requested(self, event_data: dict):
        """Close the canvas tab matching the filepath in event_data.

        Called when the Open Editors panel ✕ button emits 'editor.close_requested'.
        Delegates to close_tab() which handles unsaved-changes confirmation and
        full cleanup, then emits 'file.closed' which removes the panel row.
        """
        filepath = event_data.get('filepath') if isinstance(event_data, dict) else None
        if not filepath or not self.notebook:
            return
        try:
            for page_num in range(self.notebook.get_n_pages()):
                page = self.notebook.get_nth_page(page_num)
                drawing_area = self._get_drawing_area_from_page(page)
                if drawing_area:
                    manager = self.canvas_managers.get(drawing_area)
                    if manager and getattr(manager, 'filepath', None) == filepath:
                        GLib.idle_add(self.close_tab, page_num)
                        return
        except Exception:
            self.logger.debug("_on_editor_close_requested failed", exc_info=True)

    # ------------------------------------------------------------------
    # Public helpers for per-document access
    # ------------------------------------------------------------------

    def get_current_model_manager(self):
        """Return the ModelCanvasManager for the active document/tab.

        This provides a single, stable way for UI panels (Pathway
        Operations, BRENDA, heuristics, etc.) to access the Petri net
        model for the currently selected document in the notebook.
        """
        try:
            if not self.notebook:
                return None
            page_num = self.notebook.get_current_page()
            if page_num < 0:
                return None
            page_widget = self.notebook.get_nth_page(page_num)
            if page_widget is None:
                return None

            # Robustly resolve the GtkDrawingArea for this page
            drawing_area = self._get_drawing_area_from_page(page_widget)
            if drawing_area is None:
                return None

            return self.canvas_managers.get(drawing_area)
        except Exception:
            return None
    
    def get_current_document_id(self) -> Optional[int]:
        """Get the document ID for the currently active tab.
        
        Returns:
            Document ID (id(drawing_area)) for the active tab, or None if no active tab.
        
        Example:
            document_id = loader.get_current_document_id()
            EventBus.emit('model.changed', data, document_id=document_id)
        
        Note:
            The document ID is the stable monotonic integer stamped on the
            GtkDrawingArea widget by alloc_doc_id() at tab-creation time.
            It is never reused within a process lifetime, unlike id().
        """
        try:
            if not self.notebook:
                return None
            page_num = self.notebook.get_current_page()
            if page_num < 0:
                return None
            page_widget = self.notebook.get_nth_page(page_num)
            if page_widget is None:
                return None
            
            drawing_area = self._get_drawing_area_from_page(page_widget)
            if drawing_area is None:
                return None
            
            return doc_id(drawing_area)
        except Exception:
            return None

    def get_current_session(self) -> 'DocumentSession | None':
        """Return the :class:`DocumentSession` for the currently active tab.

        Returns ``None`` if there is no active tab or the session has not yet
        been registered (which can happen transiently during canvas setup).
        """
        try:
            if not self.notebook:
                return None
            page_num = self.notebook.get_current_page()
            if page_num < 0:
                return None
            page_widget = self.notebook.get_nth_page(page_num)
            if page_widget is None:
                return None
            drawing_area = self._get_drawing_area_from_page(page_widget)
            if drawing_area is None:
                return None
            return self.sessions.get(drawing_area)
        except Exception:
            return None

    def get_session(self, drawing_area) -> 'DocumentSession | None':
        """Return the :class:`DocumentSession` for *drawing_area*, or ``None``."""
        return self.sessions.get(drawing_area)

    def get_document_id_for_manager(self, manager) -> Optional[int]:
        """Find the document ID for a given ModelCanvasManager.
        
        Args:
            manager: ModelCanvasManager instance to find document ID for
        
        Returns:
            Document ID (id(drawing_area)) or None if manager not found
        
        Example:
            document_id = loader.get_document_id_for_manager(my_manager)
            EventBus.subscribe('simulation.progress', handler, document_id=document_id)
        """
        for drawing_area, mgr in self.canvas_managers.items():
            if mgr is manager:
                return doc_id(drawing_area)
        return None
    
    def get_drawing_area_for_document_id(self, document_id: int):
        """Reverse lookup: get drawing_area widget from document ID.
        
        Args:
            document_id: Document ID (result of id(drawing_area))
        
        Returns:
            GtkDrawingArea widget or None if not found
        
        Example:
            drawing_area = loader.get_drawing_area_for_document_id(document_id)
            manager = loader.canvas_managers.get(drawing_area)
        
        Note:
            Use get_current_session() / get_session(drawing_area) for new code.
            This lookup is primarily for EventBus internal routing.
        """
        for drawing_area in self.canvas_managers.keys():
            if doc_id(drawing_area) == document_id:
                return drawing_area
        return None

    def load(self, create_initial_document=True):
        """Load the canvas UI and return the container.
        
        Args:
            create_initial_document: If True, creates the default document during load.
                                    If False, caller must create document after wiring dependencies.
        
        Returns:
            Gtk.Box: The model canvas container with notebook.
            
        Raises:
            FileNotFoundError: If UI file doesn't exist.
            ValueError: If container or notebook not found in UI file.
        """
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'Model canvas UI file not found: {self.ui_path}')
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        self.container = self.builder.get_object('model_canvas_container')
        self.notebook = self.builder.get_object('canvas_notebook')
        if self.container is None:
            raise ValueError("Object 'model_canvas_container' not found in model_canvas.ui")
        if self.notebook is None:
            raise ValueError("Object 'canvas_notebook' not found in model_canvas.ui")
        
        # Override theme's notebook styling - use light, clean colors
        css_provider = Gtk.CssProvider()
        css = b"""
        #canvas_notebook {
            background: white;
        }
        #canvas_notebook > header {
            background: white;
        }
        #canvas_notebook > header > tabs > tab {
            background: white;
        }
        #canvas_notebook > header > tabs > tab:checked {
            background: white;
        }
        #canvas_notebook > stack {
            background: white;
        }
        """
        css_provider.load_from_data(css)
        style_context = self.notebook.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 1)
        
        # Apply global CSS for canvas object tooltips - green background with black text
        tooltip_css_provider = Gtk.CssProvider()
        tooltip_css = b"""
        tooltip {
            background-color: #22cc22;
            color: #000000;
            border: 1px solid #1a991a;
            border-radius: 3px;
            padding: 4px 8px;
        }
        tooltip * {
            color: #000000;
        }
        tooltip label {
            color: #000000;
        }
        """
        tooltip_css_provider.load_from_data(tooltip_css)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            tooltip_css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # CRITICAL FIX: Remove default tab from UI file and create fresh one programmatically
        # 
        # CERTIFICATION: The default canvas is NOT created from any notebook/XML file.
        # 
        # The UI file (model_canvas.ui) contains a pre-baked GtkNotebook tab for convenience
        # during UI design, but this tab has timing issues with controller wiring and causes
        # inconsistent behavior compared to File→New canvases.
        # 
        # SOLUTION: We ALWAYS delete ALL pages from the UI file and create a fresh canvas
        # programmatically using add_document(). This ensures:
        # 1. Default canvas is created the SAME way as File→New
        # 2. NO notebook XML content is loaded
        # 3. Consistent initialization across all canvas creation scenarios
        # 4. Proper controller wiring and viability panel state
        # 
        self.document_count = self.notebook.get_n_pages()
        if self.document_count > 0:
            # Remove all pages from the UI file (typically 1 pre-baked page)
            while self.notebook.get_n_pages() > 0:
                self.notebook.remove_page(0)
        
        # Verify notebook is empty before proceeding
        assert self.notebook.get_n_pages() == 0, "Failed to remove UI file pages - notebook should be empty"
        
        self.notebook.connect('switch-page', self._on_notebook_page_changed)
        # Intercept page creation so page 0 runs the same init flow
        self.notebook.connect('page-added', self._on_notebook_page_added)
        
        # ═══════════════════════════════════════════════════════════════════
        # GLOBAL CANVAS STATE CYCLE: Default Canvas Creation
        # ═══════════════════════════════════════════════════════════════════
        # Create fresh default tab using add_document() for consistent initialization.
        # This ensures the default tab follows the SAME normalized path as File→New.
        # 
        # The notebook itself is defined in XML UI file (model_canvas.ui), but we
        # ALWAYS remove any pre-baked tabs and create programmatically to ensure:
        # 1. NO XML/notebook content is loaded from UI file
        # 2. Canvas starts completely empty
        # 3. Consistent initialization via _on_notebook_page_added() hook
        # 
        # ARCHITECTURE: All canvas initialization is handled by the page-added hook.
        # The hook fires when add_document() calls notebook.append_page() and performs:
        # - Data collector wiring
        # - Right panel model setup
        # - Context menu handler setup
        # - Lifecycle activation (switch_to_canvas, set_scope)
        # - Sets _first_page_initialized = True
        # 
        # This is the SINGLE SOURCE OF TRUTH for first-page initialization.
        # No manual wiring is needed here - trust the normalized flow.
        # ═══════════════════════════════════════════════════════════════════
        if create_initial_document:
            page_index, drawing_area = self.add_document(filename='default')
            
            # Set context menu handler on model_canvas_loader for canvas object menus
            if self.right_panel_loader and self.right_panel_loader.context_menu_handler:
                if not self.context_menu_handler:
                    self.set_context_menu_handler(self.right_panel_loader.context_menu_handler)
            
            # Notify Pathway Operations panel for BRENDA/KEGG category model resolution
            try:
                if self.pathway_panel_loader and hasattr(self.pathway_panel_loader, 'set_model_canvas'):
                    self.pathway_panel_loader.set_model_canvas(self)
            except (AttributeError, TypeError) as e:
                self.logger.debug(f"Failed to notify pathway panel of model canvas: {e}")
        
        return self.container

    def _on_notebook_page_added(self, notebook, child, page_num):
        """Ensure newly added pages (especially page 0) get full initialization.
        
        ═══════════════════════════════════════════════════════════════════
        GLOBAL CANVAS STATE CYCLE: Single Source of Truth for First Page
        ═══════════════════════════════════════════════════════════════════
        This hook is called when a page is added to the notebook, but it fires
        TOO EARLY - before _setup_canvas_manager() completes. Therefore, this
        hook cannot access the manager from canvas_managers dictionary.
        
        The actual first-page initialization (context menu handler wiring, etc.)
        happens at the END of add_document() after the manager is fully created.
        
        This hook is kept for future extensibility and to maintain the page-added
        signal connection, but the heavy lifting is done in add_document().
        ═══════════════════════════════════════════════════════════════════
        """
        try:
            # Only do this once for the first page
            if page_num == 0 and not getattr(self, '_first_page_initialized', False):
                # Wire data collector (this can happen early)
                self._wire_data_collector_for_page(child)

                # Note: Context menu handler wiring happens in add_document()
                # after _setup_canvas_manager() completes, because the manager
                # doesn't exist in canvas_managers yet when this hook fires.

                # Ensure lifecycle active canvas and ID scope are set
                if drawing_area:
                    if self.lifecycle_adapter:
                        try:
                            self.lifecycle_adapter.switch_to_canvas(drawing_area)
                        except (AttributeError, TypeError, RuntimeError) as e:
                            self.logger.debug(f"Failed to switch lifecycle adapter to canvas: {e}")
                    try:
                        if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                            from shypn.data.canvas.id_manager import set_lifecycle_scope_manager
                            set_lifecycle_scope_manager(self.lifecycle_manager.id_manager)
                            self.lifecycle_manager.id_manager.set_scope(f"canvas_{id(drawing_area)}")
                    except (AttributeError, TypeError, RuntimeError) as e:
                        self.logger.debug(f"Failed to set lifecycle ID scope on page add: {e}")

                self._first_page_initialized = True
        except Exception:
            # Defensive: never raise from GTK signal handlers
            self.logger.debug("GTK page-added signal handler failed", exc_info=True)

    def _wire_data_collector_for_page(self, page):
        """Wire the data collector to the right panel for a given page.
        
        Extracts the drawing_area from the page and wires its data collector.
        
        Args:
            page: Notebook page widget (Gtk.Overlay or Gtk.ScrolledWindow)
        """
        # Always resolve the actual GtkDrawingArea via helper to avoid viewport mixups
        drawing_area = self._get_drawing_area_from_page(page)
        
        if self.right_panel_loader and drawing_area:
            # Get simulate_tools_palette from SwissKnife registry
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                
                # SwissKnifePalette stores SimulateToolsPaletteLoader in widget_palette_instances
                if hasattr(overlay_manager, 'swissknife_palette'):
                    swissknife = overlay_manager.swissknife_palette
                    
                    # NEW architecture: widget_palette_instances is in swissknife.registry
                    # OLD architecture: widget_palette_instances is directly on swissknife
                    simulate_tools_palette = None
                    
                    if hasattr(swissknife, 'registry') and hasattr(swissknife.registry, 'widget_palette_instances'):
                        simulate_tools_palette = swissknife.registry.widget_palette_instances.get('simulate')
                    elif hasattr(swissknife, 'widget_palette_instances'):
                        simulate_tools_palette = swissknife.widget_palette_instances.get('simulate')
                    
                    if simulate_tools_palette and hasattr(simulate_tools_palette, 'data_collector'):
                        data_collector = simulate_tools_palette.data_collector
                        self.right_panel_loader.set_data_collector(data_collector)
                        return True
        return False

    def _on_notebook_page_changed(self, notebook, page, page_num):
        """Handle notebook page switch.
        
        Args:
            notebook: GtkNotebook instance.
            page: The new page widget.
            page_num: The index of the new page.
        """
        # print(f"\n[TAB_SWITCH] ==========================================")
        
        # Update active tab styling - remove 'active' class from all tabs, add to current
        for i in range(notebook.get_n_pages()):
            page_widget = notebook.get_nth_page(i)
            tab_widget = notebook.get_tab_label(page_widget)
            if tab_widget and isinstance(tab_widget, Gtk.Box):
                style_context = tab_widget.get_style_context()
                if i == page_num:
                    style_context.add_class('active')
                else:
                    style_context.remove_class('active')
        
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        
        # ============================================================
        # EVENTBUS: Emit document.focused event for panel coordination
        # ============================================================
        # Emit event EARLY so panels can respond and handle their own updates
        # This replaces manual panel swapping code with event-driven architecture
        if drawing_area:
            canvas_manager = self.canvas_managers.get(drawing_area)
            overlay_manager = self.overlay_managers.get(drawing_area)
            
            if canvas_manager and overlay_manager:
                document_id = doc_id(drawing_area)  # use stable ID, not id()
                from shypn.events import EventBus
                EventBus.emit('document.focused', {
                    'drawing_area': drawing_area,
                    'canvas_manager': canvas_manager,
                    'overlay_manager': overlay_manager,
                    'page_num': page_num
                }, document_id=document_id)
        
        # ============================================================
        # GLOBAL-SYNC: Switch canvas context when tab changes
        # ============================================================
        # ═══════════════════════════════════════════════════════════════════
        # CERTIFICATION: Lifecycle State Preservation During Tab Switch
        # ═══════════════════════════════════════════════════════════════════
        # This tab switch handler PRESERVES per-document canvas state by
        # coordinating with the lifecycle system. It does NOT override or
        # reset any canvas state - it only switches the active context.
        #
        # LIFECYCLE SWITCH OPERATION:
        # 1. lifecycle_adapter.switch_to_canvas(drawing_area)
        #    - Updates lifecycle_manager's active canvas context
        #    - Sets ID scope: "canvas_{id}" for this drawing_area
        #    - Future ID generation (P1, T1, A1) scoped to this canvas
        #
        # 2. STATE PRESERVATION GUARANTEE:
        #    - Does NOT call reset_canvas() or clear objects
        #    - Does NOT modify manager.places/transitions/arcs
        #    - Does NOT reset simulation controller state
        #    - Does NOT clear dirty flags or file paths
        #    - ONLY switches which canvas context is active
        #
        # 3. PERSISTENCY UPDATE:
        #    - Updates file explorer display to show active canvas filename
        #    - Does NOT modify canvas state, only UI reflection
        #
        # 4. PANEL SYNCHRONIZATION:
        #    - Wires data collector for active canvas (simulation results)
        #    - Clears global Analyses panel selections (shared across canvases)
        #    - Swaps per-document Viability Panel (line 466)
        #    - Swaps per-document Report Panel (line 479)
        #
        # ANTI-OVERRIDE GUARANTEE:
        # Tab switch is READ-ONLY for canvas state. No modifications occur.
        # All per-document state remains intact and isolated per canvas.
        # ═══════════════════════════════════════════════════════════════════
        if self.lifecycle_adapter and drawing_area:
            try:
                self.lifecycle_adapter.switch_to_canvas(drawing_area)
            except Exception as e:
                self.logger.debug(f"Failed to switch canvas context: {e}")
                pass  # Failed to switch canvas context
        
        if self.persistency:
            if drawing_area and drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                filename = manager.filename
                if manager.is_default_filename():
                    self.persistency.set_filepath(None)
                else:
                    pass
        
        # Wire data collector for the switched-to page
        wired = self._wire_data_collector_for_page(page)
        
        # ============================================================
        # EVENTBUS MIGRATION: Analyses panel clearing removed
        # ============================================================
        # Per-document architecture eliminates need for manual clearing.
        # Each document has its own AnalysesPanelLoader instance that preserves
        # state across tab switches. EventBus handles show/hide automatically.
        
        # ============================================================
        # Update context menu handler for current document
        # ============================================================
        if self.right_panel_loader and drawing_area:
            if drawing_area in self.canvas_managers:
                manager = self.canvas_managers[drawing_area]
                self.right_panel_loader.set_model(manager)
                
                # CRITICAL: Explicitly ensure context menu handler has the correct model
                # This must happen EVERY time we switch tabs to ensure locality detection works
                if self.right_panel_loader.context_menu_handler:
                    self.right_panel_loader.context_menu_handler.set_model(manager)
            
            if self.right_panel_loader.context_menu_handler and (not self.context_menu_handler):
                self.set_context_menu_handler(self.right_panel_loader.context_menu_handler)
        
        # ============================================================
        # CRITICAL: Update context menu handler for per-document analyses panel
        # Each document has its own analyses panel with unique context menu handler
        # ============================================================
        if drawing_area and drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            
            # Update context menu handler to current document's handler
            if hasattr(overlay_manager, 'context_menu_handler') and overlay_manager.context_menu_handler:
                # Update model_canvas_loader's handler to point to current document's handler
                self.set_context_menu_handler(overlay_manager.context_menu_handler)
            
            # Update simulation controller reference for SwissKnife palette
            if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller:
                # Store reference for quick access
                current_controller = overlay_manager.simulation_controller
                
                # Update SwissKnife palette if it exists
                if hasattr(overlay_manager, 'swissknife_palette') and overlay_manager.swissknife_palette:
                    swissknife = overlay_manager.swissknife_palette
                    if hasattr(swissknife, 'simulation_controller'):
                        swissknife.simulation_controller = current_controller

        # ============================================================
        # EVENTBUS MIGRATION COMPLETE: Panel swapping via document.focused
        # ============================================================
        # All per-document panels now subscribe to 'document.focused' events
        # and handle their own show/hide/refresh logic automatically.
        #
        # Panels that respond to document.focused events:
        # - PathwayPanelLoader (_on_document_focused) - Lines 207-243
        # - AnalysesPanelLoader (_on_document_focused) - Lines 201-245
        # - TopologyPanelLoader (_on_document_focused) - Lines 188+
        # - ReportPanelLoader (_on_document_focused) - Lines 90, 302-370
        # - ViabilityPanelLoader (if migrated to EventBus)
        #
        # Manual (~300 lines) panel swapping code removed (Week 3 - Feb 2026).
        # EventBus approach provides clean separation: controller emits event,
        # panels respond independently. Reduces _on_notebook_page_changed() from
        # 577 lines to ~100 lines.

    def _on_tab_close_clicked(self, button, page_widget):
        """Handle tab close button click.
        
        ═══════════════════════════════════════════════════════════════════
        CERTIFICATION: Tab [X] Button → Complete File Close Operation
        ═══════════════════════════════════════════════════════════════════
        Clicking the [X] button on a tab triggers close_tab() which performs
        ALL safety checks and cleanup equivalent to File→Close:
        
        1. Checks for unsaved changes (shows Save/Discard/Cancel dialog)
        2. Performs complete lifecycle cleanup (destroys all components)
        3. Removes all per-document state (managers, controllers, palettes)
        4. Prevents data loss (user must explicitly confirm discard)
        
        See close_tab() method (line 659) for complete certification of
        safety checks, cleanup operations, and equivalence to File→Close.
        ═══════════════════════════════════════════════════════════════════
        
        Args:
            button: The close button that was clicked.
            page_widget: The page widget (overlay) to close.
        """
        page_num = self.notebook.page_num(page_widget)
        if page_num == -1:
            return
        self.close_tab(page_num)

    def _create_tab_label(self, filename='default', is_modified=False):
        """Create a tab label with file icon, filename, and close button.
        
        Args:
            filename: Document filename (without extension, or None for default)
            is_modified: Whether document has unsaved changes
            
        Returns:
            tuple: (tab_box, label_widget, close_button) for later updates
        """
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=3)
        
        # Apply CSS styling for elevated tab appearance
        css_provider = Gtk.CssProvider()
        css = b"""
        .tab-box {
            padding: 2px 6px;
            border: 1px solid #ccc;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            background: #f5f5f5;
            min-height: 18px;
            margin-top: 0;
            margin-bottom: -1px;
            margin-left: 0;
            margin-right: -1px;
        }
        .tab-box:hover {
            background: #ffffff;
            border-color: #999;
        }
        .tab-box.active {
            background: #ffffff;
            border-color: #aaa;
            border-width: 1px;
            font-weight: bold;
        }
        .tab-box.active label {
            color: white;
        }
        """
        css_provider.load_from_data(css)
        style_context = tab_box.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        style_context.add_class('tab-box')
        
        # File type icon (document icon for Petri nets) - using SMALL_TOOLBAR for compact size
        file_icon = Gtk.Image.new_from_icon_name('text-x-generic', Gtk.IconSize.SMALL_TOOLBAR)
        file_icon.show()
        tab_box.pack_start(file_icon, False, False, 0)
        
        # Use 'default.shy' if no filename provided
        if not filename or filename == 'default':
            filename = 'default.shy'
        elif not filename.endswith('.shy'):
            filename = f"{filename}.shy"
        
        # Filename label - expand to show full name without ellipsis
        display_name = f"{filename}{'*' if is_modified else ''}"
        tab_label = Gtk.Label(label=display_name)
        # Don't truncate - let tab expand to fit full filename
        # tab_label.set_ellipsize(3)  # Removed - show full text
        # tab_label.set_max_width_chars(20)  # Removed - no width limit
        tab_label.set_xalign(0.0)  # Left align
        tab_label.show()
        tab_box.pack_start(tab_label, expand=True, fill=True, padding=0)
        
        # Close button (X) - using MENU size for compact appearance
        close_button = Gtk.Button()
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_focus_on_click(False)
        close_icon = Gtk.Image.new_from_icon_name('window-close-symbolic', Gtk.IconSize.MENU)
        close_button.set_image(close_icon)
        close_button.show()
        tab_box.pack_start(close_button, False, False, 0)
        
        tab_box.show()
        
        return (tab_box, tab_label, close_button)

    def _update_tab_label(self, page_widget, filename='default', is_modified=False):
        """Update tab label for a page with new filename and modification state.
        
        Args:
            page_widget: The page widget (Gtk.Overlay) whose tab to update
            filename: New filename (without extension, or None for default)
            is_modified: Whether document has unsaved changes
        """
        tab_widget = self.notebook.get_tab_label(page_widget)
        if not tab_widget or not isinstance(tab_widget, Gtk.Box):
            return
        
        # Ensure filename is a string (convert if needed)
        filename = str(filename) if filename is not None else 'default'
        
        # Ensure is_modified is a boolean
        is_modified = bool(is_modified)
        
        # Use 'default.shy' if no filename provided
        if not filename or filename == 'default':
            filename = 'default.shy'
        elif not filename.endswith('.shy'):
            filename = f"{filename}.shy"
        
        # Find the label in the tab box (it's the second child after icon)
        children = tab_widget.get_children()
        if len(children) >= 2:
            label = children[1]  # Index 1 is the label (after icon)
            if isinstance(label, Gtk.Label):
                display_name = f"{filename}{'*' if is_modified else ''}"
                label.set_text(display_name)

    def update_current_tab_label(self, filename='default', is_modified=False):
        """Update the current (active) tab's label with new filename.
        
        Public method to be called when a file is opened or saved.
        
        Args:
            filename: New filename (can include or exclude .shy extension)
            is_modified: Whether document has unsaved changes
        """
        current_page = self.notebook.get_current_page()
        if current_page < 0:
            return
        page_widget = self.notebook.get_nth_page(current_page)
        if page_widget:
            self._update_tab_label(page_widget, filename, is_modified)

    def close_tab(self, page_num):
        """Close a tab after checking for unsaved changes.
        
        ═══════════════════════════════════════════════════════════════════
        CERTIFICATION: Tab Close (*) Performs Complete File Close
        ═══════════════════════════════════════════════════════════════════
        Closing a tab via the [X] button is EQUIVALENT to File→Close and
        performs ALL necessary safety checks and cleanup operations.
        
        SAFETY CHECKS (Phase 1 - Pre-Close Validation):
        
        1. UNSAVED CHANGES DETECTION
           - Checks manager.is_dirty flag (per-document modified state)
           - If dirty: Shows modal dialog with 3 options:
             * "Save": Proceeds with save operation, then closes
             * "Discard Changes": Closes without saving (data loss confirmed)
             * "Cancel": Aborts close operation, keeps tab open
           - Dialog implementation: persistency.check_unsaved_changes() (line 269)
           - Parent window set for Wayland transient relationship
           - Modal dialog blocks until user responds
        
        2. USER CONFIRMATION
           - Tab switches to the one being closed (gives context)
           - User sees EXACT document being closed
           - If cancelled: Switches back to original tab (line 689)
           - No accidental closes - user explicitly confirms
        
        CLEANUP OPERATIONS (Phase 2 - Resource Disposal):
        
        3. GTK WIDGET REMOVAL
           - self.notebook.remove_page(page_num)
           - Removes tab from notebook widget
           - GTK destroys widget hierarchy automatically
        
        4. LIFECYCLE SYSTEM CLEANUP
           - lifecycle_adapter.destroy_canvas(drawing_area) (line 694)
           - Lifecycle manager operations:
             * Stops running simulation (controller.stop())
             * Cleans up palette (palette.cleanup())
             * Clears step listeners (prevents callbacks to destroyed objects)
             * Deletes ID scope (frees P1-Pn, T1-Tn, A1-An counters)
             * Removes from canvas registry
           - See: canvas/lifecycle/lifecycle_manager.py destroy_canvas() (line 390)
        
        5. PER-DOCUMENT COMPONENT CLEANUP
           - Removes from canvas_managers{} dictionary (line 699)
           - Removes from simulation_controllers{} dictionary (line 701)
           - Removes from overlay_managers{} dictionary (line 703)
             * Calls overlay_manager.cleanup_overlays()
             * Clears all palette references
             * Prevents memory leaks from circular references
           - Removes from knowledge_bases{} dictionary (line 708)
           - See: canvas/canvas_overlay_manager.py cleanup_overlays() (line 188)
        
        6. AUTOMATIC DEFAULT CANVAS CREATION
           - If last tab closed: Creates new default canvas (line 712)
           - Ensures application never has zero canvases
           - User always has a working canvas available
        
        EQUIVALENCE TO FILE→CLOSE:
        
        ✓ Same unsaved changes dialog
        ✓ Same user confirmation flow
        ✓ Same cleanup operations
        ✓ Same lifecycle coordination
        ✓ Same resource disposal
        ✓ Tab close [X] IS File→Close
        
        SAFETY GUARANTEES:
        
        ✓ Cannot close with unsaved changes without confirmation
        ✓ User explicitly chooses: Save / Discard / Cancel
        ✓ All per-document state properly disposed
        ✓ No memory leaks (palettes, controllers, managers cleaned)
        ✓ No dangling references (lifecycle removes all registrations)
        ✓ No zombie simulations (simulation stopped before cleanup)
        ✓ No callback errors (step listeners cleared)
        ✓ Application never enters invalid state (auto-creates default)
        
        MULTI-DOCUMENT ISOLATION:
        
        ✓ Closing one tab does NOT affect other tabs
        ✓ Each canvas has independent state (lifecycle ensures isolation)
        ✓ Other tabs continue working normally
        ✓ Simulation in other tabs unaffected
        ✓ Dirty flags per-document (closing clean tab doesn't prompt)
        
        WAYLAND COMPATIBILITY:
        
        ✓ Dialog has parent window set (prevents protocol errors)
        ✓ Modal dialog properly blocks user input
        ✓ Tab switch logic preserves focus
        ✓ No race conditions with async dialog
        
        See also:
        - file/netobj_persistency.py check_unsaved_changes() (line 269)
        - canvas/lifecycle/lifecycle_manager.py destroy_canvas() (line 390)
        - canvas/canvas_overlay_manager.py cleanup_overlays() (line 188)
        ═══════════════════════════════════════════════════════════════════
        
        Args:
            page_num: Index of the tab to close.
            
        Returns:
            bool: True if tab was closed, False if user cancelled.
        """
        if page_num < 0 or page_num >= self.notebook.get_n_pages():
            return False
        page = self.notebook.get_nth_page(page_num)
        drawing_area = None
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
        if self.persistency and drawing_area:
            manager = self.canvas_managers.get(drawing_area)
            if manager:
                current_page = self.notebook.get_current_page()
                current_widget = self.notebook.get_nth_page(current_page)
                self.notebook.set_current_page(page_num)
                if not self.persistency.check_unsaved_changes():
                    self.notebook.set_current_page(current_page)
                    return False
        self.notebook.remove_page(page_num)
        
        # ============================================================
        # GLOBAL-SYNC: Destroy canvas in lifecycle system
        # ============================================================
        if self.lifecycle_adapter and drawing_area:
            try:
                self.lifecycle_adapter.destroy_canvas(drawing_area)
            except Exception as e:
                self.logger.debug(f"Failed to destroy canvas in lifecycle: {e}")

        # ── Sprint 18: single-session teardown ────────────────────────────
        # Pop the session (removes it from the SessionRegistry so all four
        # proxy views stop returning data for this drawing_area), then run
        # full teardown — EventBus.clear_document + panel cleanup +
        # overlay_manager.cleanup_overlays.
        #
        # The EventBus 'file.closed' emit reads filepath from the session
        # BEFORE the pop so the reference is still valid.
        session = self.sessions.pop(drawing_area, None) if drawing_area else None
        if session is not None:
            # Emit file.closed so Open Editors panel removes the entry
            try:
                import time
                from shypn.events import EventBus
                _fp = getattr(session.canvas_manager, 'filepath', None)
                if _fp:
                    EventBus.emit('file.closed', {'filepath': _fp, 'timestamp': time.time()})
            except Exception:
                self.logger.debug("EventBus emit 'file.closed' failed", exc_info=True)
            session.teardown()
        # palette_managers is not session-scoped — clean it up manually
        if drawing_area and drawing_area in self.palette_managers:
            del self.palette_managers[drawing_area]
        # ──────────────────────────────────────────────────────────────────

        if self.notebook.get_n_pages() == 0:
            # ═══════════════════════════════════════════════════════════════════
            # GLOBAL CANVAS STATE CYCLE: Auto-Recreation After Last Tab Close
            # ═══════════════════════════════════════════════════════════════════
            # When the last tab is closed, recreate a fresh default canvas.
            # This follows the EXACT SAME normalized flow as File→New:
            # 
            # 1. Reset _first_page_initialized to allow hook to fire
            # 2. Call add_document() which triggers _on_notebook_page_added()
            # 3. Hook performs COMPLETE initialization (see lines 331-371):
            #    - Data collector wiring
            #    - Right panel model setup
            #    - Context menu handler setup
            #    - Lifecycle activation (switch_to_canvas, set_scope)
            #    - Sets _first_page_initialized = True
            # 
            # NO manual wiring is performed here - trust the normalized flow.
            # This ensures the auto-recreated canvas behaves IDENTICALLY to
            # the startup default canvas and File→New canvases.
            # ═══════════════════════════════════════════════════════════════════
            self._first_page_initialized = False
            page_index, new_drawing = self.add_document(filename='default')
        return True

    def is_current_tab_empty_default(self):
        """Check if current tab is an empty default tab that can be replaced.
        
        DEPRECATED: This feature has been disabled. Users must manually close default tabs.
        
        Returns:
            bool: Always returns False (auto-replacement disabled)
        """
        # Auto-replacement disabled - users manually close default tab if unwanted
        return False

    def _get_drawing_area_from_page(self, page_widget):
        """Extract drawing area from a notebook page widget.
        
        Args:
            page_widget: Notebook page widget (Gtk.Overlay or Gtk.ScrolledWindow)
            
        Returns:
            Gtk.DrawingArea or None
        """
        # Notebook page structure is: Gtk.Overlay → Gtk.ScrolledWindow → Gtk.Viewport → Gtk.DrawingArea
        # Gtk.ScrolledWindow auto-wraps its child in a Gtk.Viewport at runtime.
        # Always descend through the Viewport to return the actual Gtk.DrawingArea.
        widget = None
        if isinstance(page_widget, Gtk.Overlay):
            scrolled = page_widget.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                widget = scrolled.get_child()
        elif isinstance(page_widget, Gtk.ScrolledWindow):
            widget = page_widget.get_child()

        # If the immediate child is a GtkViewport, get its child (the DrawingArea)
        if widget is not None and hasattr(widget, 'get_child'):
            inner = widget.get_child()
            if inner is not None:
                widget = inner

        # Ensure the returned widget is the GtkDrawingArea instance
        return widget

    def add_document(self, title=None, filename=None, replace_empty_default=True):
        """Add a new document (tab) to the canvas.
        
        ═══════════════════════════════════════════════════════════════════
        CERTIFICATION: ALL canvas creation flows use add_document()
        ═══════════════════════════════════════════════════════════════════
        
        This method is the SINGLE, UNIFIED entry point for ALL canvas creation
        in the application. Every canvas tab goes through this exact code path:
        
        1. **Startup (Default Canvas)**
           - model_canvas_loader.load() → add_document(filename='default')
           - Line 186 in load() method
        
        2. **File → New**
           - User clicks File → New in file explorer
           - file_explorer_panel._on_new_file() → canvas_loader.add_document()
           - Line 1923 in file_explorer_panel.py
        
        3. **File → Open (Load .shy file)**
           - User opens existing .shy file
           - file_explorer_panel._load_document_into_canvas() → canvas_loader.add_document()
           - Line 1808 in file_explorer_panel.py
           - Creates NEW canvas, then loads objects into it
        
        4. **Pathway Import (KEGG/SBML)**
           - Pathway imports use the SAME flow as File → Open
           - Import creates DocumentModel → file operations load it
           - Goes through _load_document_into_canvas() → add_document()
        
        5. **Test Suite**
           - All tests use add_document() to create canvases
           - See test_phase4_ui_wiring.py for examples
        
        CONSISTENCY GUARANTEE:
        - ALL canvases created from canvas_tab_template.ui
        - NO canvases created from notebook XML, .ipynb, or model files
        - IDENTICAL initialization: _setup_canvas_manager() → _setup_edit_palettes()
        - SAME controller wiring, Report Panel setup, viability panel creation
        - CONSISTENT GTK widget hierarchy for Wayland compatibility
        
        The template (canvas_tab_template.ui) contains ONLY GTK widget definitions.
        Model data (places, transitions, arcs) is loaded AFTER canvas creation via:
        - manager.load_objects() for file operations
        - manager.add_place/transition/arc() for interactive drawing
        
        ═══════════════════════════════════════════════════════════════════
        
        Args:
            title: Optional title for the new document tab (deprecated, use filename).
            filename: Base filename without extension (default: "default").
            replace_empty_default: DEPRECATED - No longer used. Always creates new tab.
            
        Returns:
            tuple: (page_index, drawing_area) for the new document.
        
        ═══════════════════════════════════════════════════════════════════
        CERTIFICATION: Complete Per-Document State Initialization
        ═══════════════════════════════════════════════════════════════════
        
        Every canvas created via add_document() receives COMPLETE initialization
        of all per-document state, algorithms, and utilities. This certification
        documents ALL components initialized for File→New and all other paths.
        
        PER-DOCUMENT COMPONENTS INITIALIZED (in order):
        
        1. **ModelCanvasManager** (line 836: _setup_canvas_manager)
           - DocumentController: Petri net objects, ID generation
           - IDManager: Isolated P1-Pn, T1-Tn, A1-An counters
           - ViewportController: Zoom, pan, viewport state
           - SelectionManager: Multi-object selection
           - ObjectEditingTransforms: Move, rotate, align operations
           - RectangleSelection: Drag-select capability
           - TransformationManager: Canvas rotation/transforms
           - Dirty state tracking: Modified flag, change callbacks
           - File state: filepath, _is_dirty, on_dirty_changed callback
           - View persistence: save/load zoom/pan state
        
        2. **SimulationController** (line 1426: _setup_edit_palettes)
           - Per-canvas simulation state machine
           - TransitionState tracking (enabled/disabled/source)
           - Stochastic scheduler integration
           - Rate computation for transitions
           - Token movement and marking updates
           - Simulation callbacks (on_simulation_complete)
           - Stored in: self.simulation_controllers[drawing_area]
        
        3. **Knowledge Base** (line 900: _setup_canvas_manager)
           - ModelKnowledgeBase for intelligent repair
           - Rule-based viability detection
           - Stored in: self.knowledge_bases[drawing_area]
           - Linked to: manager.knowledge_base
        
        4. **Viability Panel** (line 1566: _setup_edit_palettes)
           - PER-DOCUMENT ViabilityPanel instance
           - Independent issue tracking per model
           - Connected to simulation_controller.on_simulation_complete
           - Wired to drawing_area (knows which document it belongs to)
           - Stored in: overlay_managers[drawing_area].viability_panel_loader
        
        5. **Report Panel** (line 1539: _setup_edit_palettes)
           - PER-DOCUMENT ReportPanel instance
           - Simulation results display (step tables, metrics)
           - Connected to simulation_controller
           - Stored in: overlay_managers[drawing_area].report_panel_loader
        
        6. **Right Panel (Transition Rate Panel)** (line 1516: _setup_edit_palettes)
           - PER-DOCUMENT TransitionRatePanel instance
           - Rate editing for selected transitions
           - Connected to canvas_manager
           - Stored in: overlay_managers[drawing_area].right_panel_loader
        
        7. **SwissKnife Palette** (line 1325: _setup_edit_palettes)
           - Tool selection (Place, Transition, Arc, Select)
           - Mode switching (Edit/Simulation)
           - Zoom controls, grid toggle, alignment tools
           - Stored in: overlay_managers[drawing_area].swissknife_palette
        
        8. **Event Controllers** (line 922: _setup_event_controllers)
           - Mouse/touch input handling
           - Gesture recognizers (pan, zoom, rotate)
           - Drawing callbacks (on_draw)
        
        9. **Lifecycle Integration** (line 1495: _setup_edit_palettes)
           - Canvas registration with lifecycle_manager
           - Coordinated component cleanup on tab close
           - Optional: canvas-scoped ID generation via IDScopeManager
        
        CONSISTENCY GUARANTEE:
        - ALL five canvas creation scenarios execute this EXACT code path
        - IDENTICAL initialization order prevents state inconsistencies
        - NO shortcuts, NO variations between startup/File→New/imports
        - Tab close properly cleans up ALL per-document state
        
        VERIFICATION POINTS:
        - manager.create_new_document() called (line 906)
        - _setup_canvas_manager() wires all controllers
        - _setup_edit_palettes() creates ALL per-document panels
        - SimulationController stored in self.simulation_controllers
        - Viability/Report panels stored in overlay_managers
        - Knowledge base stored in self.knowledge_bases
        
        See lines 820-1640 for complete initialization sequence.
        ═══════════════════════════════════════════════════════════════════
        """
        if self.notebook is None:
            raise RuntimeError('Canvas not loaded. Call load() first.')
        
        # Auto-replacement feature has been disabled
        # Users must manually close the default tab if they don't want it
        
        # Create new tab FROM UI TEMPLATE
        # This ensures identical widget hierarchy for all canvases (default, File→New, imports)
        # and eliminates Wayland timing issues by using consistent UI-based instantiation
        self.document_count += 1
        if filename is None:
            if title:
                filename = title
            else:
                filename = f"default{(self.document_count if self.document_count > 1 else '')}"
        
        # Load canvas tab from UI template
        template_path = os.path.join(os.path.dirname(self.ui_path), 'canvas_tab_template.ui')
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Canvas tab template not found: {template_path}")
        
        # Create a new builder instance for this canvas (each canvas gets its own widgets)
        tab_builder = Gtk.Builder.new_from_file(template_path)
        overlay = tab_builder.get_object('canvas_overlay_template')
        scrolled = tab_builder.get_object('canvas_scroll_template')
        drawing = tab_builder.get_object('canvas_drawing_template')
        drawing._shypn_doc_id = alloc_doc_id()  # stable monotonic ID, immune to address reuse
        overlay_box = tab_builder.get_object('canvas_overlay_box_template')
        
        if not all([overlay, scrolled, drawing, overlay_box]):
            raise ValueError("Failed to load canvas widgets from template")
        
        # Create tab label with file icon
        tab_filename = filename if filename else 'default'
        tab_box, tab_label, close_button = self._create_tab_label(tab_filename, False)
        close_button.connect('clicked', self._on_tab_close_clicked, overlay)
        tab_box.show_all()
        
        page_index = self.notebook.append_page(overlay, tab_box)
        overlay.show_all()
        
        # Do not force explicit realize here; GTK will realize widgets when packed
        # and shown by the toplevel window. Forcing realize early can break event
        # mask setup and cause GTK criticals about anchoring.
        
        # PHASE 4: Set ID scope EARLY for this new canvas
        # Ensure that any ID generation (including during initial setup or file load)
        # uses the per-canvas scope instead of the default 'global' scope.
        try:
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                scope_name = f"canvas_{id(drawing)}"
                self.lifecycle_manager.id_manager.set_scope(scope_name)
        except (AttributeError, TypeError, RuntimeError) as e:
            self.logger.debug(f"Failed to set lifecycle ID scope early for new canvas: {e}")
        
        # Setup canvas manager BEFORE switching tabs
        # This ensures the canvas is fully initialized before receiving focus/events
        self._setup_canvas_manager(drawing, overlay_box, overlay, filename=filename)
        
        # CRITICAL: Reset simulation to initial state after creating new document
        # Ensures clean slate with no stale cached behaviors
        self._ensure_simulation_reset(drawing)
        
        # ═══════════════════════════════════════════════════════════════════
        # CRITICAL: Wire context menu handler for first page (page 0)
        # ═══════════════════════════════════════════════════════════════════
        # The page-added hook fires TOO EARLY (before _setup_canvas_manager),
        # so the manager doesn't exist yet in canvas_managers dictionary.
        # Instead, we do the wiring HERE, after the manager is fully set up.
        # 
        # This ensures the first page gets the same context menu handler wiring
        # as tab-switched pages (which get wired via _on_notebook_page_changed).
        # ═══════════════════════════════════════════════════════════════════
        if page_index == 0 and not getattr(self, '_first_page_initialized', False):
            if self.right_panel_loader and drawing in self.canvas_managers:
                manager = self.canvas_managers[drawing]
                
                # Set model on right panel loader
                self.right_panel_loader.set_model(manager)
                
                # Set model on context menu handler to enable locality detection
                if self.right_panel_loader.context_menu_handler:
                    self.right_panel_loader.context_menu_handler.set_model(manager)
                
                # Set context menu handler on model_canvas_loader
                if self.right_panel_loader.context_menu_handler:
                    self.set_context_menu_handler(self.right_panel_loader.context_menu_handler)
                
                # CRITICAL FIX: Wire data_collector for the first page (default canvas)
                # This ensures plotting works on the default canvas without requiring a tab switch
                self._wire_data_collector_for_page(overlay)
            
            # Mark that we've initialized the first page
            self._first_page_initialized = True
        
        # Switch to the newly created tab to give it focus (AFTER setup is complete)
        self.notebook.set_current_page(page_index)
        
        return (page_index, drawing)

    def _setup_canvas_manager(self, drawing_area, overlay_box=None, overlay_widget=None, filename=None):
        """Setup canvas manager and wire up callbacks for a drawing area.
        
        Args:
            drawing_area: GtkDrawingArea widget to setup.
            overlay_box: Optional GtkBox for overlay widgets (zoom control).
            overlay_widget: Optional GtkOverlay for adding overlays directly.
            filename: Base filename without extension (default: "default").
        """
        if filename is None:
            filename = 'default'
        # Ensure ID scope is set for this drawing_area before manager initialization
        try:
            if self.lifecycle_manager and hasattr(self.lifecycle_manager, 'id_manager'):
                scope_name = f"canvas_{id(drawing_area)}"
                self.lifecycle_manager.id_manager.set_scope(scope_name)
        except (AttributeError, TypeError, RuntimeError) as e:
            self.logger.debug(f"Failed to set lifecycle ID scope before manager init: {e}")
        manager = ModelCanvasManager(canvas_width=2000, canvas_height=2000, filename=filename)

        # Per-document UndoManager initialization (lifecycle-integrated)
        try:
            from shypn.edit.undo_manager import UndoManager
            if not hasattr(manager, 'undo_manager'):
                manager.undo_manager = UndoManager()
        except (ImportError, AttributeError) as e:
            self.logger.debug(f"Failed to initialize UndoManager for canvas: {e}")

        # ── Sprint 18: register DocumentSession BEFORE any proxy writes ──────
        # overlay_manager and simulation_controller are None here; they are
        # assigned below via proxy writes (setting the slot on this same session
        # object), so all code that follows sees a consistent single session.
        _early_session = DocumentSession(
            drawing_area=drawing_area,
            canvas_manager=manager,
        )
        self.sessions.register(drawing_area, _early_session)
        # ----------------------------------------------------------------

        self.canvas_managers[drawing_area] = manager  # proxy: session.canvas_manager = manager (idempotent)
        
        # Store references back to loader and drawing area for simulation reset
        manager._canvas_loader = self
        manager._drawing_area = drawing_area
        
        # Set redraw callback so manager can trigger widget redraws
        manager.set_redraw_callback(lambda: drawing_area.queue_draw())
        
        # WAYLAND FIX: Set flag to suppress callbacks during initial setup
        # Prevents premature signal firing before canvas state is fully initialized
        manager._suppress_callbacks = True
        
        # PHASE 1: Wire dirty state callback to update tab label with asterisk
        # This enables automatic tab label updates when document is modified
        def on_dirty_changed(is_dirty):
            """Callback when manager's dirty state changes.
            
            Updates the tab label to show/hide asterisk indicator.
            """
            # Skip callback if we're still setting up the canvas
            if getattr(manager, '_suppress_callbacks', False):
                return
            
            try:
                pass
                # Find the page widget for this drawing area
                # Navigation: drawing_area -> GtkScrolledWindow -> GtkOverlay (page widget)
                parent = drawing_area.get_parent()  # Should be GtkScrolledWindow
                if not parent:
                    pass
                    # Widget hierarchy not yet established - this is normal during initial setup
                    # Callback will be triggered again later when changes occur
                    return
                
                page_widget = parent.get_parent()  # Should be GtkOverlay
                if not page_widget:
                    pass
                    # Still setting up widget hierarchy
                    return
                    
                # Verify page_widget is actually in the notebook
                page_num = self.notebook.page_num(page_widget)
                if page_num < 0:
                    pass
                    # Not yet added to notebook
                    return
                
                # Get display name from manager (filename without path)
                display_name = manager.get_display_name()
                # Update tab label using existing method
                self._update_tab_label(page_widget, display_name, is_modified=is_dirty)
            except Exception as e:
                self.logger.debug(f"Tab label update during widget setup failed: {e}")
                pass
                # Silently ignore errors during widget setup
                # (e.g., if called before widget hierarchy is complete)
                pass
        
        manager.on_dirty_changed = on_dirty_changed
        
        try:
            screen = drawing_area.get_screen()
            if screen:
                dpi = screen.get_resolution()
                if dpi and dpi > 0:
                    manager.set_screen_dpi(dpi)
        except Exception as e:
            self.logger.debug(f"Screen DPI detection failed: {e}")
            pass
        
        # Only load view state for non-temporary filenames
        # Temporary names like "importing_temp" are used during imports
        # to prevent loading stale view states
        if filename != "importing_temp":
            manager.load_view_state_from_file()
        
        validation = manager.create_new_document(filename=filename)
        
        # Create Knowledge Base for intelligent model repair
        try:
            from shypn.viability.knowledge import ModelKnowledgeBase
            kb = ModelKnowledgeBase(model=None)  # Model will be set when available
            self.knowledge_bases[drawing_area] = kb
            # Make KB accessible from canvas manager
            manager.knowledge_base = kb
        except Exception as e:
            self.logger.debug(f"Could not create knowledge base for canvas: {e}")

        def on_draw_wrapper(widget, cr):
            allocation = widget.get_allocation()
            self._on_draw(widget, cr, allocation.width, allocation.height, manager)
            return False
        drawing_area.connect('draw', on_draw_wrapper)
        self._setup_event_controllers(drawing_area, manager)
        
        # Trigger initial redraw now that draw handler is connected
        # (create_new_document() called mark_needs_redraw() but handler wasn't connected yet)
        manager.mark_needs_redraw()
        
        # Setup overlay manager to handle all palettes
        if overlay_box and overlay_widget:
            overlay_manager = CanvasOverlayManager(
                overlay_widget=overlay_widget,
                overlay_box=overlay_box,
                drawing_area=drawing_area,
                canvas_manager=manager
            )
            # WAYLAND FIX: Use main_window instead of parent_window (which is never set)
            overlay_manager.setup_overlays(parent_window=getattr(self, 'main_window', None))
            
            # Store overlay manager for later access
            self.overlay_managers[drawing_area] = overlay_manager
            
            # Connect signals from palettes
            overlay_manager.connect_tool_changed_signal(
                self._on_tool_changed, manager, drawing_area
            )
            overlay_manager.connect_simulation_signals(
                self._on_simulation_step, self._on_simulation_reset, drawing_area
            )
            overlay_manager.connect_edit_button_signal(
                self._on_edit_button_toggled, drawing_area
            )
            
            # Set initial state: Edit mode is default
            # Old [E] and [S] buttons no longer exist - removed, replaced by SwissKnifePalette
            
            # Setup new OOP palette system
            self._setup_edit_palettes(overlay_widget, manager, drawing_area, overlay_manager)
            
            # Canvas setup complete - enable callbacks now that state is properly initialized
            manager._suppress_callbacks = False
        else:
            # CRITICAL FIX: Even without overlay_box, MUST enable callbacks
            # Otherwise canvas becomes non-interactive
            manager._suppress_callbacks = False

    def _reset_manager_for_load(self, manager, filename):
        """Reset manager state before loading objects from file.
        
        This prepares an existing manager to receive a loaded document,
        resetting all state flags and counters to clean slate.
        
        MUST be called BEFORE load_objects() when reusing a tab for File→Open or Import.
        
        This is the CANONICAL state reset for document loading, ensuring:
        - All state flags are reset
        - Callbacks are enabled
        - Objects are cleared
        - ID counters are reset
        - Canvas interaction states are reset (drag, arc, lasso, etc.)
        - Simulation controllers are reset to initial state
        - Swiss palettes are reset to default tool/mode
        
        Args:
            manager: ModelCanvasManager instance to reset
            filename: Base filename (without extension) for the document
        """
        from datetime import datetime
        
        # Reset document metadata
        manager.filename = filename
        manager.modified = False
        manager.created_at = datetime.now()
        manager.modified_at = None
        
        # Reset view state (will be overridden by saved view_state if exists)
        manager.zoom = 1.0
        manager.pan_x = 0.0
        manager.pan_y = 0.0
        # CRITICAL: Reset initial_pan_set flag in BOTH manager and viewport_controller
        manager._initial_pan_set = False
        manager.viewport_controller._initial_pan_set = False
        
        # CRITICAL: Ensure callbacks are enabled
        # This is the most common cause of "frozen canvas" bugs
        manager._suppress_callbacks = False
        
        # Clear any existing objects
        # (Should be empty when reusing default tab, but be paranoid)
        manager.places.clear()
        manager.transitions.clear()
        manager.arcs.clear()
        
        # Reset ID counters to avoid collisions
        manager.document_controller.id_manager.reset()
        
        # Mark as clean (document will be loaded)
        manager.mark_clean()
        
        # Clear selection
        if hasattr(manager, 'selection_manager'):
            manager.selection_manager.clear_selection()
        
        # Reset tool state
        manager.clear_tool()
        
        # Reset canvas interaction states (CRITICAL for fixing corrupted context menu/drag)
        # These states can get stuck if not properly reset between document loads
        # Find the drawing_area for this manager by looking through self.canvas_managers
        drawing_area = None
        if hasattr(self, 'canvas_managers'):
            for da, mgr in self.canvas_managers.items():
                if mgr == manager:
                    drawing_area = da
                    break
        
        if drawing_area:
            pass
            # Ensure event masks and focus are set (critical for interaction)
            drawing_area.set_events(
                Gdk.EventMask.BUTTON_PRESS_MASK | 
                Gdk.EventMask.BUTTON_RELEASE_MASK | 
                Gdk.EventMask.POINTER_MOTION_MASK | 
                Gdk.EventMask.SCROLL_MASK | 
                Gdk.EventMask.KEY_PRESS_MASK
            )
            drawing_area.set_can_focus(True)
            
            # Reset all canvas interaction state (prevents stuck modes)
            if hasattr(self, '_canvas_ctx') and drawing_area in self._canvas_ctx:
                ctx = self._canvas_ctx[drawing_area]
                ctx.reset_drag()
                ctx.reset_arc()
                # Cancel any pending click timeout
                if ctx.click.get('pending_timeout'):
                    GLib.source_remove(ctx.click['pending_timeout'])
                ctx.click.update({
                    'last_click_time': 0.0,
                    'last_click_obj': None,
                    'double_click_threshold': 0.3,
                    'pending_timeout': None,
                    'pending_click_data': None,
                })
                # Deactivate any active lasso
                if ctx.lasso.get('selector'):
                    ctx.lasso['selector'].cancel()
                ctx.lasso.update({'active': False, 'selector': None})
            
            # ============================================================
            # NOTE: Simulation controller reset moved to AFTER load_objects()
            # ============================================================
            # The simulation controller should be reset AFTER objects are loaded,
            # not here when the manager is still empty. The reset happens in
            # _ensure_simulation_reset() which is called after load_objects().
            # This ensures the controller sees the full loaded model.
            
            # ============================================================
            # CRITICAL: Reset Swiss Knife Palette to default state
            # ============================================================
            # The palette maintains tool selection, mode, and visual state.
            # When loading a new model, reset to default state (no active sub-palette).
            if drawing_area in self.overlay_managers:
                overlay_manager = self.overlay_managers[drawing_area]
                if hasattr(overlay_manager, 'swissknife_palette'):
                    palette = overlay_manager.swissknife_palette
                    # Hide any active sub-palette (returns to default state)
                    # Note: active_sub_palette only exists in old palette, not new refactored one
                    if hasattr(palette, 'active_sub_palette') and palette.active_sub_palette:
                        if hasattr(palette, '_hide_sub_palette') and hasattr(palette, 'active_category'):
                            palette._hide_sub_palette(palette.active_category)
                    # Update palette's model reference to the (reset) manager
                    palette.model = manager
                    # If palette has widget palette instances (like SimulateToolsPaletteLoader),
                    # update their model references too
                    if hasattr(palette, 'widget_palette_instances'):
                        for widget_palette in palette.widget_palette_instances.values():
                            if hasattr(widget_palette, 'model'):
                                widget_palette.model = manager
        
        # Trigger redraw to show canvas is ready for new content
        manager.mark_needs_redraw()
    
    def _ensure_simulation_reset(self, drawing_area):
        """Ensure simulation is reset to initial state for a canvas.
        
        CRITICAL for consistent behavior across all flows:
        This must be called after any operation that creates or modifies a model:
        - File → New
        - File → Open
        - Double-click file in explorer
        - KEGG import
        - SBML import
        - Parameter application (Heuristic/BRENDA/SABIO-RK)
        
        The reset ensures:
        - Behavior cache is cleared (old behaviors don't persist)
        - Places are set to initial marking (clean start)
        - Simulation time is reset to 0.0
        - Enablement states are recalculated
        
        See: CANVAS_STATE_ISSUES_COMPARISON.md for recurring pattern history
        
        Args:
            drawing_area: GtkDrawingArea for the canvas to reset
        """
        if not drawing_area:
            return
        
        try:
            if drawing_area in self.simulation_controllers:
                controller = self.simulation_controllers[drawing_area]
                manager = self.canvas_managers.get(drawing_area)
                if manager:
                    pass
                    # CRITICAL: Use reset_for_new_model() instead of reset()
                    # This recreates the model adapter and ensures the controller
                    # references the correct manager with the loaded objects
                    controller.reset_for_new_model(manager)
                    
                    # CRITICAL: Update SimulateToolsPaletteLoader's controller reference
                    # The palette has its own simulation controller reference that needs
                    # to be updated when we reset/recreate the controller for a loaded model
                    overlay_manager = self.overlay_managers.get(drawing_area)
                    if overlay_manager:
                        # CRITICAL: Update overlay_manager's controller reference
                        # This ensures arc property dialog can find the correct controller
                        overlay_manager.simulation_controller = controller
                        
                        pass
                        swissknife = getattr(overlay_manager, 'swissknife_palette', None)
                        if swissknife:
                            pass
                            # Use registry.get_widget_palette_instance() instead
                            if hasattr(swissknife, 'registry'):
                                pass
                                simulate_tools_palette = swissknife.registry.get_widget_palette_instance('simulate')
                                if simulate_tools_palette:
                                    pass
                                    
                                    # CRITICAL: Preserve step listeners from old controller
                                    # When we replace the controller reference, we need to re-register
                                    # the step listeners on the new controller, otherwise the UI won't update!
                                    old_controller = simulate_tools_palette.simulation
                                    if old_controller and hasattr(old_controller, 'step_listeners'):
                                        pass
                                    
                                    simulate_tools_palette.simulation = controller
                                    
                                    # Re-register step listeners on new controller
                                    # The palette's _on_simulation_step callback updates progress and triggers redraws
                                    if hasattr(simulate_tools_palette, '_on_simulation_step'):
                                        controller.add_step_listener(simulate_tools_palette._on_simulation_step)
                                    if hasattr(simulate_tools_palette, 'data_collector'):
                                        controller.add_step_listener(simulate_tools_palette.data_collector.on_simulation_step)
                                    
                                    # PHASE 1-2 FIX: Do NOT overwrite controller.data_collector
                                    # The controller has its own DataCollector (for Report Panel)
                                    # The simulate_tools_palette has its own (for real-time plots)
                                    # Both should coexist
                                    # DO NOT OVERWRITE: controller.data_collector = simulate_tools_palette.data_collector
                                    
                                    # CRITICAL: Re-apply UI defaults to new controller
                                    # This ensures progress bar works globally after controller reset
                                    # (for File → Open, File → Reset, KEGG/SBML imports, parameter changes)
                                    simulate_tools_palette._apply_ui_defaults_to_settings()
                                    
                                    # Re-wire report panel after controller reset via EventBus (document-scoped)
                                    EventBus.emit('simulation.controller_ready',
                                                  {'controller': controller},
                                                  document_id=doc_id(drawing_area))
                                    
                                    # VIABILITY PANEL: Wire simulation complete callback after reset
                                    # After controller reset, re-establish the callback chain for PER-DOCUMENT panel
                                    if drawing_area in self.overlay_managers:
                                        overlay_manager = self.overlay_managers[drawing_area]
                                        if hasattr(overlay_manager, 'viability_panel_loader') and overlay_manager.viability_panel_loader:
                                            try:
                                                viability_panel = overlay_manager.viability_panel_loader.panel
                                                if viability_panel and hasattr(viability_panel, 'on_simulation_complete'):
                                                    existing_callback = getattr(controller, 'on_simulation_complete', None)
                                                    
                                                    def combined_callback():
                                                        if existing_callback and callable(existing_callback):
                                                            existing_callback()
                                                        viability_panel.on_simulation_complete()
                                                    
                                                    controller.on_simulation_complete = combined_callback
                                            except Exception as e:
                                                self.logger.debug(f"Could not set viability panel simulation callback: {e}")
                                else:
                                    pass
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                else:
                    pass
                    # Fallback to basic reset if we can't get the manager
                    controller.reset()
                if manager:
                    pass
                    
                    # CRITICAL LIFECYCLE FIX: Verify all transitions are registered
                    # After import/load, controller.transition_states should have entries for ALL transitions
                    # If missing, simulation won't run until user interaction triggers re-registration
                    missing_count = 0
                    for transition in manager.transitions:
                        if transition.id not in controller.transition_states:
                            missing_count += 1
                            # Force create state for this transition
                            state = controller._get_or_create_state(transition)
                            # Initialize enablement state for this transition
                            behavior = controller._get_behavior(transition)
                            is_source = getattr(transition, 'is_source', False)
                            if is_source:
                                pass
                                # Source transitions are always enabled
                                state.enablement_time = controller.time
                                if hasattr(behavior, 'set_enablement_time'):
                                    behavior.set_enablement_time(controller.time)
                    
                    if missing_count > 0:
                        pass
                    else:
                        pass
                    
                    # CRITICAL LIFECYCLE FIX #2: Invalidate model adapter caches
                    # After load, the model adapter may have stale arc/place/transition caches
                    # Drawing an arc triggers cache invalidation which "wakes up" the simulation
                    # We must explicitly invalidate here to ensure proper simulation state
                    if hasattr(controller, 'model_adapter') and controller.model_adapter:
                        controller.model_adapter.invalidate_caches()
        except Exception as e:
            self.logger.error(f"Failed to invalidate model adapter caches: {e}")
            import traceback
            traceback.print_exc()
        

    def _setup_edit_palettes(self, overlay_widget, canvas_manager, drawing_area, overlay_manager):
        """Setup OOP palette system and all per-document panels for one canvas.

        Delegates all 8 per-document creation steps to
        :class:`~shypn.helpers.document_panel_setup.DocumentPanelSetup`.

        Sprint 18 note: the :class:`~shypn.helpers.document_session.DocumentSession`
        for this drawing_area was already registered early in
        :meth:`_setup_canvas_manager`.  ``DocumentPanelSetup.build()`` fills
        in the ``simulation_controller`` field via the ``simulation_controllers``
        proxy.  No second registration is needed here.

        Args:
            overlay_widget: GtkOverlay to attach palettes to.
            canvas_manager: ModelCanvasManager instance for this canvas.
            drawing_area: GtkDrawingArea widget.
            overlay_manager: CanvasOverlayManager instance.
        """
        DocumentPanelSetup(self, drawing_area, canvas_manager, overlay_manager).build(overlay_widget)


    def _on_palette_tool_selected(self, tools_palette, tool_name, canvas_manager, drawing_area):
        """Handle tool selection from new OOP tools palette.
        
        Args:
            tools_palette: ToolsPalette instance.
            tool_name: Name of selected tool ('place', 'transition', 'arc', 'select').
            canvas_manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if tool_name == 'select':
            canvas_manager.clear_tool()
        else:
            canvas_manager.set_tool(tool_name)
        drawing_area.queue_draw()
    
    def _on_palette_operation_triggered(self, operations_palette, operation, canvas_manager, drawing_area):
        """Handle operation trigger from new OOP operations palette.
        
        Args:
            operations_palette: OperationsPalette instance.
            operation: Operation name ('select', 'lasso', 'undo', 'redo').
            canvas_manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if operation == 'select':
            canvas_manager.clear_tool()
            drawing_area.queue_draw()
        elif operation == 'lasso':
            pass
            # Import LassoSelector
            from shypn.edit.lasso_selector import LassoSelector
            
            # Get or create lasso state via canvas context
            if drawing_area not in self._canvas_ctx:
                self._canvas_ctx[drawing_area] = CanvasInteractionContext()
            lasso_state = self._canvas_ctx[drawing_area].lasso
            
            # Create LassoSelector instance if needed
            if lasso_state['selector'] is None:
                lasso_state['selector'] = LassoSelector(canvas_manager)
            
            # Activate lasso mode
            lasso_state['active'] = True
            canvas_manager.clear_tool()  # Deactivate other tools
            
            drawing_area.queue_draw()
        elif operation == 'undo':
            if hasattr(canvas_manager, 'undo_manager') and canvas_manager.undo_manager:
                if canvas_manager.undo_manager.undo(canvas_manager):
                    drawing_area.queue_draw()
        elif operation == 'redo':
            if hasattr(canvas_manager, 'undo_manager') and canvas_manager.undo_manager:
                if canvas_manager.undo_manager.redo(canvas_manager):
                    drawing_area.queue_draw()

    # ============================================================
    # SWISSKNIFE PALETTE SIGNAL HANDLERS - Unified handlers
    # ============================================================
    
    def _on_swissknife_tool_activated(self, palette, tool_id, canvas_manager, drawing_area):
        """Handle tool activation from SwissKnifePalette.
        
        Unified handler for all tool types from SwissKnifePalette:
        - Drawing tools: place, transition, arc
        - Selection tools: select, lasso
        - Layout tools: layout_auto, layout_hierarchical, layout_force
        
        This replaces the old _on_palette_tool_selected and _on_palette_operation_triggered handlers.
        
        Args:
            palette: SwissKnifePalette instance
            tool_id: Tool identifier string
            canvas_manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Update tool visual feedback
        if hasattr(palette, 'tool_registry'):
            palette.tool_registry.set_active_tool(tool_id)
        
        # Set cursor based on tool
        window = drawing_area.get_window()
        if window:
            display = drawing_area.get_display()
            cursor = None
            
            if tool_id == 'place':
                cursor = Gdk.Cursor.new_from_name(display, 'crosshair')
            elif tool_id == 'transition':
                cursor = Gdk.Cursor.new_from_name(display, 'crosshair')
            elif tool_id == 'arc':
                cursor = Gdk.Cursor.new_from_name(display, 'cell')
            elif tool_id == 'select':
                cursor = Gdk.Cursor.new_from_name(display, 'default')
            elif tool_id == 'lasso':
                cursor = Gdk.Cursor.new_from_name(display, 'hand1')
            elif tool_id.startswith('layout_'):
                cursor = Gdk.Cursor.new_from_name(display, 'default')
            
            window.set_cursor(cursor)
        
        # Drawing tools (place, transition, arc)
        if tool_id in ('place', 'transition', 'arc'):
            # Check permission before activating structural tools
            # This uses canvas-centric access pattern that survives SwissPalette refactoring
            controller = self.get_canvas_controller(drawing_area)
            if controller:
                allowed, reason = controller.interaction_guard.check_tool_activation(tool_id)
                if not allowed:
                    self._show_info_message(reason)
                    return  # Don't activate the tool
            
            canvas_manager.set_tool(tool_id)
            drawing_area.queue_draw()
        
        # Selection tools
        elif tool_id == 'select':
            canvas_manager.clear_tool()
            drawing_area.queue_draw()
        
        elif tool_id == 'lasso':
            pass
            # Lasso selection logic (copied from old _on_palette_operation_triggered)
            from shypn.edit.lasso_selector import LassoSelector
            
            # Get or create lasso state via canvas context
            if drawing_area not in self._canvas_ctx:
                self._canvas_ctx[drawing_area] = CanvasInteractionContext()
            lasso_state = self._canvas_ctx[drawing_area].lasso
            
            # Create LassoSelector instance if needed
            if lasso_state['selector'] is None:
                lasso_state['selector'] = LassoSelector(canvas_manager)
            
            # Activate lasso mode
            lasso_state['active'] = True
            canvas_manager.clear_tool()  # Deactivate other tools
            
            drawing_area.queue_draw()
        
        # Layout tools - call existing layout methods
        elif tool_id == 'layout_auto':
            self._on_layout_auto_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_hierarchical':
            self._on_layout_hierarchical_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_force':
            self._on_layout_force_clicked(None, drawing_area, canvas_manager)
        
        elif tool_id == 'layout_settings':
            pass
            # Toggle layout parameter panel
            palette.parameter_manager.toggle_panel('layout')
    
    def _on_swissknife_mode_change_requested(self, palette, requested_mode, canvas_manager, drawing_area):
        """Handle mode change request from SwissKnifePalette.
        
        Called when user clicks category buttons that trigger mode changes.
        Currently, Edit/Simulate/Layout are all in 'edit' mode, so this may not
        trigger until modes are separated in future.
        
        Args:
            palette: SwissKnifePalette instance
            requested_mode: 'edit' or 'simulate'
            canvas_manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # TODO: Implement mode switching logic when needed
        # current_mode = self._get_current_mode(drawing_area)
        # if requested_mode != current_mode:
        #     self._switch_canvas_mode(drawing_area, requested_mode)
        pass
    
    def _on_swissknife_float_toggled(self, palette, is_floating, widget, drawing_area):
        """Handle float/attach toggle from SwissKnifePalette.
        
        Repositions the palette between floating (center/variable) and 
        attached (bottom/center) states.
        
        Args:
            palette: SwissKnifePalette instance
            is_floating: True if now floating, False if attached
            widget: The palette widget to reposition
            drawing_area: GtkDrawingArea for canvas reference (unused now)
        """
        if is_floating:
            pass
            # Floating mode: use START alignment for absolute positioning via margins
            # Combined with hexpand/vexpand=False to maintain natural size
            widget.set_halign(Gtk.Align.START)
            widget.set_valign(Gtk.Align.START)
            widget.set_hexpand(False)
            widget.set_vexpand(False)
            
            # DON'T set size_request - let widget maintain its natural size
            # This allows sub-palettes and parameter panels to expand/collapse naturally
            
            # Keep current position (margins stay as they are)
        else:
            pass
            # Attached mode: move to bottom center
            widget.set_halign(Gtk.Align.CENTER)
            widget.set_valign(Gtk.Align.END)
            widget.set_hexpand(False)
            widget.set_vexpand(False)
            
            # Clear size request to allow natural sizing in attached mode
            widget.set_size_request(-1, -1)
            
            # Get overlay widget (viewport container) - this is the actual visible area
            # Navigation: widget (palette) -> overlay (viewport container)
            overlay_widget = widget.get_parent()
            if overlay_widget:
                pass
                # Ensure margin keeps palette visible in viewport
                viewport_height = overlay_widget.get_allocated_height()
                palette_height = widget.get_allocated_height()
                
                # Calculate safe margin (keep at least 10px from bottom)
                min_margin = 20
                max_margin = max(min_margin, viewport_height - palette_height - 10)
                margin = min(min_margin, max_margin)
                
                widget.set_margin_bottom(margin)
            else:
                pass
                # Fallback if parent not available
                widget.set_margin_bottom(20)
            
            widget.set_margin_top(0)
            widget.set_margin_start(0)
            widget.set_margin_end(0)
    
    def _on_swissknife_position_changed(self, palette, dx, dy, widget, drawing_area):
        """Handle position change from SwissKnifePalette drag.
        
        Updates the widget margins to move it by the delta amounts.
        Uses viewport-aware bounds to keep palette mostly visible.
        
        Args:
            palette: SwissKnifePalette instance
            dx: Horizontal delta from drag (screen space)
            dy: Vertical delta from drag (screen space)
            widget: The palette widget to reposition
            drawing_area: GtkDrawingArea for canvas reference (unused now)
        """
        # Get overlay widget (viewport container) - this is the actual visible area
        # Navigation: widget (palette) -> overlay (viewport container)
        overlay_widget = widget.get_parent()
        if not overlay_widget:
            return
        
        # Get viewport dimensions from overlay (actual window size)
        viewport_width = overlay_widget.get_allocated_width()
        viewport_height = overlay_widget.get_allocated_height()
        
        # Get palette dimensions
        palette_width = widget.get_allocated_width()
        palette_height = widget.get_allocated_height()
        
        # Get current margins
        current_left = widget.get_margin_start()
        current_top = widget.get_margin_top()
        
        # Apply delta with viewport-aware bounds
        # Keep at least min_visible pixels of palette on screen
        min_visible = 50  # Minimum pixels that must stay visible
        
        # Calculate bounds
        # Left bound: palette can go left until only min_visible pixels show
        min_left = -palette_width + min_visible
        # Right bound: palette can go right until only min_visible pixels show
        max_left = viewport_width - min_visible
        # Top bound: palette can go up until only min_visible pixels show
        min_top = -palette_height + min_visible
        # Bottom bound: palette can go down until only min_visible pixels show
        max_top = viewport_height - min_visible
        
        # Apply delta and clamp to bounds
        new_left = max(min_left, min(max_left, int(current_left + dx)))
        new_top = max(min_top, min(max_top, int(current_top + dy)))
        
        widget.set_margin_start(new_left)
        widget.set_margin_top(new_top)

    def _on_simulation_step(self, palette, time, drawing_area):
        """Handle simulation step - redraw canvas to show updated token state.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            time: Current simulation time
            drawing_area: GtkDrawingArea widget to redraw
        """
        drawing_area.queue_draw()

    def _on_simulation_reset(self, palette, drawing_area):
        """Handle simulation reset - blank analysis plots immediately.
        
        IMPORTANT: Force immediate canvas blanking by calling update_plot() directly
        instead of setting needs_update=True. This ensures plots are cleared synchronously
        with the reset action, providing immediate visual feedback to the user.
        
        Args:
            palette: SwissKnifePalette that forwarded the signal
            drawing_area: GtkDrawingArea widget for the canvas
        """
        if self.right_panel_loader:
            pass
            # Place panel - force immediate update
            if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                panel = self.right_panel_loader.place_panel
                panel.last_data_length.clear()
                # Force immediate canvas blank/update - don't wait for periodic check
                if panel.selected_objects:
                    panel.update_plot()  # Will show empty plot with 0 data
                else:
                    panel._show_empty_state()
            
            # Transition panel - force immediate update
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                panel = self.right_panel_loader.transition_panel
                panel.last_data_length.clear()
                # Force immediate canvas blank/update - don't wait for periodic check
                if panel.selected_objects:
                    panel.update_plot()  # Will show empty plot with 0 data
                else:
                    panel._show_empty_state()
            
            # PHASE 1-2 FIX: Reset Dynamic Analyses Panel plots
            # This clears all real-time plots (transitions, places, diagnostics)
            if hasattr(self.right_panel_loader, 'dynamic_analyses_panel') and self.right_panel_loader.dynamic_analyses_panel:
                try:
                    self.right_panel_loader.dynamic_analyses_panel.reset()
                except Exception as e:
                    print(f"Warning: Could not reset dynamic analyses panel: {e}")
        
        # Also check overlay-based dynamic analyses panel (per-document)
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            if hasattr(overlay_manager, 'analyses_panel_loader') and overlay_manager.analyses_panel_loader:
                try:
                    overlay_manager.analyses_panel_loader.panel.reset()
                except Exception as e:
                    self.logger.debug(f"Could not reset analyses panel for canvas: {e}")

    def _on_simulation_settings_changed(self, palette, drawing_area):
        """Handle simulation settings change.
        
        Args:
            palette: SimulateToolsPaletteLoader that emitted the signal
            drawing_area: GtkDrawingArea widget
        """
        # Settings changed - update all per-document components
        
        # Get simulation settings from palette
        simulation_settings = None
        if hasattr(palette, 'simulation') and palette.simulation:
            simulation_settings = palette.simulation.settings
        
        # Forward to analyses panel (updates plot x-axis for duration changes)
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            
            # Update Dynamic Analyses Panel
            if hasattr(overlay_manager, 'analyses_panel_loader'):
                analyses_loader = overlay_manager.analyses_panel_loader
                if analyses_loader and hasattr(analyses_loader, 'panel') and analyses_loader.panel:
                    if hasattr(analyses_loader.panel, 'on_settings_changed'):
                        analyses_loader.panel.on_settings_changed(simulation_settings)
            
            # Update Report Panel (may need to refresh displays)
            if hasattr(overlay_manager, 'report_panel_loader'):
                report_loader = overlay_manager.report_panel_loader
                if report_loader and hasattr(report_loader, 'panel') and report_loader.panel:
                    if hasattr(report_loader.panel, 'refresh'):
                        report_loader.panel.refresh()
        
        # Redraw canvas
        drawing_area.queue_draw()

    def _on_edit_button_toggled(self, edit_palette, show, drawing_area):
        """Handle [E] button toggle for showing/hiding NEW OOP edit palettes.
        
        Args:
            edit_palette: EditPaletteLoader that emitted the signal
            show: True to show palettes, False to hide
            drawing_area: GtkDrawingArea widget
        """
        if drawing_area in self.palette_managers:
            palette_manager = self.palette_managers[drawing_area]
            if show:
                palette_manager.show_all()
            else:
                palette_manager.hide_all()

    def _on_tool_changed(self, tools_palette, tool_name, manager, drawing_area):
        """Handle tool selection change from edit tools palette.
        
        Args:
            tools_palette: EditToolsLoader instance that emitted the signal.
            tool_name: Name of the selected tool ('place', 'transition', 'arc') or empty string for none.
            manager: ModelCanvasManager instance.
            drawing_area: GtkDrawingArea widget.
        """
        if tool_name:
            # Check permission before activating tools
            # Canvas-centric access ensures this survives SwissPalette refactoring
            controller = self.get_canvas_controller(drawing_area)
            if controller:
                allowed, reason = controller.interaction_guard.check_tool_activation(tool_name)
                if not allowed:
                    self._show_info_message(reason)
                    tools_palette.clear_selection()  # Deselect the tool button
                    return
            
            manager.set_tool(tool_name)
        else:
            manager.clear_tool()

    @property
    def _canvas_ctx(self):
        """Proxy to input handler's per-canvas interaction context registry."""
        return self._input_handler.canvas_ctx

    def _get_canvas_page_num(self, widget):
        """Return the notebook page index for *widget* (Ctrl+W handler)."""
        try:
            if widget and widget.get_parent():
                return self.notebook.page_num(widget.get_parent().get_parent())
            return self.notebook.get_current_page() if self.notebook else -1
        except Exception:
            return self.notebook.get_current_page() if self.notebook else -1

    def _popdown_canvas_context_menu(self):
        """Dismiss active canvas context menu — delegates to CanvasContextMenuController (Sprint 22)."""
        return self._ctx_menu_ctrl.popdown_canvas_menu()

    def _setup_event_controllers(self, drawing_area, manager):
        """Setup mouse and keyboard event controllers.
        
        Args:
            drawing_area: GtkDrawingArea widget.
            manager: ModelCanvasManager instance.
        """
        # Ensure required event masks using add_events (safe after realize)
        required_mask = (
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.SCROLL_MASK
            | Gdk.EventMask.KEY_PRESS_MASK
        )
        try:
            if hasattr(drawing_area, 'add_events'):
                drawing_area.add_events(required_mask)
        except (TypeError, AttributeError) as e:
            self.logger.debug(f"Failed to add GTK event masks to drawing area: {e}")
        drawing_area.set_can_focus(True)
        drawing_area.connect('button-press-event', self._input_handler.on_button_press, manager)
        drawing_area.connect('button-release-event', self._input_handler.on_button_release, manager)
        drawing_area.connect('motion-notify-event', self._input_handler.on_motion_notify, manager)
        drawing_area.connect('scroll-event', self._input_handler.on_scroll_event, manager)
        drawing_area.connect('key-press-event', self._input_handler.on_key_press_event, manager)
        self._input_handler.register_drawing_area(drawing_area)
        self._setup_canvas_context_menu(drawing_area, manager)

        # Also attach handlers to GtkViewport (wrapper inside scrolled window),
        # some environments deliver events at the viewport level first.
        try:
            scrolled = drawing_area.get_parent()
            if scrolled and hasattr(scrolled, 'get_child'):
                viewport = scrolled.get_child()
            else:
                viewport = None
            # Attach to GtkScrolledWindow as well (some backends deliver here)
            if scrolled and hasattr(scrolled, 'connect'):
                required_mask = (
                    Gdk.EventMask.BUTTON_PRESS_MASK
                    | Gdk.EventMask.BUTTON_RELEASE_MASK
                    | Gdk.EventMask.POINTER_MOTION_MASK
                    | Gdk.EventMask.SCROLL_MASK
                    | Gdk.EventMask.KEY_PRESS_MASK
                )
                try:
                    if hasattr(scrolled, 'add_events'):
                        scrolled.add_events(required_mask)
                except (TypeError, AttributeError) as e:
                    self.logger.debug(f"Failed to add GTK event masks to scrolled window: {e}")
                scrolled.connect('button-press-event', lambda w, e, m=manager: self._input_handler.on_button_press(drawing_area, e, m))
                scrolled.connect('button-release-event', lambda w, e, m=manager: self._input_handler.on_button_release(drawing_area, e, m))
                scrolled.connect('motion-notify-event', lambda w, e, m=manager: self._input_handler.on_motion_notify(drawing_area, e, m))
                scrolled.connect('scroll-event', lambda w, e, m=manager: self._input_handler.on_scroll_event(drawing_area, e, m))
                scrolled.connect('key-press-event', lambda w, e, m=manager: self._input_handler.on_key_press_event(drawing_area, e, m))
            if viewport and hasattr(viewport, 'connect'):
                # Preserve masks on viewport and add required ones
                required_mask = (
                    Gdk.EventMask.BUTTON_PRESS_MASK
                    | Gdk.EventMask.BUTTON_RELEASE_MASK
                    | Gdk.EventMask.POINTER_MOTION_MASK
                    | Gdk.EventMask.SCROLL_MASK
                    | Gdk.EventMask.KEY_PRESS_MASK
                )
                try:
                    if hasattr(viewport, 'add_events'):
                        viewport.add_events(required_mask)
                except (TypeError, AttributeError) as e:
                    self.logger.debug(f"Failed to add GTK event masks to viewport: {e}")

                # Wrapper lambdas forward events to the drawing_area handlers
                viewport.connect('button-press-event', lambda w, e, m=manager: self._input_handler.on_button_press(drawing_area, e, m))
                viewport.connect('button-release-event', lambda w, e, m=manager: self._input_handler.on_button_release(drawing_area, e, m))
                viewport.connect('motion-notify-event', lambda w, e, m=manager: self._input_handler.on_motion_notify(drawing_area, e, m))
                viewport.connect('scroll-event', lambda w, e, m=manager: self._input_handler.on_scroll_event(drawing_area, e, m))
                viewport.connect('key-press-event', lambda w, e, m=manager: self._input_handler.on_key_press_event(drawing_area, e, m))
        except (TypeError, AttributeError) as e:
            self.logger.debug(f"Failed to wire GTK events for canvas widgets: {e}")

    def _on_draw(self, drawing_area, cr, width, height, manager):
        """Draw callback — delegates to CanvasRenderer (Sprint 21)."""
        self._renderer.render_frame(drawing_area, cr, width, height, manager)

    def _draw_arc_preview(self, cr, arc_state, manager):
        """Arc-preview draw — delegates to CanvasRenderer (Sprint 21)."""
        self._renderer.render_arc_preview(cr, arc_state, manager)

    def _show_canvas_context_menu(self, x, y, drawing_area):
        """Pop up canvas context menu — delegates to CanvasContextMenuController (Sprint 22)."""
        self._ctx_menu_ctrl.show_canvas_menu(x, y, drawing_area)

    def _show_object_context_menu(self, x, y, drawing_area, manager, obj):
        """Pop up per-object context menu — delegates to CanvasContextMenuController (Sprint 22)."""
        self._ctx_menu_ctrl.show_object_menu(x, y, drawing_area, manager, obj)

    # Context-menu item builders — Sprint 22: delegates to CanvasContextMenuController

    def _add_place_context_items(self, obj, menu_items: list, manager, drawing_area) -> None:
        """Append Place-specific context-menu items. Sprint 22: delegates."""
        self._ctx_menu_ctrl._add_place_context_items(obj, menu_items, manager, drawing_area)

    def _add_transition_context_items(self, obj, menu_items: list, manager, drawing_area) -> None:
        """Append Transition-specific context-menu items. Sprint 22: delegates."""
        self._ctx_menu_ctrl._add_transition_context_items(obj, menu_items, manager, drawing_area)

    def _add_arc_context_items(self, obj, menu_items: list, manager, drawing_area) -> None:
        """Append Arc-specific context-menu items. Sprint 22: delegates."""
        self._ctx_menu_ctrl._add_arc_context_items(obj, menu_items, manager, drawing_area)

    def get_canvas_manager(self, drawing_area=None):
        """Get the canvas manager for a drawing area.

        Args:
            drawing_area: GtkDrawingArea. If None, returns manager for current document.

        Returns:
            ModelCanvasManager: Canvas manager instance, or None if not found.
        """
        if drawing_area is None:
            drawing_area = self.get_current_document()
        return self.canvas_managers.get(drawing_area)

    def get_canvas_controller(self, drawing_area=None):
        """Get the simulation controller for a drawing area.
        
        Canvas-centric controller access.
        This method provides stable access to controllers that survives
        SwissPalette refactoring. Controllers are keyed by drawing_area,
        which is a stable reference that won't change during UI refactoring.
        
        Args:
            drawing_area: GtkDrawingArea. If None, returns controller for current document.
            
        Returns:
            SimulationController: Controller instance with state_detector, 
                                 buffered_settings, and interaction_guard.
                                 Returns None if not found.
        
        Usage:
            controller = self.get_canvas_controller(drawing_area)
            if controller and not controller.interaction_guard.can_activate_tool('place'):
                reason = controller.interaction_guard.get_block_reason('place')
                show_message(reason)
        """
        if drawing_area is None:
            drawing_area = self.get_current_document()
        return self.simulation_controllers.get(drawing_area)

    def get_current_document(self):
        """Get the currently active document's drawing area.
        
        Returns:
            GtkDrawingArea: The active drawing area, or None if no pages.
        """
        if self.notebook is None:
            return None
        page_index = self.notebook.get_current_page()
        if page_index == -1:
            return None
        page = self.notebook.get_nth_page(page_index)
        if isinstance(page, Gtk.Overlay):
            scrolled = page.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                child = scrolled.get_child()
                if hasattr(child, 'get_child'):
                    child = child.get_child()
                if isinstance(child, Gtk.DrawingArea):
                    return child
        elif isinstance(page, Gtk.ScrolledWindow):
            child = page.get_child()
            if hasattr(child, 'get_child'):
                child = child.get_child()
            if isinstance(child, Gtk.DrawingArea):
                return child
        return None

    def get_current_model(self):
        """Get the current canvas manager as model for topology analysis.
        
        The ModelCanvasManager IS the model - it has places, transitions, arcs
        attributes that satisfy the TopologyAnalyzer duck-typed interface.
        
        This method is used by the Topology Panel to get the model for analysis.
        
        Returns:
            ModelCanvasManager: The active canvas manager (which is the model),
                               or None if no document is open.
        
        Example:
            # From Topology Panel Controller:
            model = model_canvas_loader.get_current_model()
            if model:
                analyzer = PInvariantAnalyzer(model)
                result = analyzer.analyze()
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        return self.get_canvas_manager(drawing_area)
    
    def get_current_knowledge_base(self):
        """Get the knowledge base for the currently active document.
        
        The ModelKnowledgeBase aggregates multi-domain knowledge (topology,
        biology, biochemistry, dynamics) to enable intelligent model repair.
        
        Returns:
            ModelKnowledgeBase: The knowledge base for the active document,
                               or None if no document is open or KB not created.
        
        Example:
            # From Viability Panel:
            kb = model_canvas_loader.get_current_knowledge_base()
            if kb:
                dead_transitions = kb.get_dead_transitions()
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        return self.knowledge_bases.get(drawing_area)
    
    def get_knowledge_base(self, drawing_area):
        """Get the knowledge base for a specific drawing area.
        
        Args:
            drawing_area: The GtkDrawingArea widget
            
        Returns:
            ModelKnowledgeBase: The knowledge base, or None if not found
        """
        return self.knowledge_bases.get(drawing_area)
    
    def reset_current_canvas(self):
        """Reset the current canvas to initial state (File → New equivalent).
        
        Clears all objects, resets simulation, reinitializes palette.
        Preserves the canvas instance and ID scope.
        Uses the lifecycle system when available, falls back to legacy clear otherwise.
        
        Returns:
            bool: True if reset succeeded, False if no canvas or reset failed
            
        Example:
            # From File menu handler:
            if model_canvas_loader.reset_current_canvas():
                print("Canvas reset successfully")
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            pass
            return False
        
        # PHASE 4: Use lifecycle system if available
        if self.lifecycle_manager:
            try:
                self.lifecycle_manager.reset_canvas(drawing_area)
                # Trigger redraw
                drawing_area.queue_draw()
                return True
            except Exception as e:
                self.logger.debug(f"Lifecycle manager reset failed: {e}")
        
        # Legacy fallback: Manual cleanup
        try:
            manager = self.get_canvas_manager(drawing_area)
            if manager:
                pass
                # Clear objects
                manager.places.clear()
                manager.transitions.clear()
                manager.arcs.clear()
                
                # Reset simulation if controller exists
                if drawing_area in self.simulation_controllers:
                    controller = self.simulation_controllers[drawing_area]
                    if hasattr(controller, 'reset'):
                        controller.reset()
                
                # Trigger redraw
                drawing_area.queue_draw()
                return True
        except Exception as e:
            self.logger.debug(f"Manual canvas reset failed: {e}")
            return False
        
        return False
    
    def get_current_canvas_info(self):
        """Get information about the current canvas for UI display.
        
        Returns a dictionary with canvas metadata including:
        - canvas_id: Unique canvas identifier
        - scope_name: ID scope name  
        - next_place_id: Next place ID that will be generated
        - next_transition_id: Next transition ID that will be generated
        - next_arc_id: Next arc ID that will be generated
        - element_count: Number of elements in canvas
        
        Returns:
            dict: Canvas information, or None if no active canvas
            
        Example:
            info = model_canvas_loader.get_current_canvas_info()
            if info:
                print(f"Canvas: {info['scope_name']}")
                print(f"Next IDs: P{info['next_place_id']}, T{info['next_transition_id']}")
        """
        drawing_area = self.get_current_document()
        if drawing_area is None:
            return None
        
        info = {
            'canvas_id': id(drawing_area),
            'scope_name': None,
            'next_place_id': '?',
            'next_transition_id': '?',
            'next_arc_id': '?',
            'element_count': 0
        }
        
        # Get scope information from lifecycle if available
        if self.lifecycle_manager:
            try:
                context = self.lifecycle_manager.get_context(drawing_area)
                if context:
                    info['scope_name'] = context.id_scope
                    
                    # Get next IDs from the ID manager
                    # We can't generate without side effects, so we peek at counters
                    id_mgr = self.lifecycle_manager.id_manager
                    if hasattr(id_mgr, '_scopes') and context.id_scope in id_mgr._scopes:
                        scope_data = id_mgr._scopes[context.id_scope]
                        info['next_place_id'] = scope_data.get('place', 0) + 1
                        info['next_transition_id'] = scope_data.get('transition', 0) + 1
                        info['next_arc_id'] = scope_data.get('arc', 0) + 1
            except Exception as e:
                self.logger.debug(f"Could not retrieve ID scope data: {e}")
        
        # Get element count from canvas manager
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            place_count = len(manager.places) if hasattr(manager, 'places') else 0
            trans_count = len(manager.transitions) if hasattr(manager, 'transitions') else 0
            arc_count = len(manager.arcs) if hasattr(manager, 'arcs') else 0
            info['element_count'] = place_count + trans_count + arc_count
        
        return info


    def get_notebook(self):
        """Get the notebook widget for direct access.
        
        Returns:
            GtkNotebook: The canvas notebook widget.
        """
        return self.notebook

    def set_grid_style(self, style, drawing_area=None):
        """Set the grid style for a drawing area.
        
        Args:
            style: Grid style ('line', 'dot', or 'cross').
            drawing_area: GtkDrawingArea. If None, applies to current document.
        """
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            manager.set_grid_style(style)
            if drawing_area is None:
                drawing_area = self.get_current_document()
            if drawing_area:
                drawing_area.queue_draw()

    def cycle_grid_style(self, drawing_area=None):
        """Cycle through grid styles (line -> dot -> cross -> line).
        
        Args:
            drawing_area: GtkDrawingArea. If None, applies to current document.
        """
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            styles = [manager.GRID_STYLE_LINE, manager.GRID_STYLE_DOT, manager.GRID_STYLE_CROSS]
            current_index = styles.index(manager.grid_style)
            next_style = styles[(current_index + 1) % len(styles)]
            self.set_grid_style(next_style, drawing_area)

    def set_persistency_manager(self, persistency):
        """Set the persistency manager for file operations integration.
        
        This allows canvas operations (like clear canvas) to properly reset
        the persistency state when creating a new document.
        
        Args:
            persistency: NetObjPersistency instance from main application
        """
        self.persistency = persistency
        
        # Connect to persistency callbacks to update tab labels
        if hasattr(persistency, 'on_file_saved'):
            original_on_file_saved = persistency.on_file_saved
            def on_file_saved_wrapper(filepath):
                self._on_file_operation_completed(filepath, is_save=True)
                if original_on_file_saved:
                    original_on_file_saved(filepath)
            persistency.on_file_saved = on_file_saved_wrapper
        
        if hasattr(persistency, 'on_file_loaded'):
            original_on_file_loaded = persistency.on_file_loaded
            def on_file_loaded_wrapper(filepath, document):
                self._on_file_operation_completed(filepath, is_save=False)
                if original_on_file_loaded:
                    original_on_file_loaded(filepath, document)
            persistency.on_file_loaded = on_file_loaded_wrapper
        
        if hasattr(persistency, 'on_dirty_changed'):
            original_on_dirty_changed = persistency.on_dirty_changed
            def on_dirty_changed_wrapper(is_dirty):
                self._on_dirty_state_changed(is_dirty)
                if original_on_dirty_changed:
                    original_on_dirty_changed(is_dirty)
            persistency.on_dirty_changed = on_dirty_changed_wrapper
    
    def set_project(self, project):
        """Set the current project for structured save paths.
        
        When a project is open, all saves go to structured directories:
        - Petri net models → project/models/
        - Raw pathway data → project/pathways/
        - Metadata (BRENDA) → project/metadata/
        
        Args:
            project: Project instance or None
        """
        self.project = project
        
        # Propagate project to ALL pathway panels in all open documents
        for drawing_area, overlay in self.overlay_managers.items():
            if hasattr(overlay, 'pathway_panel_loader'):
                pathway_panel_loader = overlay.pathway_panel_loader
                # Update loader's project reference
                pathway_panel_loader.project = project
                # Propagate to panel and all its categories
                if hasattr(pathway_panel_loader, 'panel'):
                    pathway_panel_loader.panel.set_project(project)
    
    def get_active_pathway_panel(self):
        """Get the pathway panel loader for the currently active document.
        
        Returns:
            PathwayPanelLoader instance for active document, or None if no active document
        """
        drawing_area = self.get_current_document()
        if drawing_area and drawing_area in self.overlay_managers:
            overlay = self.overlay_managers[drawing_area]
            return getattr(overlay, 'pathway_panel_loader', None)
        return None

    def _on_file_operation_completed(self, filepath, is_save=True):
        """Handle file save/load completion to update tab label.
        
        Args:
            filepath: Full path to the saved/loaded file
            is_save: True if save operation, False if load operation
        """
        # print(f"\n[FILE_OP] ========================================")
        
        if not filepath:
            pass
            return
        
        # Extract filename with .shy extension
        filename = os.path.basename(filepath)
        # If filename doesn't have .shy extension, it might be without extension
        if not filename.endswith('.shy'):
            base = os.path.splitext(filename)[0]
            filename = f"{base}.shy"
        
        
        # Get current page
        current_page_num = self.notebook.get_current_page()
        if current_page_num < 0:
            pass
            return
        
        current_page = self.notebook.get_nth_page(current_page_num)
        
        # Update tab label with new filename (no asterisk after save/load)
        self._update_tab_label(current_page, filename, is_modified=False)
        
        # Also update the canvas manager's filename (without extension for internal use)
        drawing_area = self._get_drawing_area_from_page(current_page)
        
        if drawing_area and drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            # Store filename without extension in manager
            base_filename = os.path.splitext(filename)[0]
            manager.filename = base_filename
            
            # If this was a save operation, mark as saved (clears imported flag)
            if is_save:
                manager.mark_as_saved()

        # Emit EventBus events so Open Editors panel and other subscribers stay in sync
        try:
            import time
            from shypn.events import EventBus
            event_name = 'file.saved' if is_save else 'file.opened'
            EventBus.emit(event_name, {
                'filepath': filepath,
                'document': None,
                'timestamp': time.time()
            })
        except Exception:
            self.logger.debug("EventBus emit '%s' failed", event_name, exc_info=True)


    def _on_dirty_state_changed(self, is_dirty):
        """Handle dirty state change to update tab label modification indicator.
        
        Args:
            is_dirty: True if document has unsaved changes
        """
        # Get current page
        current_page_num = self.notebook.get_current_page()
        if current_page_num < 0:
            return
        
        current_page = self.notebook.get_nth_page(current_page_num)
        drawing_area = self._get_drawing_area_from_page(current_page)
        
        if drawing_area and drawing_area in self.canvas_managers:
            manager = self.canvas_managers[drawing_area]
            # Get base filename (without extension) from manager
            base_filename = manager.filename if hasattr(manager, 'filename') else 'default'
            
            # _update_tab_label will add .shy extension automatically
            # Update tab label with modification indicator (asterisk)
            self._update_tab_label(current_page, base_filename, is_modified=is_dirty)

    def _get_drawing_area_from_page(self, page_widget):
        """Extract drawing area from a notebook page widget.
        
        Args:
            page_widget: Page widget (usually Gtk.Overlay)
            
        Returns:
            Gtk.DrawingArea or None
        """
        if isinstance(page_widget, Gtk.Overlay):
            scrolled = page_widget.get_child()
            if isinstance(scrolled, Gtk.ScrolledWindow):
                drawing_area = scrolled.get_child()
                if hasattr(drawing_area, 'get_child'):
                    drawing_area = drawing_area.get_child()
                return drawing_area
        return None

    def set_right_panel_loader(self, right_panel_loader):
        """Set the right panel loader for data collector updates.
        
        This allows the notebook to update the right panel's data collector
        when the user switches between tabs with different simulations.
        
        Args:
            right_panel_loader: RightPanelLoader instance from main application
        """
        self.right_panel_loader = right_panel_loader
        if self.notebook and self.notebook.get_n_pages() > 0:
            current_page_num = self.notebook.get_current_page()
            current_page = self.notebook.get_nth_page(current_page_num)
            self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
        
        # Wire locality sync callback for all existing Report panels
        self._wire_locality_sync_for_existing_panels()
        
        # CRITICAL FIX: Wire data collector for all existing pages
        # This ensures the default canvas (page 0) gets its data collector wired
        # even if it was created before right_panel_loader was set
        self._wire_data_collectors_for_all_pages()
    
    def _wire_locality_sync_for_existing_panels(self):
        """Wire transition→report locality sync callbacks for all existing panels.
        
        Called when right_panel_loader is set, to retroactively wire callbacks
        for Report panels that were created before the transition panel existed.
        """
        if not self.right_panel_loader:
            return
        
        if not hasattr(self.right_panel_loader, 'transition_panel') or not self.right_panel_loader.transition_panel:
            return
        
        transition_panel = self.right_panel_loader.transition_panel
        
        # Create a SINGLE callback that dynamically routes to the current active document's report panel
        # This fixes the issue where the callback was captured for a specific document
        def on_transition_selected(transition, locality):
            """Called when user selects transition in Analyses panel.
            
            Routes the selection to the CURRENTLY ACTIVE document's report panel.
            """
            import logging
            lg = logging.getLogger(__name__)
            lg.debug(f"[LOCALITY_CALLBACK] Received transition {transition.name if hasattr(transition, 'name') else transition.id}")
            lg.debug(f"[LOCALITY_CALLBACK] Locality valid: {locality.is_valid if locality else False}")
            
            # Get the current active drawing area
            current_page_num = self.notebook.get_current_page()
            current_page = self.notebook.get_nth_page(current_page_num)
            
            drawing_area = None
            if isinstance(current_page, Gtk.Overlay):
                scrolled = current_page.get_child()
                if isinstance(scrolled, Gtk.ScrolledWindow):
                    drawing_area = scrolled.get_child()
                    if hasattr(drawing_area, 'get_child'):
                        drawing_area = drawing_area.get_child()
            
            if not drawing_area or drawing_area not in self.overlay_managers:
                lg.warning("[LOCALITY_CALLBACK] No active drawing area found")
                return
            
            # Get the report panel for the current document
            overlay_manager = self.overlay_managers[drawing_area]
            if not hasattr(overlay_manager, 'report_panel_loader'):
                lg.warning("[LOCALITY_CALLBACK] No report_panel_loader for active document")
                return
            
            report_panel_loader = overlay_manager.report_panel_loader
            if not report_panel_loader or not hasattr(report_panel_loader, 'panel'):
                lg.warning("[LOCALITY_CALLBACK] No report panel for active document")
                return
            
            report_panel = report_panel_loader.panel
            lg.debug(f"[LOCALITY_CALLBACK] Report panel categories: {len(report_panel.categories)}")
            
            # Find ModelsCategory in Report panel (for "Show Selected Locality")
            from shypn.ui.panels.report.model_structure_category import ModelsCategory
            for category in report_panel.categories:
                lg.debug(f"[LOCALITY_CALLBACK] Checking category: {type(category).__name__}")
                if isinstance(category, ModelsCategory):
                    lg.debug("[LOCALITY_CALLBACK] Found ModelsCategory, calling set_selected_locality()")
                    category.set_selected_locality(transition, locality)
                    lg.debug("[LOCALITY_CALLBACK] set_selected_locality() completed")
                    break
            else:
                lg.debug("[LOCALITY_CALLBACK] ModelsCategory not found in report panel")
            
            # Find DynamicAnalysesCategory in Report panel (for "Reaction Selected" simulation data)
            from shypn.ui.panels.report.parameters_category import DynamicAnalysesCategory
            for category in report_panel.categories:
                if isinstance(category, DynamicAnalysesCategory):
                    lg.debug("[LOCALITY_CALLBACK] Found DynamicAnalysesCategory, calling set_selected_reaction()")
                    category.set_selected_reaction(transition, locality)
                    lg.debug("[LOCALITY_CALLBACK] set_selected_reaction() completed")
                    break
            else:
                lg.debug("[LOCALITY_CALLBACK] DynamicAnalysesCategory not found in report panel")
        
        # Set the single dynamic callback (no loop needed, single global transition panel)
        transition_panel.on_selection_changed_callback = on_transition_selected
    
    def _wire_data_collectors_for_all_pages(self):
        """Wire data collectors for all existing pages.
        
        This is called when right_panel_loader is first set, to ensure all
        existing canvases (especially the default canvas on page 0) have their
        data collectors properly wired to the plot panels.
        """
        if not self.right_panel_loader:
            return
        
        if not self.notebook:
            return
        
        # Wire data collector for each existing page
        n_pages = self.notebook.get_n_pages()
        
        for page_num in range(n_pages):
            page = self.notebook.get_nth_page(page_num)
            if page:
                self._wire_data_collector_for_page(page)
    
    def wire_existing_canvases_to_right_panel(self):
        """Wire data_collector to right_panel for all existing canvases.
        
        This is called after both model_canvas_loader and right_panel_loader are initialized.
        It retroactively wires any canvases that were created before right_panel_loader existed
        (e.g., the startup default canvas).
        
        Simple solution: Just trigger the existing _on_notebook_page_changed() handler
        for the current page, which already has all the wiring logic.
        """
        if not self.right_panel_loader:
            return
        
        # Get the current page and trigger the page changed handler
        # This will execute all the existing wiring logic
        current_page_num = self.notebook.get_current_page()
        current_page = self.notebook.get_nth_page(current_page_num)
        
        # Manually call the page changed handler to wire the startup canvas
        self._on_notebook_page_changed(self.notebook, current_page, current_page_num)
    
    def _wire_viability_callbacks(self):
        """Wire simulation complete callbacks to Viability Panel for all existing controllers.
        
        OBSOLETE: This method is no longer needed as viability panels are now
        created per-document in _setup_edit_palettes() where callbacks are wired.
        
        Kept for backward compatibility but does nothing.
        """
        # All viability callback wiring is now done per-document during panel creation
        # See _setup_edit_palettes() PER-DOCUMENT VIABILITY PANEL section
        pass

    def set_context_menu_handler(self, handler):
        """Set the context menu handler for adding analysis menu items.
        
        This allows canvas object context menus to include "Add to Analysis" options.
        
        Args:
            handler: ContextMenuHandler instance
        """
        self.context_menu_handler = handler

    def set_file_explorer_panel(self, file_explorer_panel):
        """Set the file explorer panel for keyboard shortcut integration.
        
        This allows keyboard shortcuts (Ctrl+S, Ctrl+Shift+S) to trigger
        save operations through the file explorer panel.
        
        Args:
            file_explorer_panel: FileExplorerPanel instance from main application
        """
        self.file_explorer_panel = file_explorer_panel

    def _setup_canvas_context_menu(self, drawing_area, manager):
        """Wire context menu for drawing_area — delegates to CanvasContextMenuController (Sprint 22)."""
        self._ctx_menu_ctrl.setup_for_drawing_area(drawing_area, manager)

    def _on_zoom_in_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_zoom_in_clicked(menu, drawing_area, manager)

    def _on_zoom_out_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_zoom_out_clicked(menu, drawing_area, manager)

    def _on_fit_to_window_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_fit_to_window_clicked(menu, drawing_area, manager)

    def _on_rotate_90_cw_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_rotate_90_cw_clicked(menu, drawing_area, manager)

    def _on_rotate_90_ccw_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_rotate_90_ccw_clicked(menu, drawing_area, manager)

    def _on_rotate_180_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_rotate_180_clicked(menu, drawing_area, manager)

    def _on_reset_rotation_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_reset_rotation_clicked(menu, drawing_area, manager)

    def _on_grid_line_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_grid_line_clicked(menu, drawing_area, manager)

    def _on_grid_dot_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_grid_dot_clicked(menu, drawing_area, manager)

    def _on_grid_cross_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_grid_cross_clicked(menu, drawing_area, manager)

    def _on_clear_canvas_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_clear_canvas_clicked(menu, drawing_area, manager)

    def _on_create_center_marker_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_create_center_marker_clicked(menu, drawing_area, manager)

    def _on_reset_zoom_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_reset_zoom_clicked(menu, drawing_area, manager)

    def _on_center_view_clicked(self, menu, drawing_area, manager):
        self._ctx_menu_ctrl._on_center_view_clicked(menu, drawing_area, manager)

    # ------------------------------------------------------------------
    # Layout delegates — logic lives in CanvasLayoutController
    # ------------------------------------------------------------------

    def _on_layout_auto_clicked(self, menu, drawing_area, manager):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._on_layout_auto_clicked(menu, drawing_area, manager)

    def _on_layout_hierarchical_clicked(self, menu, drawing_area, manager):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._on_layout_hierarchical_clicked(menu, drawing_area, manager)

    def _on_layout_force_clicked(self, menu, drawing_area, manager):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._on_layout_force_clicked(menu, drawing_area, manager)

    def _on_layout_circular_clicked(self, menu, drawing_area, manager):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._on_layout_circular_clicked(menu, drawing_area, manager)

    def _on_layout_orthogonal_clicked(self, menu, drawing_area, manager):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._on_layout_orthogonal_clicked(menu, drawing_area, manager)

    def _apply_specific_layout(self, manager, drawing_area, algorithm, algorithm_name):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._apply_specific_layout(manager, drawing_area, algorithm, algorithm_name)

    def _show_layout_message(self, message, drawing_area):
        """Delegate to CanvasLayoutController."""
        self.layout_ctrl._show_layout_message(message, drawing_area)

    def _on_object_delete(self, obj, manager, drawing_area):
        """Delete an object from the canvas.
        
        Args:
            obj: Object to delete (Place, Transition, or Arc)
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Place, Transition, Arc

        # Record operation for undo (capture state before cascade deletion)
        if hasattr(manager, 'undo_manager'):
            try:
                from shypn.edit.snapshots import capture_delete_snapshots
                from shypn.edit.undo_operations import DeleteOperation
                snapshots = capture_delete_snapshots(manager, [obj])
                manager.undo_manager.push(DeleteOperation(snapshots))
            except Exception:
                # Fallback: inline snapshot capture to avoid import-time issues
                def _inline_capture(manager, targets):
                    snaps = []
                    recorded_arc_ids = set()
                    def snap_arc(a):
                        return {
                            'kind': 'arc',
                            'id': getattr(a, 'id', None),
                            'label': getattr(a, 'label', None),
                            'source_id': getattr(a.source, 'id', None),
                            'target_id': getattr(a.target, 'id', None),
                        }
                    for target in targets:
                        if isinstance(target, Arc):
                            s = snap_arc(target)
                            if s['id'] and s['id'] not in recorded_arc_ids:
                                snaps.append(s)
                                recorded_arc_ids.add(s['id'])
                            continue
                        kind = 'place' if isinstance(target, Place) else 'transition'
                        base = {
                            'kind': kind,
                            'id': getattr(target, 'id', None),
                            'label': getattr(target, 'label', None),
                            'x': getattr(target, 'x', 0.0),
                            'y': getattr(target, 'y', 0.0),
                        }
                        if kind == 'place':
                            base['radius'] = getattr(target, 'radius', None)
                        else:
                            base['width'] = getattr(target, 'width', None)
                            base['height'] = getattr(target, 'height', None)
                        incident = []
                        connected_ids = []
                        for a in manager.arcs:
                            if a.source == target or a.target == target:
                                a_id = getattr(a, 'id', None)
                                if a_id and a_id not in recorded_arc_ids:
                                    incident.append(snap_arc(a))
                                    connected_ids.append(a_id)
                                    recorded_arc_ids.add(a_id)
                        base['connected_arc_ids'] = connected_ids
                        base['arcs'] = incident
                        snaps.append(base)
                    return snaps
                try:
                    from shypn.edit.undo_operations import DeleteOperation
                    snapshots = _inline_capture(manager, [obj])
                    manager.undo_manager.push(DeleteOperation(snapshots))
                except (ImportError, AttributeError, TypeError) as e:
                    self.logger.debug(f"Failed to push undo operation for object deletion: {e}")

        # Perform deletion using facade methods to ensure cascade + observers
        if isinstance(obj, Place):
            if obj in manager.places:
                manager.remove_place(obj)
        elif isinstance(obj, Transition):
            if obj in manager.transitions:
                manager.remove_transition(obj)
        elif isinstance(obj, Arc):
            if obj in manager.arcs:
                manager.remove_arc(obj)
        
        if obj.selected:
            manager.selection_manager.deselect(obj)
        if manager.selection_manager.is_edit_mode() and manager.selection_manager.edit_target == obj:
            manager.selection_manager.exit_edit_mode()
        manager.mark_dirty()
        drawing_area.queue_draw()

    def _on_object_edit_mode(self, obj, manager, drawing_area):
        """Enter EDIT mode for an object.
        
        Args:
            obj: Object to edit
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Clear arc creation state to prevent spurious arc creation
        arc_state = self._canvas_ctx[drawing_area].arc if drawing_area in self._canvas_ctx else None
        if arc_state:
            arc_state['source'] = None
            arc_state['ignore_next_release'] = True  # Ignore any queued mouse events
        
        if not obj.selected:
            manager.selection_manager.select(obj, multi=False, manager=manager)
        manager.selection_manager.enter_edit_mode(obj, manager=manager)
        drawing_area.queue_draw()
    
    def _on_toggle_recording(self, obj, manager, drawing_area):
        """Toggle batch mode recording for an object (place or transition).
        
        Args:
            obj: Object to toggle recording (Place or Transition)
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Get simulation settings from manager
        if not hasattr(manager, 'simulation_settings'):
            print("Warning: No simulation settings available for recording")
            return
        
        settings = manager.simulation_settings
        if not settings or not hasattr(settings, 'is_object_recorded'):
            print("Warning: Simulation settings not properly initialized")
            return
        
        # Toggle recording state
        obj_id = obj.id
        
        # Define recording indicator color (orange for all recorded objects)
        RECORDING_COLOR = (1.0, 0.6, 0.0)  # RGB: orange
        
        # Import default colors
        from shypn.netobjs import Place, Transition
        from shypn.utils.color_schema_manager import ColorSchemaManager
        
        if settings.is_object_recorded(obj_id):
            settings.remove_recorded_object(obj_id)
            
            # Restore type-appropriate default colors
            if isinstance(obj, Place):
                ColorSchemaManager.reset_place_color(obj)
            elif isinstance(obj, Transition):
                ColorSchemaManager.reset_transition_colors(obj)
        else:
            settings.add_recorded_object(obj_id)
            
            # Apply recording color (orange for all types)
            if isinstance(obj, Place):
                obj.border_color = ColorSchemaManager.RECORDING_COLOR
            elif isinstance(obj, Transition):
                obj.border_color = ColorSchemaManager.RECORDING_COLOR
                obj.fill_color = ColorSchemaManager.RECORDING_COLOR
        
        # Trigger on_changed callback if available
        if hasattr(obj, 'on_changed') and obj.on_changed:
            obj.on_changed()
        
        # Redraw to show visual indicator
        drawing_area.queue_draw()

    def _on_object_properties(self, obj, manager, drawing_area):
        """Open properties dialog for an object.
        
        Args:
            obj: Object to edit properties for
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # ============================================================================
        # WAYLAND FIX: Close any open context menu BEFORE opening property dialog
        # This prevents menu/dialog parent conflicts on Wayland
        # ============================================================================
        if hasattr(self, '_active_context_menu') and self._active_context_menu:
            try:
                self._active_context_menu.popdown()
                self._active_context_menu.hide()
                # Give Wayland time to process menu destruction
                from gi.repository import GLib
                # Process ALL pending events to ensure menu is fully closed
                for _ in range(10):  # Process multiple times
                    while GLib.MainContext.default().pending():
                        GLib.MainContext.default().iteration(False)
            except (TypeError, AttributeError, RuntimeError) as e:
                self.logger.debug(f"Failed to cleanup context menu on Wayland: {e}")
            self._active_context_menu = None
        
        # Give Wayland a moment to fully process menu destruction
        import time
        time.sleep(0.05)  # 50ms delay
        
        # CRITICAL: Clear ALL arc creation state before opening dialog
        # This prevents spurious arc creation when dialog closes
        arc_state = self._canvas_ctx[drawing_area].arc if drawing_area in self._canvas_ctx else None
        if arc_state:
            arc_state['source'] = None
            arc_state['cursor_pos'] = (0, 0)
            arc_state['ignore_next_release'] = True
        
        # Also temporarily switch tool if arc tool is active
        original_tool = None
        if manager.is_tool_active() and manager.get_tool() == 'arc':
            original_tool = 'arc'
            manager.set_tool('select')  # Force to select mode during dialog
        
        from shypn.netobjs import Place, Transition, Arc

        # CRITICAL: Ensure parent_window is valid for Wayland
        if not self.parent_window:
            return
        
        # WAYLAND FIX: Ensure the canvas page widget AND drawing area are mapped before opening dialog
        # On Wayland, dialogs require the entire widget hierarchy to be fully visible and mapped
        # Get the page widget (overlay) for this drawing area
        page_widget = None
        for i in range(self.notebook.get_n_pages()):
            page = self.notebook.get_nth_page(i)
            page_drawing = self._get_drawing_area_from_page(page)
            if page_drawing == drawing_area:
                page_widget = page
                break
        
        # Check if BOTH page widget and drawing area are mapped
        page_mapped = page_widget.get_mapped() if page_widget else False
        drawing_mapped = drawing_area.get_mapped()
        page_realized = page_widget.get_realized() if page_widget else False
        drawing_realized = drawing_area.get_realized()
        
        # CRITICAL: Also check if this page is the CURRENT page in the notebook
        # On Wayland, dialogs can only attach to widgets on the visible/current page
        current_page_num = self.notebook.get_current_page()
        page_num = -1
        if page_widget:
            page_num = self.notebook.page_num(page_widget)
        is_current_page = (page_num == current_page_num)
        
        if not (page_mapped and drawing_mapped and is_current_page):
            # Use timeout to defer dialog opening until both widgets are mapped
            from gi.repository import GLib
            
            retry_count = [0]  # Use list to allow modification in nested function
            MAX_RETRIES = 20  # 20 retries * 50ms = 1 second max wait
            
            def open_when_mapped():
                retry_count[0] += 1
                page_ready = page_widget.get_mapped() if page_widget else False
                drawing_ready = drawing_area.get_mapped()
                is_current = (self.notebook.page_num(page_widget) == self.notebook.get_current_page()) if page_widget else False
                
                if page_ready and drawing_ready and is_current:
                    pass
                    # Call this function again now that widgets are mapped
                    self._on_object_properties(obj, manager, drawing_area)
                    return False  # Don't repeat
                elif retry_count[0] >= MAX_RETRIES:
                    print(f"  Final state: page_ready={page_ready}, drawing_ready={drawing_ready}, is_current={is_current}")
                    return False  # Give up
                else:
                    return True  # Keep checking
            
            # Check every 50ms for up to 1 second
            GLib.timeout_add(50, open_when_mapped)
            return
        
        # Check the drawing area's toplevel for Wayland compatibility
        toplevel = drawing_area.get_toplevel()
        if toplevel and isinstance(toplevel, Gtk.Window):
            pass
        
        # WAYLAND FIX: Use main_window instead of parent_window (which is never set)
        # main_window is set in shypn.py after ModelCanvasLoader initialization
        parent_window = getattr(self, 'main_window', None)
        
        dialog_loader = self._create_properties_dialog(obj, parent_window, manager, drawing_area)
        if dialog_loader is None:
            return

        def on_properties_changed(loader):
            # CRITICAL FIX: Use loader.arc_obj instead of closure obj
            # After arc transformation, obj is stale (old arc removed from model)
            # but loader.arc_obj is updated to point to the new arc
            if isinstance(obj, Arc):
                # Get current arc from dialog (might be transformed)
                current_arc = loader.arc_obj if hasattr(loader, 'arc_obj') else obj
                
                # Clear behavior cache for ALL transitions connected to this arc
                # This is critical when arc type changes (normal ↔ test ↔ inhibitor)
                # because transition enablement/firing behavior depends on arc consumption
                controller = self.get_canvas_controller(drawing_area)
                if controller:
                    # CRITICAL: Invalidate ModelAdapter arc cache
                    # The ModelAdapter caches arcs in _arcs_dict, and when an arc is
                    # transformed (Arc → TestArc), behaviors retrieve arcs from the
                    # CACHED dictionary which contains the old Arc with wrong arc_type
                    if hasattr(controller, 'model_adapter') and controller.model_adapter:
                        controller.model_adapter.invalidate_caches()
                    
                    # Find all transitions connected to the arc's source or target
                    arc_source = getattr(current_arc, 'source', None)
                    arc_target = getattr(current_arc, 'target', None)
                    
                    # If arc connects to a transition, clear that transition's behavior
                    # Note: Transition is imported at module level (line 45)
                    if isinstance(arc_source, Transition) and arc_source.id in controller.behavior_cache:
                        del controller.behavior_cache[arc_source.id]
                    if isinstance(arc_target, Transition) and arc_target.id in controller.behavior_cache:
                        del controller.behavior_cache[arc_target.id]
            drawing_area.queue_draw()
            
            # MANAGER SYNCHRONIZATION FIX: Use canvas-centric controller access
            # This works reliably across ALL canvas creation paths (Default Canvas,
            # File New, File Open, KEGG Import, SBML Import) because controllers are
            # keyed by drawing_area in self.simulation_controllers dict.
            # Previous code used overlay_manager.get_palette('simulate_tools') which
            # was unreliable due to palette structure variations across paths.
            if isinstance(obj, Transition):
                controller = self.get_canvas_controller(drawing_area)
                if controller:
                    pass
                    # Clear behavior cache when transition type/properties change
                    # This forces behavior algorithm recompilation on next simulation step
                    controller.behavior_cache.pop(id(obj), None)
                    
                    # CRITICAL: If transition became a source transition, enable it immediately
                    # This allows simulation to run without needing to press Reset
                    if getattr(obj, 'is_source', False):
                        if id(obj) in controller.transition_states:
                            state = controller.transition_states[id(obj)]
                            if state.enablement_time is None:
                                state.enablement_time = controller.time
                    
                    # Clear historical data so plot shows new rate function immediately
                    if hasattr(controller, 'data_collector') and controller.data_collector:
                        controller.data_collector.clear_transition(obj.id)
                
                # CRITICAL: Notify manager observers so controller gets 'modified' event
                # This ensures the observer pattern properly handles property changes
                manager._notify_observers('modified', obj)
            
            if isinstance(obj, (Place, Transition)) and self.right_panel_loader:
                if hasattr(self.right_panel_loader, 'place_panel') and self.right_panel_loader.place_panel:
                    if isinstance(obj, Place):
                        if obj in self.right_panel_loader.place_panel.selected_objects:
                            self.right_panel_loader.place_panel.needs_update = True
                if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                    if isinstance(obj, Transition):
                        if obj in self.right_panel_loader.transition_panel.selected_objects:
                            self.right_panel_loader.transition_panel.needs_update = True
        dialog_loader.connect('properties-changed', on_properties_changed)
        
        # Show dialog
        self._show_dialog_safely(dialog_loader, drawing_area, original_tool, manager)
    
    # ------------------------------------------------------------------
    # Properties dialog helpers (split from _on_object_properties)
    # ------------------------------------------------------------------

    def _get_simulation_data_collector(self, drawing_area):
        """Return the DataCollector for the given drawing area's simulate palette.

        Returns ``None`` when no matching palette is found.
        """
        overlay_manager = self.overlay_managers.get(drawing_area)
        if overlay_manager is None:
            return None
        swissknife = getattr(overlay_manager, 'swissknife_palette', None)
        if swissknife is None:
            return None
        # New architecture: registry holds widget palette instances
        registry = getattr(swissknife, 'registry', None)
        if registry and hasattr(registry, 'widget_palette_instances'):
            simulate_tools = registry.widget_palette_instances.get('simulate')
        else:
            simulate_tools = getattr(swissknife, 'widget_palette_instances', {}).get('simulate')
        return getattr(simulate_tools, 'data_collector', None) if simulate_tools else None

    def _create_properties_dialog(self, obj, parent_window, manager, drawing_area):
        """Return the appropriate properties dialog loader for *obj*.

        Uses a type → factory dispatch so that adding new object types requires
        only an additional entry rather than a growing elif chain.

        Returns ``None`` when *obj* is not a recognised net-object type.
        """
        from shypn.netobjs import Place, Transition, Arc
        from shypn.helpers.place_prop_dialog_loader import create_place_prop_dialog
        from shypn.helpers.transition_prop_dialog_loader import create_transition_prop_dialog
        from shypn.helpers.arc_prop_dialog_loader import create_arc_prop_dialog

        common = dict(parent_window=parent_window, persistency_manager=self.persistency, model=manager)

        for cls, factory in [
            (Place, lambda o: create_place_prop_dialog(o, **common)),
            (Transition, lambda o: create_transition_prop_dialog(
                o, data_collector=self._get_simulation_data_collector(drawing_area), **common)),
            (Arc, lambda o: create_arc_prop_dialog(o, **common)),
        ]:
            if isinstance(obj, cls):
                return factory(obj)
        return None

    def _show_dialog_safely(self, dialog_loader, drawing_area, original_tool, manager):
        """Show dialog with error handling.
        
        Args:
            dialog_loader: The dialog loader instance
            drawing_area: The canvas drawing area
            original_tool: The original tool before dialog (for restoration)
            manager: The canvas manager
        """
        try:
            pass
            # The dialog_loader already has parent_window set during creation
            # We don't need to set transient_for again - it's already configured
            
            response = dialog_loader.run()
            
            if response == Gtk.ResponseType.OK:
                drawing_area.queue_draw()
                
                # Update simulation controller state after transition type/property changes
                # This ensures newly created or type-switched stochastic/timed transitions
                # are properly scheduled when the simulation starts
                controller = self.get_canvas_controller(drawing_area)
                if controller:
                    controller._update_enablement_states()
        except Exception as e:
            import traceback
            traceback.print_exc()
        finally:
            pass
            # CRITICAL: Always destroy dialog to prevent orphaned widgets
            # Orphaned widgets cause Wayland focus issues and app crashes
            dialog_loader.destroy()
        
        # Restore original tool if we switched it
        if original_tool == 'arc':
            manager.set_tool('arc')
        
        # Clear arc creation state again after dialog closes to prevent spurious arc creation
        # This handles the case where mouse release happens after dialog closes
        arc_state = self._canvas_ctx[drawing_area].arc if drawing_area in self._canvas_ctx else None
        if arc_state:
            arc_state['source'] = None
            arc_state['cursor_pos'] = (0, 0)

    def _on_transition_type_change(self, transition, new_type, manager, drawing_area):
        """Handle transition type change from context menu.
        
        Args:
            transition: Transition object
            new_type: New transition type ('immediate', 'timed', 'stochastic', 'continuous')
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.netobjs import Transition
        old_type = getattr(transition, 'transition_type', 'continuous')
        if old_type == new_type:
            return
        transition.transition_type = new_type
        if self.persistency:
            self.persistency.mark_dirty()
        if drawing_area in self.overlay_managers:
            overlay_manager = self.overlay_managers[drawing_area]
            simulate_tools = overlay_manager.get_palette('simulate_tools')
            if simulate_tools and simulate_tools.simulation:
                simulate_tools.simulation.invalidate_behavior_cache(transition.id)
        if self.right_panel_loader:
            if hasattr(self.right_panel_loader, 'transition_panel') and self.right_panel_loader.transition_panel:
                if transition in self.right_panel_loader.transition_panel.selected_objects:
                    self.right_panel_loader.transition_panel.needs_update = True
        drawing_area.queue_draw()

    def _on_transition_flip_orientation(self, transition, manager, drawing_area):
        """Handle flip orientation from context menu.
        
        Swaps the width and height of the transition rectangle.
        
        Args:
            transition: Transition object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        if hasattr(transition, 'width') and hasattr(transition, 'height'):
            # Swap width and height
            transition.width, transition.height = transition.height, transition.width
            
            # Mark document dirty
            if self.persistency:
                self.persistency.mark_dirty()
            
            # Redraw canvas
            drawing_area.queue_draw()
    
    def _on_convert_to_signal(self, place, signal_type, manager, drawing_area):
        """Convert place to signal place with specified type.
        
        Also converts all connected normal arcs to SignalFlowArcs to maintain
        semantic consistency (signal places must use signal flow arcs).
        
        Args:
            place: Place object to convert
            signal_type: Signal type ('energy', 'regulatory', 'quorum', 'spatial')
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Set signal place properties
        place.is_signal_place = True
        place.signal_type = signal_type
        
        # Apply normalized color schema using ColorSchemaManager
        from shypn.utils.color_schema_manager import ColorSchemaManager
        place.shape = 'hexagon'
        ColorSchemaManager.reset_place_color(place)  # Blue border for signal places
        
        # Convert connected arcs to SignalFlowArcs
        from shypn.netobjs.test_arc import TestArc
        from shypn.netobjs.inhibitor_arc import InhibitorArc
        from shypn.utils.arc_transform import convert_to_signal_flow, is_signal_flow
        
        arcs_converted = 0
        arcs_to_replace = []  # List of (old_arc, new_arc) tuples
        
        for arc in manager.arcs[:]:  # Iterate over copy to allow modification
            # Skip if arc doesn't connect to this place
            if arc.source != place and arc.target != place:
                continue
            
            # Skip if arc is already a signal flow arc (straight or curved)
            if is_signal_flow(arc):
                continue
            
            # Skip test arcs and inhibitor arcs (they have special semantics)
            if isinstance(arc, (TestArc, InhibitorArc)):
                continue
            
            # Convert Arc or CurvedArc to SignalFlowArc / CurvedSignalFlowArc
            # (curvature is preserved by convert_to_signal_flow)
            # ColorSchemaManager is applied inside the constructor via reset_arc_color
            try:
                new_arc = convert_to_signal_flow(arc)
                arcs_to_replace.append((arc, new_arc))
                arcs_converted += 1
            except ValueError as e:
                print(f"Warning: Failed to convert arc {arc.id}: {e}")
        
        # Replace arcs in manager
        for old_arc, new_arc in arcs_to_replace:
            manager.replace_arc(old_arc, new_arc)
        
        # Mark document dirty
        if self.persistency:
            self.persistency.mark_dirty()
        
        # Redraw canvas
        drawing_area.queue_draw()
        
        # Show confirmation
        type_labels = {
            'energy': 'Ψₑ - Energy/Metabolic State',
            'regulatory': 'Ψᵣ - Regulatory/Gene Expression',
            'quorum': 'Ψq - Quorum/Cell Communication',
            'spatial': 'Ψₛ - Spatial/Compartment Sensing'
        }
        type_label = type_labels.get(signal_type, signal_type)
        
        if arcs_converted > 0:
            print(f"Converted '{place.name}' to signal place: {type_label}")
            print(f"  → Converted {arcs_converted} connected arc(s) to SignalFlowArc")
        # else:
        #     print(f"Converted '{place.name}' to signal place: {type_label}")

        # Notify environment panel (and any other listeners)
        try:
            from shypn.events import EventBus
            from shypn.core.document_id import doc_id
            EventBus.emit('model.place.modified',
                          {'object': place, 'object_id': place.id},
                          document_id=doc_id(drawing_area))
        except Exception:
            pass

    def _on_remove_signal_designation(self, place, manager, drawing_area):
        """Remove signal place designation from place.
        
        Also converts SignalFlowArcs back to normal Arcs if they no longer
        connect to any signal places.
        
        Args:
            place: Place object to modify
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        # Clear signal place properties
        place.is_signal_place = False
        place.signal_type = None
        
        # Restore default appearance using ColorSchemaManager
        from shypn.utils.color_schema_manager import ColorSchemaManager
        place.shape = 'circle'
        ColorSchemaManager.reset_place_color(place)
        
        # Convert SignalFlowArcs back to normal Arcs if they don't connect to other signal places
        from shypn.netobjs.place import Place
        from shypn.utils.arc_transform import convert_to_normal, is_signal_flow
        
        arcs_converted = 0
        arcs_to_replace = []  # List of (old_arc, new_arc) tuples
        
        for arc in manager.arcs[:]:  # Iterate over copy to allow modification
            # Skip if arc doesn't connect to this place
            if arc.source != place and arc.target != place:
                continue
            
            # Only process signal flow arcs (straight or curved)
            if not is_signal_flow(arc):
                continue
            
            # Check if arc still connects to another signal place
            source_is_signal = (isinstance(arc.source, Place) and 
                               getattr(arc.source, 'is_signal_place', False))
            target_is_signal = (isinstance(arc.target, Place) and 
                               getattr(arc.target, 'is_signal_place', False))
            
            # If arc no longer connects to any signal place, convert back to normal
            if not (source_is_signal or target_is_signal):
                try:
                    new_arc = convert_to_normal(arc)
                    arcs_to_replace.append((arc, new_arc))
                    arcs_converted += 1
                except Exception as e:
                    print(f"Warning: Failed to convert arc {arc.id} back to normal: {e}")
        
        # Replace arcs in manager
        for old_arc, new_arc in arcs_to_replace:
            manager.replace_arc(old_arc, new_arc)
        
        # Mark document dirty
        if self.persistency:
            self.persistency.mark_dirty()
        
        # Redraw canvas
        drawing_area.queue_draw()
        
        if arcs_converted > 0:
            print(f"Removed signal designation from '{place.name}'")
            print(f"  → Converted {arcs_converted} SignalFlowArc(s) back to normal Arc")
        else:
            print(f"Removed signal designation from '{place.name}'")

        # Notify environment panel (and any other listeners)
        try:
            from shypn.events import EventBus
            from shypn.core.document_id import doc_id
            EventBus.emit('model.place.modified',
                          {'object': place, 'object_id': place.id},
                          document_id=doc_id(drawing_area))
        except Exception:
            pass

    def _on_arc_edit_weight(self, arc, manager, drawing_area):
        """Quick edit arc weight.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        dialog = Gtk.Dialog(title=f'Edit {arc.name} Weight', parent=self.parent_window, modal=True, destroy_with_parent=True)
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        content_area = dialog.get_content_area()
        content_area.set_spacing(10)
        content_area.set_border_width(10)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        label = Gtk.Label(label='Weight:')
        box.pack_start(label, False, False, 0)
        weight_spin = Gtk.SpinButton()
        weight_spin.set_adjustment(Gtk.Adjustment(value=arc.weight, lower=1, upper=999, step_increment=1))
        weight_spin.set_digits(0)
        box.pack_start(weight_spin, True, True, 0)
        box.show_all()
        content_area.pack_start(box, True, True, 0)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_weight = int(weight_spin.get_value())
            if new_weight != arc.weight:
                arc.set_weight(new_weight)
                manager.mark_modified()
                drawing_area.queue_draw()
        dialog.destroy()

    def _on_arc_make_curved(self, arc, manager, drawing_area):
        """Transform arc to curved.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import make_curved
        
        new_arc = make_curved(arc)
        manager.replace_arc(arc, new_arc)
        drawing_area.queue_draw()

    def _on_arc_make_straight(self, arc, manager, drawing_area):
        """Transform arc to straight.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import make_straight
        
        new_arc = make_straight(arc)
        manager.replace_arc(arc, new_arc)
        drawing_area.queue_draw()

    def _on_arc_convert_to_inhibitor(self, arc, manager, drawing_area):
        """Convert arc to inhibitor type.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_inhibitor
        
        
        try:
            new_arc = convert_to_inhibitor(arc)
            manager.replace_arc(arc, new_arc)
            
            # Invalidate ModelAdapter cache if simulation is running
            self._invalidate_simulation_cache(manager)
            
            drawing_area.queue_draw()
        except ValueError as e:
            # Invalid transformation (e.g., Transition → Place)
            self._show_error_dialog(str(e))
            return

    def _on_arc_convert_to_normal(self, arc, manager, drawing_area):
        """Convert arc to normal type.
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_normal
        
        new_arc = convert_to_normal(arc)
        manager.replace_arc(arc, new_arc)
        
        # Invalidate ModelAdapter cache if simulation is running
        self._invalidate_simulation_cache(manager)
        
        drawing_area.queue_draw()
    
    def _on_arc_convert_to_test(self, arc, manager, drawing_area):
        """Convert arc to test type (catalyst).
        
        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_test
        
        try:
            new_arc = convert_to_test(arc)
            manager.replace_arc(arc, new_arc)
            
            # Invalidate ModelAdapter cache if simulation is running
            self._invalidate_simulation_cache(manager)
            
            drawing_area.queue_draw()
        except ValueError as e:
            # Invalid transformation (e.g., Transition → Place)
            self._show_error_dialog(str(e))
            return

    def _on_arc_convert_to_signal_flow(self, arc, manager, drawing_area):
        """Convert arc to signal flow type.

        Signal flow arcs carry dual semantics: they consume/produce tokens
        (like normal arcs) and also propagate information to the vertical
        decision hierarchy layers. Curvature is preserved.

        Args:
            arc: Arc object
            manager: ModelCanvasManager instance
            drawing_area: GtkDrawingArea widget
        """
        from shypn.utils.arc_transform import convert_to_signal_flow

        try:
            new_arc = convert_to_signal_flow(arc)
            manager.replace_arc(arc, new_arc)

            # Invalidate ModelAdapter cache if simulation is running
            self._invalidate_simulation_cache(manager)

            drawing_area.queue_draw()
        except ValueError as e:
            self._show_error_dialog(str(e))
            return
    
    def _generate_unique_name(self, manager, base_name):
        """Generate a unique name for a pasted object.
        
        Args:
            manager: ModelCanvasManager instance
            base_name: Base name to start from
            
        Returns:
            str: Unique name
        """
        # Extract base name without numeric suffix
        import re
        match = re.match(r'(.+?)(\d+)$', base_name)
        if match:
            prefix = match.group(1)
        else:
            prefix = base_name
        
        # Find all existing names
        existing_names = set()
        for place in manager.places:
            existing_names.add(place.name)
        for transition in manager.transitions:
            existing_names.add(transition.name)
        
        # Generate unique name
        counter = 1
        while True:
            candidate = f"{prefix}{counter}"
            if candidate not in existing_names:
                return candidate
            counter += 1
    
    def _invalidate_simulation_cache(self, manager):
        """Force simulation reinitialization after arc transformations.
        
        When an arc is converted (e.g., Arc → TestArc), the SubnetSimulator's
        subnet_model still holds references to the OLD arc objects. We must
        force reinitialization so the subnet is rebuilt with new arc instances.
        
        For RUNNING simulations, we must STOP them completely because behavior
        objects have cached references to old arc instances.
        
        Args:
            manager: ModelCanvasManager instance
        """
        # Try to find active simulation and force reinitialization
        try:
            # Method 1: Check document controller's viability panel (subnet simulator)
            if hasattr(manager, 'document_controller'):
                doc_controller = manager.document_controller
                # Viability panel has simulation controller
                if hasattr(doc_controller, 'viability_panel') and doc_controller.viability_panel:
                    viability_panel = doc_controller.viability_panel
                    if hasattr(viability_panel, 'subnet_simulator') and viability_panel.subnet_simulator:
                        simulator = viability_panel.subnet_simulator
                        # If simulation is initialized, force complete reinitialization
                        # This clears the old subnet and rebuilds with updated arc instances
                        if simulator.is_initialized():
                            # Clear old controller and subnet
                            simulator.controller = None
                            simulator.subnet_model = None
                            # Rebuild subnet with new arc instances from main model
                            simulator.initialize_simulation()
            
            # Method 2: UNIFIED CONTROLLER INVALIDATION
            # After Fix #2, overlay_manager.simulation_controller and canvas controller
            # should be the SAME instance. Invalidate whichever one exists.
            sim_controller = None
            was_running = False
            
            # Try overlay_manager first
            if hasattr(manager, 'overlay_manager') and manager.overlay_manager:
                overlay_manager = manager.overlay_manager
                if hasattr(overlay_manager, 'simulation_controller') and overlay_manager.simulation_controller:
                    sim_controller = overlay_manager.simulation_controller
            
            # Try canvas controller if overlay one not found
            if not sim_controller and hasattr(manager, '_drawing_area') and manager._drawing_area:
                sim_controller = self.get_canvas_controller(manager._drawing_area)
            
            # Now invalidate whichever controller we found
            if sim_controller:
                # CRITICAL: If simulation is running, STOP it completely
                # Behavior objects have cached arc references that won't update
                if hasattr(sim_controller, 'is_running') and sim_controller.is_running:
                    was_running = True
                    # Stop simulation completely
                    if hasattr(sim_controller, 'stop'):
                        sim_controller.stop()
                
                # Invalidate ModelAdapter caches to pick up new arc instances
                if hasattr(sim_controller, 'model_adapter') and sim_controller.model_adapter:
                    sim_controller.model_adapter.invalidate_caches()
                # Clear behavior cache so behaviors are recreated with new arcs
                if hasattr(sim_controller, 'behavior_cache'):
                    sim_controller.behavior_cache.clear()
                # Clear transition states (enablement times, scheduled times)
                if hasattr(sim_controller, 'transition_states'):
                    sim_controller.transition_states.clear()
                
                # Force rebuild of all behavior objects with new arc references
                if hasattr(sim_controller, '_behavior_objects'):
                    sim_controller._behavior_objects = {}
                
                # Log warning if simulation was stopped
                if was_running:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning("Simulation stopped due to arc transformation - please restart simulation to apply changes")
        except Exception:
            # Silently ignore if no active simulation found
            self.logger.debug("Simulation stop after arc transformation failed", exc_info=True)
    
    def _show_error_dialog(self, message):
        """Show an error dialog to the user.
        
        Args:
            message: Error message to display
        """
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text="Invalid Operation"
        )
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def _show_info_message(self, message):
        """Show an informational message to the user.
        
        Used for permission denials and state-based restrictions.
        
        Args:
            message: Information message to display
        """
        dialog = Gtk.MessageDialog(
            transient_for=None,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Action Not Allowed"
        )
        dialog.set_keep_above(True)  # Ensure dialog stays on top
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

def create_model_canvas(ui_path=None, create_initial_document=True):
    """Convenience function to create and load the model canvas loader.
    
    Args:
        ui_path: Optional path to model_canvas.ui.
        create_initial_document: If True, creates default document during load.
                                If False, caller must create document after wiring dependencies.
        
    Returns:
        ModelCanvasLoader: The loaded model canvas loader instance.
        
    Example:
        loader = create_model_canvas()
        container = loader.load()
        # Add to main window workspace
    """
    loader = ModelCanvasLoader(ui_path)
    loader.load(create_initial_document=create_initial_document)
    return loader