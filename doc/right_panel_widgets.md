# Right Panel Widget Reference

## Overview
The right panel contains analysis tools for Petri net models, organized in expandable sections with tabs for Transitions and Places.

## Widget IDs for Programmatic Access

### Main Structure
- **topological_analyses_expander**: GtkExpander for topological analysis section
- **topological_content**: GtkBox container for topological analysis widgets
- **dynamic_analyses_expander**: GtkExpander for dynamic analysis section
- **internal_dynamic_analyses**: GtkNotebook with Transitions and Places tabs

### Transitions Tab Widgets
- **transitions_page**: Main GtkBox container for the Transitions tab
- **transitions_search_entry**: GtkEntry for search input
- **transitions_search_button**: GtkButton to trigger search
- **transitions_clear_button**: GtkButton to clear search
- **transitions_result_label**: GtkLabel to display search results (format: "Selected: T1, T2, T5")
- **transitions_canvas_container**: GtkBox container for embedding matplotlib canvas

### Places Tab Widgets
- **places_page**: Main GtkBox container for the Places tab
- **places_search_entry**: GtkEntry for search input
- **places_search_button**: GtkButton to trigger search
- **places_clear_button**: GtkButton to clear search
- **places_result_label**: GtkLabel to display search results (format: "Selected: P1, P2, P3")
- **places_canvas_container**: GtkBox container for embedding matplotlib canvas

## Usage Example: Embedding Matplotlib Canvas

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import matplotlib
matplotlib.use('GTK3Agg')
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as FigureCanvas
from matplotlib.figure import Figure

# Get the container from builder
builder = Gtk.Builder()
builder.add_from_file('ui/panels/right_panel.ui')
canvas_container = builder.get_object('transitions_canvas_container')

# Clear placeholder content
for child in canvas_container.get_children():
    canvas_container.remove(child)

# Create matplotlib figure and canvas
fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
canvas = FigureCanvas(fig)
canvas.set_size_request(250, 300)

# Add canvas to container
canvas_container.pack_start(canvas, True, True, 0)
canvas_container.show_all()

# Plot data
ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
ax.set_xlabel('Time')
ax.set_ylabel('Tokens')
ax.set_title('Transition Firing Rate')
canvas.draw()
```

## Usage Example: Search Functionality

```python
def on_transitions_search_clicked(button):
    search_entry = builder.get_object('transitions_search_entry')
    result_label = builder.get_object('transitions_result_label')
    
    query = search_entry.get_text()
    # Perform search logic here
    results = search_transitions(query)  # Returns list like ['T1', 'T2', 'T5']
    
    # Update result label
    result_text = "Selected: " + ", ".join(results) if results else "Selected: "
    result_label.set_text(result_text)

def on_transitions_clear_clicked(button):
    search_entry = builder.get_object('transitions_search_entry')
    result_label = builder.get_object('transitions_result_label')
    
    search_entry.set_text("")
    result_label.set_text("Selected: ")

# Connect signals
search_button = builder.get_object('transitions_search_button')
clear_button = builder.get_object('transitions_clear_button')
search_button.connect('clicked', on_transitions_search_clicked)
clear_button.connect('clicked', on_transitions_clear_clicked)
```

## Layout Structure

```
Right Panel
├── Topologic Analyses (GtkExpander)
│   └── [topological_content container - ready for widgets]
│
└── Dynamic Analyses (GtkExpander)
    └── Notebook (GtkNotebook)
        ├── Transitions Tab
        │   ├── Search Entry + Search Button + Clear Button
        │   ├── Result Label (one line: "Selected: T1, T2, T5")
        │   └── Canvas Container (for matplotlib plots)
        │
        └── Places Tab
            ├── Search Entry + Search Button + Clear Button
            ├── Result Label (one line: "Selected: P1, P2, P3")
            └── Canvas Container (for matplotlib plots)
```

## Notes

- Both canvas containers are expandable (vexpand=True, hexpand=True) to fill available space
- Result labels use ellipsize="end" to handle long lists gracefully
- Result labels are selectable for copy/paste functionality
- Canvas containers have placeholder labels that should be removed before embedding matplotlib
- The matplotlib backend should be set to 'GTK3Agg' for proper integration
