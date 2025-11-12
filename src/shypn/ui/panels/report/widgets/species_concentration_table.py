#!/usr/bin/env python3
"""Species Concentration Table widget.

Displays place (species) metrics in a sortable table with 8 columns.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import List


class SpeciesConcentrationTable(Gtk.ScrolledWindow):
    """Table displaying species concentration metrics.
    
    Columns:
    1. Species Name (with color indicator)
    2. Initial Tokens
    3. Final Tokens
    4. Min
    5. Max
    6. Average
    7. Δ (Total Change)
    8. Rate (Δ/time)
    """
    
    def __init__(self):
        """Initialize species concentration table."""
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.set_vexpand(True)
        
        # Create tree view with columns
        self.store = Gtk.ListStore(
            str,   # 0: Place Name
            str,   # 1: Color (hex)
            float, # 2: Initial (changed to float for continuous)
            float, # 3: Final (changed to float for continuous)
            float, # 4: Min (changed to float for continuous)
            float, # 5: Max (changed to float for continuous)
            float, # 6: Average
            float, # 7: Change (Δ) (changed to float for continuous)
            float  # 8: Rate (Δ/time)
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
        
        # Column 0: Species Name with color indicator
        renderer_text = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Species", renderer_text, text=0)
        column.set_resizable(True)
        column.set_sort_column_id(0)
        column.set_min_width(150)
        self.tree_view.append_column(column)
        
        # Column 1: Initial Tokens
        self._add_numeric_column("Initial", 2, float, format_str="{:.2f}")
        
        # Column 2: Final Tokens
        self._add_numeric_column("Final", 3, float, format_str="{:.2f}")
        
        # Column 3: Minimum
        self._add_numeric_column("Min", 4, float, format_str="{:.2f}")
        
        # Column 4: Maximum
        self._add_numeric_column("Max", 5, float, format_str="{:.2f}")
        
        # Column 5: Average
        self._add_numeric_column("Average", 6, float, format_str="{:.2f}")
        
        # Column 6: Total Change
        self._add_numeric_column("Δ", 7, float, format_str="{:+.2f}")
        
        # Column 7: Change Rate
        self._add_numeric_column("Rate (Δ/t)", 8, float, format_str="{:+.4f}")
        
    def _add_numeric_column(self, title: str, column_id: int, 
                           value_type: type, format_str: str = None):
        """Add a numeric column with right alignment.
        
        Args:
            title: Column title
            column_id: Store column index
            value_type: Data type (int or float)
            format_str: Optional format string
        """
        renderer = Gtk.CellRendererText()
        renderer.set_property("xalign", 1.0)  # Right align
        
        column = Gtk.TreeViewColumn(title, renderer)
        
        if format_str:
            column.set_cell_data_func(renderer, self._format_cell, 
                                     (column_id, format_str))
        else:
            column.add_attribute(renderer, "text", column_id)
            
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
        
    def populate(self, species_metrics: List):
        """Populate table with species metrics.
        
        Args:
            species_metrics: List of SpeciesMetrics instances
        """
        # CRITICAL: Clear BEFORE populating to prevent mixing old and new data
        self.store.clear()
        
        if not species_metrics:
            return
        
        for metrics in species_metrics:
            self.store.append([
                metrics.place_name,
                metrics.place_color,
                metrics.initial_tokens,
                metrics.final_tokens,
                metrics.min_tokens,
                metrics.max_tokens,
                metrics.avg_tokens,
                metrics.total_change,
                metrics.change_rate
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
        lines.append("Species,Initial,Final,Min,Max,Average,Change,Rate")
        
        # Data rows
        iter = self.store.get_iter_first()
        while iter:
            values = []
            values.append(self.store.get_value(iter, 0))  # Species name
            for i in range(2, 9):  # Skip color column (1)
                values.append(str(self.store.get_value(iter, i)))
            lines.append(",".join(values))
            iter = self.store.iter_next(iter)
            
        return "\n".join(lines)
