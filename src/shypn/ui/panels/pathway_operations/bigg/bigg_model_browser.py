"""BiGG model browser widget.

Provides a widget for browsing, filtering, and selecting BiGG models.
Wayland-safe with proper signal handler cleanup.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, Callable
import logging
import threading

from shypn.importer.bigg.bigg_model_fetcher import BiGGModelFetcher, BiGGModelInfo


class BiGGModelBrowser(Gtk.Box):
    """Widget for browsing and selecting BiGG models.
    
    Provides organism filtering, search, and model selection.
    Wayland-safe: properly manages widget lifecycle and signal handlers.
    
    Attributes:
        fetcher: BiGGModelFetcher service for API access
        _selected_model: Currently selected model
        _on_selection_changed: Callback for selection changes
        _signal_handlers: List of (handler_id, widget) for cleanup
    """
    
    def __init__(self, fetcher: BiGGModelFetcher):
        """Initialize model browser.
        
        Args:
            fetcher: BiGGModelFetcher service instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        self.fetcher = fetcher
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Track for Wayland-safe cleanup
        self._signal_handlers = []
        self._selected_model: Optional[BiGGModelInfo] = None
        self._on_selection_changed: Optional[Callable] = None
        
        self._build_ui()
        self._load_models_async()
    
    def _build_ui(self):
        """Build widget structure."""
        # Organism filter
        filter_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filter_label = Gtk.Label(label="Organism:")
        filter_label.set_xalign(0)
        filter_box.pack_start(filter_label, False, False, 0)
        
        self.organism_combo = Gtk.ComboBoxText()
        self.organism_combo.append_text("All Organisms")
        self.organism_combo.append_text("Escherichia coli")
        self.organism_combo.append_text("Saccharomyces cerevisiae")
        self.organism_combo.append_text("Homo sapiens")
        self.organism_combo.set_active(0)
        handler_id = self.organism_combo.connect("changed", self._on_organism_changed)
        self._signal_handlers.append((handler_id, self.organism_combo))
        
        filter_box.pack_start(self.organism_combo, True, True, 0)
        self.pack_start(filter_box, False, False, 0)
        
        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_label = Gtk.Label(label="Search:")
        search_label.set_xalign(0)
        search_box.pack_start(search_label, False, False, 0)
        
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Model ID or organism...")
        handler_id = self.search_entry.connect("search-changed", self._on_search_changed)
        self._signal_handlers.append((handler_id, self.search_entry))
        
        search_box.pack_start(self.search_entry, True, True, 0)
        self.pack_start(search_box, False, False, 0)
        
        # Model list with scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_size_request(-1, 300)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # ListStore: ID, Organism, Stats, Rxns, Mets, BiGGModelInfo object
        self.model_store = Gtk.ListStore(str, str, str, int, int, object)
        
        self.model_view = Gtk.TreeView(model=self.model_store)
        self.model_view.set_headers_visible(True)
        
        # ID column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Model ID", renderer, text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        column.set_min_width(120)
        self.model_view.append_column(column)
        
        # Organism column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Organism", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_resizable(True)
        column.set_expand(True)
        self.model_view.append_column(column)
        
        # Stats column
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Size", renderer, text=2)
        column.set_resizable(True)
        column.set_min_width(100)
        self.model_view.append_column(column)
        
        # Selection handling
        selection = self.model_view.get_selection()
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        handler_id = selection.connect("changed", self._on_model_selected)
        self._signal_handlers.append((handler_id, selection))
        
        scrolled.add(self.model_view)
        self.pack_start(scrolled, True, True, 0)
        
        # Status label
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>Loading models...</i>")
        self.status_label.set_xalign(0)
        self.pack_start(self.status_label, False, False, 0)
    
    def _load_models_async(self):
        """Load models in background thread."""
        def load():
            try:
                models = self.fetcher.fetch_models()
                GLib.idle_add(self._on_models_loaded, models, None)
            except Exception as e:
                GLib.idle_add(self._on_models_loaded, None, str(e))
        
        thread = threading.Thread(target=load, daemon=True)
        thread.start()
    
    def _on_models_loaded(self, models, error):
        """Handle models loaded (runs in main thread).
        
        Args:
            models: List of BiGGModelInfo or None if error
            error: Error message or None if success
        """
        if error:
            self.status_label.set_markup(f"<span color='red'>Error loading models: {error}</span>")
            self.logger.error(f"Failed to load models: {error}")
            return False
        
        self._populate_model_list(models)
        self.status_label.set_text(f"{len(models)} models available")
        self.logger.info(f"Loaded {len(models)} BiGG models")
        return False
    
    def _populate_model_list(self, models):
        """Populate tree view with models (runs in main thread).
        
        Args:
            models: List of BiGGModelInfo
        """
        self.model_store.clear()
        for model in models:
            stats = f"{model.reaction_count}R / {model.metabolite_count}M"
            self.model_store.append([
                model.id,
                model.organism,
                stats,
                model.reaction_count,
                model.metabolite_count,
                model
            ])
    
    def _on_organism_changed(self, combo):
        """Handle organism filter change."""
        organism = combo.get_active_text()
        
        try:
            if organism == "All Organisms":
                models = self.fetcher.fetch_models()
            else:
                models = self.fetcher.filter_by_organism(organism)
            
            self._populate_model_list(models)
            self.status_label.set_text(f"{len(models)} models available")
        except Exception as e:
            self.status_label.set_markup(f"<span color='red'>Error: {e}</span>")
            self.logger.error(f"Filtering error: {e}")
    
    def _on_search_changed(self, entry):
        """Handle search query change."""
        query = entry.get_text()
        
        try:
            if query:
                models = self.fetcher.search_models(query)
            else:
                models = self.fetcher.fetch_models()
            
            self._populate_model_list(models)
            self.status_label.set_text(f"{len(models)} models found")
        except Exception as e:
            self.status_label.set_markup(f"<span color='red'>Error: {e}</span>")
            self.logger.error(f"Search error: {e}")
    
    def _on_model_selected(self, selection):
        """Handle model selection."""
        model, iter = selection.get_selected()
        if iter:
            self._selected_model = model[iter][5]  # BiGGModelInfo object
            if self._on_selection_changed:
                self._on_selection_changed(self._selected_model)
    
    def get_selected_model(self) -> Optional[BiGGModelInfo]:
        """Get currently selected model.
        
        Returns:
            Selected BiGGModelInfo or None
        """
        return self._selected_model
    
    def set_selection_callback(self, callback: Callable[[BiGGModelInfo], None]):
        """Set callback for selection changes.
        
        Args:
            callback: Function to call when selection changes
        """
        self._on_selection_changed = callback
    
    def cleanup(self):
        """Clean up signal handlers (Wayland-safe)."""
        for handler_id, widget in self._signal_handlers:
            try:
                if widget and not widget.is_destroyed():
                    widget.disconnect(handler_id)
            except (AttributeError, TypeError) as e:
                # Widget already destroyed or invalid
                import logging
                logging.getLogger(__name__).debug(f"Signal disconnect failed: {e}")
                pass
        self._signal_handlers.clear()
        self.logger.debug("BiGGModelBrowser cleaned up")
    
    def do_destroy(self):
        """Override destroy to ensure cleanup."""
        self.cleanup()
        Gtk.Box.do_destroy(self)
