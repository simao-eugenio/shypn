#!/usr/bin/env python3
"""Reaction Activity Table widget.

Displays transition (reaction) metrics in a sortable table with 7 columns.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import List


class ReactionActivityTable(Gtk.ScrolledWindow):
    """Table displaying reaction activity metrics.
    
    Columns:
    1. ID (Transition ID)
    2. Reaction Name
    3. Type (Stochastic/Continuous)
    4. Firing Count
    5. Average Rate
    6. Total Flux
    7. Contribution %
    8. Status
    """
    
    def __init__(self):
        """Initialize reaction activity table."""
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        
        # Create tree view with columns
        self.store = Gtk.ListStore(
            str,   # 0: Transition ID
            str,   # 1: Transition Name
            str,   # 2: Type (stochastic/continuous)
            int,   # 3: Firing Count
            float, # 4: Average Rate
            int,   # 5: Total Flux
            float, # 6: Contribution %
            str    # 7: Status
        )
        
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(1)  # Search by reaction name
        self.tree_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        
        # Add columns
        self._setup_columns()
        
        self.add(self.tree_view)
        
    def _setup_columns(self):
        """Create table columns."""
        
        # Column 0: ID
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("ID", renderer, text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        column.set_min_width(60)
        self.tree_view.append_column(column)
        
        # Column 1: Transition Name
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Reaction", renderer, text=1)
        column.set_resizable(True)
        column.set_sort_column_id(1)
        column.set_min_width(150)
        self.tree_view.append_column(column)
        
        # Column 2: Type
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center align
        column = Gtk.TreeViewColumn("Type", renderer, text=2)
        column.set_resizable(True)
        column.set_sort_column_id(2)
        self.tree_view.append_column(column)
        
        # Column 3: Firing Count
        self._add_numeric_column("Firings", 3, "{:,d}")
        
        # Column 4: Average Rate
        self._add_numeric_column("Avg Rate", 4, "{:.4f}")
        
        # Column 5: Total Flux
        self._add_numeric_column("Total Flux", 5, "{:,d}")
        
        # Column 6: Contribution %
        self._add_numeric_column("Contribution %", 6, "{:.2f}")
        
        # Column 7: Status
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center align
        column = Gtk.TreeViewColumn("Status", renderer, text=7)
        column.set_resizable(True)
        column.set_sort_column_id(7)
        self.tree_view.append_column(column)
        
    def _add_numeric_column(self, title: str, column_id: int, format_str: str):
        """Add a numeric column with right alignment.
        
        Args:
            title: Column title
            column_id: Store column index
            format_str: Format string for display
        """
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right align
        
        column = Gtk.TreeViewColumn(title, renderer)
        column.set_cell_data_func(renderer, self._format_cell, 
                                 (column_id, format_str))
        column.set_resizable(True)
        column.set_sort_column_id(column_id)
        self.tree_view.append_column(column)
        
    def _format_cell(self, column, cell, model, iter, user_data):
        """Format cell value.
        
        Args:
            column: TreeViewColumn
            cell: CellRenderer
            model: TreeModel
            iter: TreeIter
            user_data: Tuple of (column_id, format_str)
        """
        column_id, format_str = user_data
        value = model.get_value(iter, column_id)
        
        try:
            cell.set_property("text", format_str.format(value))
        except (ValueError, TypeError):
            cell.set_property("text", str(value))
        
    def populate(self, reaction_metrics: List):
        """Populate table with reaction metrics.
        
        Args:
            reaction_metrics: List of ReactionMetrics instances
        """
        # CRITICAL: Clear BEFORE populating to prevent mixing old and new data
        self.store.clear()
        
        if not reaction_metrics:
            return
        
        for metrics in reaction_metrics:
            self.store.append([
                metrics.transition_id,
                metrics.transition_name,
                metrics.transition_type,
                metrics.firing_count,
                metrics.average_rate,
                metrics.total_flux,
                metrics.contribution,
                metrics.status.value
            ])
        
        # Force update
        self.tree_view.queue_draw()
            
    def clear(self):
        """Clear all table data."""
        self.store.clear()
        
    def export_csv(self) -> str:
        """Export table data as CSV.
        
        Returns:
            CSV string with headers and data
        """
        lines = []
        
        # Header
        lines.append("ID,Reaction,Type,Firings,Avg Rate,Total Flux,Contribution %,Status")
        
        # Data rows
        iter = self.store.get_iter_first()
        while iter:
            values = []
            for i in range(8):  # All columns including ID
                values.append(str(self.store.get_value(iter, i)))
            lines.append(",".join(values))
            iter = self.store.iter_next(iter)
            
        return "\n".join(lines)
