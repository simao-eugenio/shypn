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
    1. Reaction Name
    2. Type (Stochastic/Continuous)
    3. Firing Count
    4. Average Rate
    5. Total Flux
    6. Contribution %
    7. Status
    """
    
    def __init__(self):
        """Initialize reaction activity table."""
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        
        # Create tree view with columns
        self.store = Gtk.ListStore(
            str,   # 0: Transition Name
            str,   # 1: Type (stochastic/continuous)
            int,   # 2: Firing Count
            float, # 3: Average Rate
            int,   # 4: Total Flux
            float, # 5: Contribution %
            str    # 6: Status
        )
        
        self.tree_view = Gtk.TreeView(model=self.store)
        self.tree_view.set_enable_search(True)
        self.tree_view.set_search_column(0)
        self.tree_view.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        
        # Add columns
        self._setup_columns()
        
        self.add(self.tree_view)
        
    def _setup_columns(self):
        """Create table columns."""
        
        # Column 0: Transition Name
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Reaction", renderer, text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        column.set_min_width(150)
        self.tree_view.append_column(column)
        
        # Column 1: Type
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center align
        column = Gtk.TreeViewColumn("Type", renderer, text=1)
        column.set_resizable(True)
        column.set_sort_column_id(1)
        self.tree_view.append_column(column)
        
        # Column 2: Firing Count
        self._add_numeric_column("Firings", 2, "{:,d}")
        
        # Column 3: Average Rate
        self._add_numeric_column("Avg Rate", 3, "{:.4f}")
        
        # Column 4: Total Flux
        self._add_numeric_column("Total Flux", 4, "{:,d}")
        
        # Column 5: Contribution %
        self._add_numeric_column("Contribution %", 5, "{:.2f}")
        
        # Column 6: Status
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 0.5)  # Center align
        column = Gtk.TreeViewColumn("Status", renderer, text=6)
        column.set_resizable(True)
        column.set_sort_column_id(6)
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
        self.store.clear()
        
        for metrics in reaction_metrics:
            self.store.append([
                metrics.transition_name,
                metrics.transition_type,
                metrics.firing_count,
                metrics.average_rate,
                metrics.total_flux,
                metrics.contribution,
                metrics.status.value
            ])
            
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
        lines.append("Reaction,Type,Firings,Avg Rate,Total Flux,Contribution %,Status")
        
        # Data rows
        iter = self.store.get_iter_first()
        while iter:
            values = []
            for i in range(7):  # All columns
                values.append(str(self.store.get_value(iter, i)))
            lines.append(",".join(values))
            iter = self.store.iter_next(iter)
            
        return "\n".join(lines)
