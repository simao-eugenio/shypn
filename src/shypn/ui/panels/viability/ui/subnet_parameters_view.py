#!/usr/bin/env python3
"""Subnet Parameters View - Manages editable parameter tables for Places/Transitions/Arcs.

Provides tabbed interface for viewing and editing subnet parameters with:
- Places: ID, Name, Marking (editable), Type, Label
- Transitions: ID, Name, Rate (editable), Formula (editable), Type, Label
- Arcs: ID, From, To, Weight (editable), Type
- Results: Time, Step, Transition, Markings (simulation results)

Features:
- Editable TreeView columns with validation
- Context menus for creating parameter sweeps
- Visual sweep indicators (colored backgrounds)
- Real-time synchronization with automation baseline

Author: Simão Eugénio
Date: January 22, 2026
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango


class SubnetParametersView(Gtk.Box):
    """Widget for displaying and editing subnet parameters in tabbed interface."""
    
    def __init__(self):
        """Initialize subnet parameters view."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Callbacks (set by parent panel)
        self.on_place_marking_edited = None
        self.on_transition_rate_edited = None
        self.on_transition_formula_edited = None
        self.on_arc_weight_edited = None
        self.on_create_sweep_from_place = None
        self.on_create_sweep_from_transition = None
        self.on_create_sweep_from_arc = None
        
        # Storage for sweep indicators
        self.swept_rows = {}  # {(param_type, param_id): TreeIter}
        
        # Build UI
        self._build_ui()
    
    def _build_ui(self):
        """Build expander with tabbed parameter interface."""
        # Expander
        self.subnet_expander = Gtk.Expander()
        self.subnet_expander.set_expanded(True)
        self.subnet_expander.set_margin_start(10)
        self.subnet_expander.set_margin_end(10)
        self.subnet_expander.set_margin_top(10)
        
        subnet_label = Gtk.Label()
        subnet_label.set_xalign(0)
        subnet_label.set_markup("<b>SUBNET PARAMETERS</b>")
        self.subnet_expander.set_label_widget(subnet_label)
        
        # Notebook (tabs for Places, Transitions, Arcs, Results)
        self.subnet_notebook = Gtk.Notebook()
        self.subnet_notebook.set_margin_start(12)
        self.subnet_notebook.set_margin_top(6)
        self.subnet_notebook.set_margin_bottom(6)
        
        # Places tab with editable TreeView
        places_scroll = Gtk.ScrolledWindow()
        places_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        places_scroll.set_size_request(-1, 200)
        
        self.places_treeview, self.places_store = self._create_places_treeview()
        places_scroll.add(self.places_treeview)
        self.subnet_notebook.append_page(places_scroll, Gtk.Label(label="Places"))
        
        # Transitions tab with editable TreeView
        transitions_scroll = Gtk.ScrolledWindow()
        transitions_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        transitions_scroll.set_size_request(-1, 200)
        
        self.transitions_treeview, self.transitions_store = self._create_transitions_treeview()
        transitions_scroll.add(self.transitions_treeview)
        self.subnet_notebook.append_page(transitions_scroll, Gtk.Label(label="Transitions"))
        
        # Arcs tab with editable TreeView
        arcs_scroll = Gtk.ScrolledWindow()
        arcs_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        arcs_scroll.set_size_request(-1, 200)
        
        self.arcs_treeview, self.arcs_store = self._create_arcs_treeview()
        arcs_scroll.add(self.arcs_treeview)
        self.subnet_notebook.append_page(arcs_scroll, Gtk.Label(label="Arcs"))
        
        # Results tab with simulation results
        results_scroll = Gtk.ScrolledWindow()
        results_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        results_scroll.set_size_request(-1, 200)
        
        self.results_treeview, self.results_store = self._create_results_treeview()
        results_scroll.add(self.results_treeview)
        self.subnet_notebook.append_page(results_scroll, Gtk.Label(label="Results"))
        
        self.subnet_expander.add(self.subnet_notebook)
        self.pack_start(self.subnet_expander, False, False, 0)
    
    def _create_places_treeview(self):
        """Create TreeView for editing place parameters.
        
        Columns: ID, Name, Marking (editable), Type, Label, Background
        """
        # Create ListStore: id, name, marking (int, editable), type, label, background
        store = Gtk.ListStore(str, str, int, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(1)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0, background=5)
        column_id.set_resizable(True)
        column_id.set_min_width(60)
        treeview.append_column(column_id)
        
        # Column 1: Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer_name, text=1, background=5)
        column_name.set_resizable(True)
        column_name.set_min_width(100)
        treeview.append_column(column_name)
        
        # Column 2: Marking (EDITABLE)
        renderer_marking = Gtk.CellRendererText()
        renderer_marking.set_property("editable", True)
        renderer_marking.connect("edited", self._on_place_marking_edited_internal, store)
        column_marking = Gtk.TreeViewColumn("Marking", renderer_marking, text=2, background=5)
        column_marking.set_resizable(True)
        column_marking.set_min_width(80)
        treeview.append_column(column_marking)
        
        # Column 3: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=3, background=5)
        column_type.set_resizable(True)
        column_type.set_min_width(100)
        treeview.append_column(column_type)
        
        # Column 4: Label
        renderer_label = Gtk.CellRendererText()
        column_label = Gtk.TreeViewColumn("Label", renderer_label, text=4, background=5)
        column_label.set_resizable(True)
        column_label.set_expand(True)
        column_label.set_min_width(150)
        treeview.append_column(column_label)
        
        # Add right-click context menu
        treeview.connect("button-press-event", self._on_places_table_button_press)
        
        return treeview, store
    
    def _create_transitions_treeview(self):
        """Create TreeView for editing transition parameters.
        
        Columns: ID, Name, Rate (editable), Formula (editable), Type, Label, Background
        """
        # Create ListStore: id, name, rate (float, editable), formula (str, editable), type, label, background
        store = Gtk.ListStore(str, str, float, str, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(1)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0, background=6)
        column_id.set_resizable(True)
        column_id.set_min_width(60)
        treeview.append_column(column_id)
        
        # Column 1: Name
        renderer_name = Gtk.CellRendererText()
        column_name = Gtk.TreeViewColumn("Name", renderer_name, text=1, background=6)
        column_name.set_resizable(True)
        column_name.set_min_width(100)
        treeview.append_column(column_name)
        
        # Column 2: Rate (EDITABLE)
        renderer_rate = Gtk.CellRendererText()
        renderer_rate.set_property("editable", True)
        renderer_rate.connect("edited", self._on_transition_rate_edited_internal, store)
        column_rate = Gtk.TreeViewColumn("Rate", renderer_rate, text=2, background=6)
        column_rate.set_resizable(True)
        column_rate.set_min_width(80)
        treeview.append_column(column_rate)
        
        # Column 3: Formula (EDITABLE)
        renderer_formula = Gtk.CellRendererText()
        renderer_formula.set_property("editable", True)
        renderer_formula.connect("edited", self._on_transition_formula_edited_internal, store)
        column_formula = Gtk.TreeViewColumn("Formula", renderer_formula, text=3, background=6)
        column_formula.set_resizable(True)
        column_formula.set_expand(True)
        column_formula.set_min_width(200)
        treeview.append_column(column_formula)
        
        # Column 4: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=4, background=6)
        column_type.set_resizable(True)
        column_type.set_min_width(100)
        treeview.append_column(column_type)
        
        # Column 5: Label
        renderer_label = Gtk.CellRendererText()
        column_label = Gtk.TreeViewColumn("Label", renderer_label, text=5, background=6)
        column_label.set_resizable(True)
        column_label.set_min_width(150)
        treeview.append_column(column_label)
        
        # Add right-click context menu
        treeview.connect("button-press-event", self._on_transitions_table_button_press)
        
        return treeview, store
    
    def _create_arcs_treeview(self):
        """Create TreeView for editing arc parameters.
        
        Columns: ID, From, To, Weight (editable), Type, Background
        """
        # Create ListStore: id, from_id, to_id, weight (int, editable), arc_type, background
        store = Gtk.ListStore(str, str, str, int, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        
        # Column 0: ID
        renderer_id = Gtk.CellRendererText()
        column_id = Gtk.TreeViewColumn("ID", renderer_id, text=0, background=5)
        column_id.set_resizable(True)
        column_id.set_min_width(80)
        treeview.append_column(column_id)
        
        # Column 1: From
        renderer_from = Gtk.CellRendererText()
        column_from = Gtk.TreeViewColumn("From", renderer_from, text=1, background=5)
        column_from.set_resizable(True)
        column_from.set_min_width(100)
        treeview.append_column(column_from)
        
        # Column 2: To
        renderer_to = Gtk.CellRendererText()
        column_to = Gtk.TreeViewColumn("To", renderer_to, text=2, background=5)
        column_to.set_resizable(True)
        column_to.set_min_width(100)
        treeview.append_column(column_to)
        
        # Column 3: Weight (EDITABLE)
        renderer_weight = Gtk.CellRendererText()
        renderer_weight.set_property("editable", True)
        renderer_weight.connect("edited", self._on_arc_weight_edited_internal, store)
        column_weight = Gtk.TreeViewColumn("Weight", renderer_weight, text=3, background=5)
        column_weight.set_resizable(True)
        column_weight.set_min_width(80)
        treeview.append_column(column_weight)
        
        # Column 4: Type
        renderer_type = Gtk.CellRendererText()
        column_type = Gtk.TreeViewColumn("Type", renderer_type, text=4, background=5)
        column_type.set_resizable(True)
        column_type.set_min_width(120)
        treeview.append_column(column_type)
        
        # Add right-click context menu
        treeview.connect("button-press-event", self._on_arcs_table_button_press)
        
        return treeview, store
    
    def _create_results_treeview(self):
        """Create TreeView for displaying simulation results.
        
        Columns: Label, Value1, Value2, Value3, Info
        """
        # Create ListStore: 5 string columns for flexible display
        store = Gtk.ListStore(str, str, str, str, str)
        
        # Create TreeView
        treeview = Gtk.TreeView(model=store)
        treeview.set_enable_search(True)
        treeview.set_search_column(0)
        
        # Column 0: Label/Name
        renderer_0 = Gtk.CellRendererText()
        column_0 = Gtk.TreeViewColumn("Label", renderer_0, text=0)
        column_0.set_resizable(True)
        column_0.set_min_width(150)
        treeview.append_column(column_0)
        
        # Column 1: Value 1
        renderer_1 = Gtk.CellRendererText()
        column_1 = Gtk.TreeViewColumn("Value 1", renderer_1, text=1)
        column_1.set_resizable(True)
        column_1.set_min_width(80)
        treeview.append_column(column_1)
        
        # Column 2: Value 2
        renderer_2 = Gtk.CellRendererText()
        column_2 = Gtk.TreeViewColumn("Value 2", renderer_2, text=2)
        column_2.set_resizable(True)
        column_2.set_min_width(80)
        treeview.append_column(column_2)
        
        # Column 3: Value 3
        renderer_3 = Gtk.CellRendererText()
        column_3 = Gtk.TreeViewColumn("Value 3", renderer_3, text=3)
        column_3.set_resizable(True)
        column_3.set_min_width(80)
        treeview.append_column(column_3)
        
        # Column 4: Info/Status
        renderer_4 = Gtk.CellRendererText()
        renderer_4.set_property("wrap-mode", Pango.WrapMode.WORD)
        renderer_4.set_property("wrap-width", 250)
        column_4 = Gtk.TreeViewColumn("Info", renderer_4, text=4)
        column_4.set_resizable(True)
        column_4.set_expand(True)
        column_4.set_min_width(200)
        treeview.append_column(column_4)
        
        return treeview, store
    
    # === EDIT CALLBACKS (delegate to parent) ===
    
    def _on_place_marking_edited_internal(self, widget, path, new_text, store):
        """Internal handler for place marking edits - delegates to parent callback."""
        if self.on_place_marking_edited:
            self.on_place_marking_edited(widget, path, new_text, store)
    
    def _on_transition_rate_edited_internal(self, widget, path, new_text, store):
        """Internal handler for transition rate edits - delegates to parent callback."""
        if self.on_transition_rate_edited:
            self.on_transition_rate_edited(widget, path, new_text, store)
    
    def _on_transition_formula_edited_internal(self, widget, path, new_text, store):
        """Internal handler for transition formula edits - delegates to parent callback."""
        if self.on_transition_formula_edited:
            self.on_transition_formula_edited(widget, path, new_text, store)
    
    def _on_arc_weight_edited_internal(self, widget, path, new_text, store):
        """Internal handler for arc weight edits - delegates to parent callback."""
        if self.on_arc_weight_edited:
            self.on_arc_weight_edited(widget, path, new_text, store)
    
    # === CONTEXT MENU HANDLERS ===
    
    def _on_places_table_button_press(self, treeview, event):
        """Handle right-click on places table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path = path_info[0]
            store = treeview.get_model()
            iter = store.get_iter(path)
            
            place_id = store.get_value(iter, 0)
            place_name = store.get_value(iter, 1)
            current_marking = store.get_value(iter, 2)
            
            # Create context menu
            menu = Gtk.Menu()
            
            item = Gtk.MenuItem(label=f"Create Sweep from '{place_name}'")
            item.connect("activate", lambda w: self.on_create_sweep_from_place(
                w, place_id, place_name, current_marking
            ) if self.on_create_sweep_from_place else None)
            menu.append(item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        
        return False
    
    def _on_transitions_table_button_press(self, treeview, event):
        """Handle right-click on transitions table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path = path_info[0]
            store = treeview.get_model()
            iter = store.get_iter(path)
            
            trans_id = store.get_value(iter, 0)
            trans_name = store.get_value(iter, 1)
            current_rate = store.get_value(iter, 2)
            
            # Create context menu
            menu = Gtk.Menu()
            
            item = Gtk.MenuItem(label=f"Create Sweep from '{trans_name}'")
            item.connect("activate", lambda w: self.on_create_sweep_from_transition(
                w, trans_id, trans_name, current_rate
            ) if self.on_create_sweep_from_transition else None)
            menu.append(item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        
        return False
    
    def _on_arcs_table_button_press(self, treeview, event):
        """Handle right-click on arcs table to show context menu."""
        if event.button == 3:  # Right-click
            # Get clicked row
            path_info = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path_info is None:
                return False
            
            path = path_info[0]
            store = treeview.get_model()
            iter = store.get_iter(path)
            
            arc_id = store.get_value(iter, 0)
            from_id = store.get_value(iter, 1)
            to_id = store.get_value(iter, 2)
            current_weight = store.get_value(iter, 3)
            
            arc_label = f"{from_id} → {to_id}"
            
            # Create context menu
            menu = Gtk.Menu()
            
            item = Gtk.MenuItem(label=f"Create Sweep from '{arc_label}'")
            item.connect("activate", lambda w: self.on_create_sweep_from_arc(
                w, arc_id, arc_label, current_weight
            ) if self.on_create_sweep_from_arc else None)
            menu.append(item)
            
            menu.show_all()
            menu.popup_at_pointer(event)
            return True
        
        return False
    
    # === SWEEP INDICATORS ===
    
    def update_sweep_indicators(self, swept_param_type, swept_param_id):
        """Update visual indicators showing which parameter is being swept.
        
        Args:
            swept_param_type: 'places', 'transitions', or 'arcs'
            swept_param_id: ID of swept parameter
        """
        # Clear previous indicators
        self.clear_sweep_indicators()
        
        # Determine which store to update
        if swept_param_type == 'places':
            store = self.places_store
            bg_column = 5
        elif swept_param_type == 'transitions':
            store = self.transitions_store
            bg_column = 6
        elif swept_param_type == 'arcs':
            store = self.arcs_store
            bg_column = 5
        else:
            return
        
        # Find and highlight the swept parameter row
        iter = store.get_iter_first()
        while iter:
            param_id = store.get_value(iter, 0)
            if param_id == swept_param_id:
                # Highlight this row with light blue background
                store.set_value(iter, bg_column, "#E3F2FD")
                self.swept_rows[(swept_param_type, swept_param_id)] = iter
                break
            iter = store.iter_next(iter)
    
    def clear_sweep_indicators(self):
        """Clear all sweep indicator highlights."""
        # Clear places
        iter = self.places_store.get_iter_first()
        while iter:
            self.places_store.set_value(iter, 5, "")
            iter = self.places_store.iter_next(iter)
        
        # Clear transitions
        iter = self.transitions_store.get_iter_first()
        while iter:
            self.transitions_store.set_value(iter, 6, "")
            iter = self.transitions_store.iter_next(iter)
        
        # Clear arcs
        iter = self.arcs_store.get_iter_first()
        while iter:
            self.arcs_store.set_value(iter, 5, "")
            iter = self.arcs_store.iter_next(iter)
        
        self.swept_rows.clear()
