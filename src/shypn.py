#!/usr/bin/env python3
"""GTK3 Main Application Loader.

This script loads the main window and orchestrates panel loading via their
individual loaders. Each panel is responsible for loading its own UI.

Architecture:
- Main loader (this file) loads main_window.ui
- Each panel has its own loader in src/shypn/ (e.g., left_panel_loader.py)
- Panel loaders manage attachable/detachable windows
- HeaderBar toggle buttons control panel attach/detach behavior
- Attached panels appear at extreme left of main window
"""
import os
import sys

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
UI_PATH = os.path.join(REPO_ROOT, 'ui', 'main', 'main_window.ui')

try:
	import gi
	gi.require_version('Gtk', '3.0')
	gi.require_version('Gdk', '3.0')
	
	# Import gi.repository.cairo to register foreign struct converters
	# This fixes "Couldn't find foreign struct converter for 'cairo.Context'" error
	# which occurs in conda environments with pygobject
	try:
		gi.require_version('cairo', '1.0')
		from gi.repository import cairo as _gi_cairo  # noqa: F401
	except (ImportError, ValueError):
		pass  # Cairo integration may not be available
	
	from gi.repository import Gtk, Gdk, GLib
	
	# Initialize Gdk early to avoid initialization issues in imports
	Gdk.init(sys.argv)
	
	# WAYLAND FIX: Suppress Wayland Error 71 protocol messages via environment variable
	# GDK prints these directly to stderr before our log handler can catch them
	# Setting G_MESSAGES_DEBUG to empty suppresses GDK messages at the C level
	import os
	if 'G_MESSAGES_DEBUG' not in os.environ:
		os.environ['G_MESSAGES_DEBUG'] = ''
	
except Exception as e:
	print('ERROR: GTK3 (PyGObject) not available:', e, file=sys.stderr)
	sys.exit(1)

# TEST MODE: Check which file panel to use
USE_SIMPLE_TEST_PANEL = os.environ.get('SHYPN_USE_SIMPLE_PANEL', '0') == '1'
USE_FILE_PANEL_V2 = os.environ.get('SHYPN_USE_FILE_PANEL_V2', '0') == '1'  # Old V2 panel
USE_FILE_PANEL = os.environ.get('SHYPN_USE_FILE_PANEL', '1') == '1'  # Default to modern file panel

# Import panel loaders from src/shypn/helpers/
try:
	if USE_SIMPLE_TEST_PANEL:
		# Simple test panel will be defined later (skip import)
		pass
	elif USE_FILE_PANEL:
		from shypn.helpers.file_panel_loader import create_left_panel
	elif USE_FILE_PANEL_V2:
		from shypn.helpers.file_panel_v3_loader import create_file_panel_v3 as create_left_panel
	else:
		from shypn.helpers.left_panel_loader import create_left_panel
	from shypn.helpers.right_panel_loader import create_right_panel
	from shypn.helpers.pathway_panel_loader import create_pathway_panel
	from shypn.helpers.topology_panel_loader import TopologyPanelLoader
	from shypn.helpers.model_canvas_loader import create_model_canvas
	from shypn.file import create_persistency_manager
	from shypn.ui import MasterPalette
except ImportError as e:
	print(f'ERROR: Cannot import loaders: {e}', file=sys.stderr)
	sys.exit(1)

def main(argv=None):
	if argv is None:
		argv = sys.argv

	# Validate main UI file exists
	if not os.path.exists(UI_PATH):
		print(f'ERROR: Main UI file not found: {UI_PATH}', file=sys.stderr)
		sys.exit(2)

	app = Gtk.Application(application_id='org.shypn.dockdemo')

	def on_activate(a):
		
		# Load workspace settings
		from shypn.workspace_settings import WorkspaceSettings
		workspace_settings = WorkspaceSettings()
		
		# Load CSS for main window styling
		css_path = os.path.join(REPO_ROOT, 'ui', 'main', 'main_window.css')
		if os.path.exists(css_path):
			css_provider = Gtk.CssProvider()
			css_provider.load_from_path(css_path)
			screen = Gdk.Screen.get_default()
			style_context = Gtk.StyleContext()
			style_context.add_provider_for_screen(
				screen,
				css_provider,
				Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
			)
		
		# Load main window
		main_builder = Gtk.Builder.new_from_file(UI_PATH)
		window = main_builder.get_object('main_window')
		if window is None:
			print('ERROR: `main_window` object not found in UI file.', file=sys.stderr)
			sys.exit(3)
		
		# Setup menu actions (File, Edit, View, Help)
		from shypn.ui.menu_actions import MenuActions
		menu_actions = MenuActions(a, window)
		menu_actions.register_all_actions()
		
		# Restore window geometry
		geom = workspace_settings.get_window_geometry()
		window.set_default_size(geom.get('width', 1200), geom.get('height', 800))
		if geom.get('x') is not None and geom.get('y') is not None:
			window.move(geom['x'], geom['y'])
		
		# WAYLAND FIX: Do NOT restore maximized state on startup
		# Maximizing window after panels are loaded causes Error 71 on Wayland
		# Users can manually maximize using window controls without issues
		# Store maximize state to apply AFTER panels are loaded
		# should_maximize = geom.get('maximized', False)
		
		# WAYLAND FIX: Do NOT realize() or maximize() before panels are loaded
		# Early realize() + maximize causes Error 71 on Wayland when panels are added
		# Window will be automatically realized when show_all() is called later
		# window.realize()  # COMMENTED OUT - causes Error 71 on maximized windows
		
		# WAYLAND FIX: Add event mask for multi-monitor support
		# This prevents Error 71 when moving mouse between monitors
		if window.get_window():
			try:
				window.get_window().set_events(
					window.get_window().get_events() | 
					Gdk.EventMask.STRUCTURE_MASK |
					Gdk.EventMask.PROPERTY_CHANGE_MASK
				)
			except Exception:
				pass  # Wayland-specific issue, not critical
		
		# WAYLAND FIX: Monitor change protection
		# Suppress Error 71 when window moves between monitors
		def on_configure_event(widget, event):
			"""Handle window configuration changes (move, resize, monitor switch).
			
			Suppresses Wayland Error 71 by catching exceptions during monitor switches.
			"""
			try:
				# Allow normal processing
				return False
			except Exception as e:
				# Suppress Wayland Error 71 and similar compositor issues
				if "71" in str(e) or "BadWindow" in str(e):
					return True  # Event handled, don't propagate
				return False
		
		window.connect('configure-event', on_configure_event)
		
		# WAYLAND FIX: Screen change protection for monitor hotplug
		def on_screen_changed(widget, old_screen):
			"""Handle screen changes when monitors are added/removed or window moves between monitors."""
			try:
				# Update event mask for new screen
				if widget.get_window():
					widget.get_window().set_events(
						widget.get_window().get_events() | 
						Gdk.EventMask.STRUCTURE_MASK |
						Gdk.EventMask.PROPERTY_CHANGE_MASK
					)
			except Exception:
				pass  # Suppress Wayland errors
			return False
		
		window.connect('screen-changed', on_screen_changed)
		
		# Add double-click on header bar to toggle maximize
		# NOTE: May cause Error 71 on Wayland if panels are visible
		header_bar = main_builder.get_object('header_bar')
		if header_bar:
			def on_header_bar_button_press(widget, event):
				"""Handle double-click on header bar to toggle maximize."""
				if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and event.button == 1:
					if window.is_maximized():
						window.unmaximize()
					else:
						window.maximize()
					return True
				return False
			
			header_bar.connect('button-press-event', on_header_bar_button_press)

		# Load model canvas
		try:
			model_canvas_loader = create_model_canvas()
			# Set parent window for zoom palette window
			model_canvas_loader.parent_window = window
		except Exception as e:
			print(f'ERROR: Failed to load model canvas: {e}', file=sys.stderr)
			sys.exit(8)

		# Create file persistency manager
		try:
			persistency = create_persistency_manager(parent_window=window)
		except Exception as e:
			print(f'ERROR: Failed to create persistency manager: {e}', file=sys.stderr)
			sys.exit(11)
		
		# Wire persistency manager to canvas loader
		# This allows canvas operations (like clear canvas) to reset persistency state
		model_canvas_loader.set_persistency_manager(persistency)
		
		# Get main workspace and add canvas
		main_workspace = main_builder.get_object('main_workspace')
		if main_workspace is None:
			print('ERROR: main_workspace not found in main window', file=sys.stderr)
			sys.exit(9)
		
		# Add canvas to workspace (expands to fill space)
		canvas_container = model_canvas_loader.container
		main_workspace.pack_start(canvas_container, True, True, 0)  # GTK3 uses pack_start
		
		# Get status bar from main_window.ui (now defined in XML)
		status_bar = main_builder.get_object('status_bar')
		if not status_bar:
			# Fallback: create status bar if not in UI file (shouldn't happen)
			status_bar = Gtk.Statusbar()
			status_bar.set_visible(True)
			print("Warning: status_bar not found in UI, creating fallback", file=sys.stderr)
		
		# Initialize status bar context
		status_context_id = status_bar.get_context_id("main")
		
		# Helper function to update status bar
		def update_status(message):
			"""Update the status bar with a message."""
			if status_bar and status_context_id:
				status_bar.pop(status_context_id)
				if message:
					status_bar.push(status_context_id, message)
		
		# Set initial status
		update_status("Ready")
		
		# Wire status bar to canvas loader
		model_canvas_loader.status_bar = status_bar
		model_canvas_loader.status_context_id = status_context_id
		model_canvas_loader.update_status = update_status

		# Load left panel via its loader
		try:
			# Load the panel immediately so file_explorer is initialized
			# We need file_explorer available for wiring callbacks before add_to_stack()
			left_panel_loader = create_left_panel(load_window=True)
		except Exception as e:
			print(f'ERROR: Failed to load left panel: {e}', file=sys.stderr)
			sys.exit(4)
		
		# ====================================================================
		# Wire File Explorer to Canvas Loader and Persistency Manager
		# ====================================================================
		
		# Get file explorer instance from left panel
		file_explorer = left_panel_loader.file_explorer
		
		if file_explorer:
			# WAYLAND FIX: Set parent window IMMEDIATELY so dialogs work even before panel is attached
			# This prevents crashes when user clicks toolbar buttons before toggling panel on
			file_explorer.set_parent_window(window)
			
			# Wire persistency manager to file explorer for UI updates and file operations
			file_explorer.set_persistency_manager(persistency)
			
			# WAYLAND FIX: Also ensure persistency has parent window reference
			if hasattr(file_explorer, 'persistency') and file_explorer.persistency:
				file_explorer.persistency.parent_window = window
			
			# Wire canvas loader to file explorer for document operations
			# This allows file explorer to access canvas managers and their is_default_filename() flag
			file_explorer.set_canvas_loader(model_canvas_loader)
			
			# Wire file explorer's open request to load into canvas
			def on_file_open_requested(filepath):
				"""Handle file open request from file explorer (double-click or context menu).
				
				This callback just delegates to FileExplorerPanel which has all the
				file loading logic. This keeps shypn.py as a simple launcher/wiring file.
				
				Args:
					filepath: Full path to the file to open
				"""
				update_status(f"Opening {os.path.basename(filepath)}...")
				# Delegate to FileExplorerPanel which handles all file loading logic
				file_explorer._open_file_from_path(filepath)
				update_status(f"Opened {os.path.basename(filepath)}")
			
			file_explorer.on_file_open_requested = on_file_open_requested

		# Load right panel via its loader
		try:
			right_panel_loader = create_right_panel()
		except Exception as e:
			print(f'ERROR: Failed to load right panel: {e}', file=sys.stderr)
			sys.exit(5)
		
		# Load topology panel FIRST (needed by pathway panel wiring)
		try:
			# Topology panel doesn't need model at init - will get it at analysis time
			topology_panel_loader = TopologyPanelLoader(model=None)
			# Wire model_canvas_loader so topology can access current model
			if hasattr(topology_panel_loader, 'controller') and topology_panel_loader.controller:
				# Use the proper method to set model_canvas_loader
				topology_panel_loader.set_model_canvas_loader(model_canvas_loader)
				
				# ===================================================================
				# WIRE TOPOLOGY PANEL TO MODEL LIFECYCLE EVENTS
				# This ensures cache is invalidated when models change/switch
				# ===================================================================
				
				# Event 1: Tab Switching (user creates multiple models and switches)
				# Connect to notebook's page-changed signal
				def on_canvas_tab_switched(notebook, page, page_num):
					"""Called when user switches to different model tab."""
					drawing_area = model_canvas_loader.get_current_document()
					if drawing_area and topology_panel_loader.controller:
						topology_panel_loader.controller.on_tab_switched(drawing_area)
				
				if model_canvas_loader.notebook:
					model_canvas_loader.notebook.connect('switch-page', on_canvas_tab_switched)
				
				# Event 2: File Operations (user opens .shy file)
				# Wire to file explorer's open callback
				if file_explorer:
					original_on_file_open = file_explorer.on_file_open_requested
					
					def on_file_open_with_topology_notify(filepath):
						"""Wrapper that notifies topology panel after file opens."""
						# Call original file open handler
						if original_on_file_open:
							original_on_file_open(filepath)
						
						# Notify topology panel that model changed
						drawing_area = model_canvas_loader.get_current_document()
						if drawing_area and topology_panel_loader.controller:
							topology_panel_loader.controller.on_file_opened(drawing_area)
					
					file_explorer.on_file_open_requested = on_file_open_with_topology_notify
				
				# Event 3: Pathway Import (KEGG/SBML import)
				# Will be wired after pathway_panel_loader is created (see below)
				
		except Exception as e:
			print(f'WARNING: Failed to load topology panel: {e}', file=sys.stderr)
			topology_panel_loader = None
		
		# Load pathway panel via its loader
		try:
			pathway_panel_loader = create_pathway_panel(
				model_canvas=model_canvas_loader,
				workspace_settings=workspace_settings
			)
			
			# WAYLAND FIX: Set parent window for SBML Import panel immediately
			# This ensures FileChooserDialog has valid parent before panel is attached
			if pathway_panel_loader and hasattr(pathway_panel_loader, 'sbml_import_controller'):
				if pathway_panel_loader.sbml_import_controller:
					pathway_panel_loader.sbml_import_controller.set_parent_window(window)
			
			# Wire topology panel to pathway import events (if both panels loaded)
			if topology_panel_loader and topology_panel_loader.controller and pathway_panel_loader:
				# KEGG Import: Wrap import completion callback to notify topology
				# DISABLED: Topology notification can trigger expensive calculations
				pass
				# if hasattr(pathway_panel_loader, 'kegg_import_controller') and pathway_panel_loader.kegg_import_controller:
				# 	kegg_ctrl = pathway_panel_loader.kegg_import_controller
				# 	original_kegg_complete = kegg_ctrl._on_import_complete
				# 	
				# 	def kegg_import_with_topology_notify(document_model):
				# 		"""Wrapper for KEGG import completion that notifies topology panel."""
				# 		# Run original completion handler
				# 		result = original_kegg_complete(document_model)
				# 		
				# 		# Notify topology that model was imported (with error handling)
				# 		try:
				# 			drawing_area = model_canvas_loader.get_current_document()
				# 			if drawing_area and topology_panel_loader and topology_panel_loader.controller:
				# 				topology_panel_loader.controller.on_pathway_imported(drawing_area)
				# 		except Exception as e:
				# 			print(f"[KEGG] Warning: Failed to notify topology panel: {e}", file=sys.stderr)
				# 			import traceback
				# 			traceback.print_exc()
				# 		
				# 		return result
				# 	
				# 	kegg_ctrl._on_import_complete = kegg_import_with_topology_notify
				
				# SBML Import: Wrap load completion callback to notify topology
				# DISABLED: Topology notification can trigger expensive calculations
				# if hasattr(pathway_panel_loader, 'sbml_import_controller') and pathway_panel_loader.sbml_import_controller:
				# 	sbml_ctrl = pathway_panel_loader.sbml_import_controller
				# 	original_sbml_complete = sbml_ctrl._on_load_complete
				# 	
				# 	def sbml_load_with_topology_notify(document_model, pathway_name):
				# 		"""Wrapper for SBML load completion that notifies topology panel."""
				# 		# Run original completion handler
				# 		result = original_sbml_complete(document_model, pathway_name)
				# 		
				# 		# Notify topology that model was imported (with error handling)
				# 		try:
				# 			drawing_area = model_canvas_loader.get_current_document()
				# 			if drawing_area and topology_panel_loader and topology_panel_loader.controller:
				# 				topology_panel_loader.controller.on_pathway_imported(drawing_area)
				# 		except Exception as e:
				# 			print(f"[SBML] Warning: Failed to notify topology panel: {e}", file=sys.stderr)
				# 			import traceback
				# 			traceback.print_exc()
				# 		
				# 		return result
				# 	
				# 	sbml_ctrl._on_load_complete = sbml_load_with_topology_notify
				
		except Exception as e:
			print(f'WARNING: Failed to load pathway panel: {e}', file=sys.stderr)
			pathway_panel_loader = None
			topology_panel_loader = None
		
		# Wire pathway panel loader to file panel for project synchronization
		# This ensures pathway import controllers get updated when project is opened
		if pathway_panel_loader and left_panel_loader:
			left_panel_loader.set_pathway_panel_loader(pathway_panel_loader)
		
		# Wire model canvas loader to file panel for project synchronization
		# This ensures all canvas managers save to correct project directories
		if model_canvas_loader and left_panel_loader:
			left_panel_loader.set_model_canvas_loader(model_canvas_loader)
		
		# Wire right panel loader to canvas loader
		# This allows tab switching to update the right panel's data collector
		model_canvas_loader.set_right_panel_loader(right_panel_loader)
		
		# IMPORTANT: Wire data_collector for any EXISTING canvases (e.g., startup default canvas)
		# The startup canvas is created before right_panel_loader exists, so we need to
		# wire it retroactively here after both components are initialized
		try:
			model_canvas_loader.wire_existing_canvases_to_right_panel()
		except Exception as e:
			import traceback
			print(f"[SHYPN ERROR] Exception in wire_existing_canvases_to_right_panel(): {e}", file=sys.stderr)
			traceback.print_exc()
		
		# Wire context menu handler to canvas loader
		# This allows right-click context menus to include "Add to Analysis" options
		if hasattr(right_panel_loader, 'context_menu_handler') and right_panel_loader.context_menu_handler:
			model_canvas_loader.set_context_menu_handler(right_panel_loader.context_menu_handler)
			
			# Wire pathway operations panel to context menu handler for BRENDA enrichment
			if pathway_panel_loader and hasattr(pathway_panel_loader, 'panel'):
				right_panel_loader.context_menu_handler.set_pathway_operations_panel(pathway_panel_loader.panel)
		
		# Wire file explorer panel to canvas loader
		# This allows keyboard shortcuts (Ctrl+S, Ctrl+Shift+S) to trigger save operations
		if file_explorer:
			model_canvas_loader.set_file_explorer_panel(file_explorer)
			# Wire file explorer panel to menu actions for File menu operations
			menu_actions.set_file_explorer_panel(file_explorer)

		# Get the GtkStack that contains all panel containers
		left_dock_stack = main_builder.get_object('left_dock_stack')
		if left_dock_stack is None:
			print('ERROR: left_dock_stack not found in main window', file=sys.stderr)
			sys.exit(6)

		# Get individual panel containers from the stack
		files_panel_container = main_builder.get_object('files_panel_container')
		analyses_panel_container = main_builder.get_object('analyses_panel_container')
		pathways_panel_container = main_builder.get_object('pathways_panel_container')
		topology_panel_container = main_builder.get_object('topology_panel_container')
		report_panel_container = main_builder.get_object('report_panel_container')

		# Get paned widget for curtain resize control
		left_paned = main_builder.get_object('left_paned')

		# ====================================================================
		# WAYLAND FIX: Show main window FIRST, then add panels
		# Following skeleton test pattern: window.show_all() before panel operations
		# ====================================================================
		
		# CRITICAL: Hide panel containers BEFORE window.show_all()
		# This prevents them from being shown when show_all() is called
		if files_panel_container:
			files_panel_container.set_visible(False)
			files_panel_container.set_no_show_all(False)
		if analyses_panel_container:
			analyses_panel_container.set_visible(False)
			analyses_panel_container.set_no_show_all(False)
		if pathways_panel_container:
			pathways_panel_container.set_visible(False)
			pathways_panel_container.set_no_show_all(False)
		if topology_panel_container:
			topology_panel_container.set_visible(False)
			topology_panel_container.set_no_show_all(False)
		
		# Collapse left_paned to 0 width
		if left_paned:
			left_paned.set_position(0)
		
		# ====================================================================
		# Create Master Palette (vertical toolbar on far left)
		# WAYLAND FIX: Must be created and inserted BEFORE window.show_all()
		# ====================================================================
		master_palette = MasterPalette()
		
		# Get palette slot and insert palette BEFORE showing main window
		master_palette_slot = main_builder.get_object('master_palette_slot')
		if master_palette_slot:
			# Clear any existing children (shouldn't be any)
			for child in master_palette_slot.get_children():
				master_palette_slot.remove(child)
			# Add palette widget
			palette_widget = master_palette.get_widget()
			master_palette_slot.pack_start(palette_widget, True, True, 0)
		else:
			print("ERROR: master_palette_slot not found in UI", file=sys.stderr)
			sys.exit(20)
		
		# WAYLAND FIX: Present window AFTER all widgets are added
		# This ensures everything is in place before window realization
		if isinstance(window, Gtk.ApplicationWindow):
			window.set_application(a)
			window.show_all()  # Show all widgets including MasterPalette
		else:
			w = Gtk.ApplicationWindow(application=a)
			w.add(window)  # GTK3 uses add() instead of set_child()
			window.show_all()  # Show all widgets including MasterPalette
		
		# CRITICAL: Hide panels AFTER window.show_all()
		# show_all() reveals everything, so we must explicitly hide panels that start hidden
		
		# Make sure left_dock_stack and left_paned are visible
		if left_dock_stack:
			left_dock_stack.set_visible(True)
			left_dock_stack.set_no_show_all(False)  # Allow children to be shown later
		
		if left_paned:
			left_paned.set_visible(True)
			left_paned.set_position(0)  # Collapse to hide all panels
		
		# Hide all panel containers (but they can be shown later)
		if files_panel_container:
			files_panel_container.set_visible(False)
			files_panel_container.set_no_show_all(False)
		if analyses_panel_container:
			analyses_panel_container.set_visible(False)
			analyses_panel_container.set_no_show_all(False)
		if pathways_panel_container:
			pathways_panel_container.set_visible(False)
			pathways_panel_container.set_no_show_all(False)
		if topology_panel_container:
			topology_panel_container.set_visible(False)
			topology_panel_container.set_no_show_all(False)
		if report_panel_container:
			report_panel_container.set_visible(False)
			report_panel_container.set_no_show_all(False)
		
		# ====================================================================
		# NOW add panels to GtkStack AFTER window is shown
		# Following skeleton test pattern for Wayland safety
		# WAYLAND FIX: Panels load content directly without creating windows
		# ====================================================================
		
		# Add Files panel to stack
		if left_panel_loader:
			left_panel_loader.add_to_stack(left_dock_stack, files_panel_container, 'files')
		
		# Add Pathways panel to stack
		if pathway_panel_loader:
			pathway_panel_loader.add_to_stack(left_dock_stack, pathways_panel_container, 'pathways')
		
		# Add Analyses panel to stack
		if right_panel_loader:
			right_panel_loader.add_to_stack(left_dock_stack, analyses_panel_container, 'analyses')
		
		# Add Topology panel to stack
		if topology_panel_loader:
			topology_panel_loader.add_to_stack(left_dock_stack, topology_panel_container, 'topology')
		
		# ====================================================================
		# Create and Add Report Panel to stack
		# ====================================================================
		try:
			from shypn.ui.panels.report import ReportPanel
			report_panel = ReportPanel(project=None, model_canvas=model_canvas_loader)
			
			# Wire topology panel to report panel for analysis summary
			# The loader has a .panel attribute which is the actual TopologyPanel
			if topology_panel_loader and hasattr(topology_panel_loader, 'panel'):
				report_panel.set_topology_panel(topology_panel_loader.panel)
			
			# Wire dynamic analyses panel to report panel for real-time data
			if right_panel_loader and hasattr(right_panel_loader, 'dynamic_analyses_panel'):
				report_panel.set_dynamic_analyses_panel(right_panel_loader.dynamic_analyses_panel)
			
			# Wire pathway operations panel to report panel for pathway data
			if pathway_panel_loader and hasattr(pathway_panel_loader, 'panel'):
				report_panel.set_pathway_operations_panel(pathway_panel_loader.panel)
			
			report_panel_container.pack_start(report_panel, True, True, 0)
			report_panel.show_all()
		except Exception as e:
			print(f"[SHYPN ERROR] Failed to load Report Panel: {e}", file=sys.stderr)
			import traceback
			traceback.print_exc()

		# ====================================================================
		# WAYLAND FIX: Do NOT auto-maximize on startup
		# Programmatic maximize after panel loading causes Error 71 on Wayland
		# Users can manually maximize using window controls
		# ====================================================================
		# if should_maximize:
		# 	from gi.repository import GLib
		# 	def do_delayed_maximize():
		# 		window.maximize()
		# 		return False  # Don't repeat
		# 	# Defer maximize to give GTK time to settle the widget hierarchy
		# 	GLib.idle_add(do_delayed_maximize)

		# ====================================================================
		# Set parent windows for dialogs (AFTER window.show_all())
		# ====================================================================
		if left_panel_loader:
			left_panel_loader.parent_window = window
			# Also set for file_explorer and persistency if using File Panel V3
			if hasattr(left_panel_loader, 'file_explorer') and left_panel_loader.file_explorer:
				left_panel_loader.file_explorer.parent_window = window
				if hasattr(left_panel_loader.file_explorer, 'persistency') and left_panel_loader.file_explorer.persistency:
					left_panel_loader.file_explorer.persistency.parent_window = window
		
		if right_panel_loader:
			right_panel_loader.parent_window = window
		
		if pathway_panel_loader:
			pathway_panel_loader.parent_window = window
		
		if topology_panel_loader:
			topology_panel_loader.parent_window = window

		# Define toggle handlers (show/hide panel windows as transient windows)
		# ====================================================================
		# Skeleton Pattern: Master Palette toggle handlers
		# Use show_in_stack() / hide_in_stack() to control panel visibility
		# ====================================================================
		
		def on_left_toggle(is_active):
			"""Handle Files panel toggle from Master Palette.
			
			EXCLUSIVE MODE: Only one panel active at a time.
			When button is activated, deactivate others.
			"""
			if not left_panel_loader:
				return
			
			if is_active:
				# Deactivate other panels (exclusive mode)
				master_palette.set_active('pathways', False)
				master_palette.set_active('analyses', False)
				master_palette.set_active('topology', False)
				master_palette.set_active('report', False)
				
				# Show this panel (in stack if hanged, or floating if detached)
				left_panel_loader.show_in_stack()
				# Expand left paned to show stack only if panel is hanged
				if left_panel_loader.is_hanged and left_paned:
					try:
						left_paned.set_position(250)
					except Exception:
						pass
			else:
				left_panel_loader.hide_in_stack()
				# Hide stack when last panel is hidden
				if left_dock_stack:
					left_dock_stack.set_visible(False)
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass

		def on_right_toggle(is_active):
			"""Handle Analyses panel toggle from Master Palette.
			
			EXCLUSIVE MODE: Only one panel active at a time.
			When button is activated, deactivate others.
			"""
			if not right_panel_loader:
				return
			
			if is_active:
				# Deactivate other panels (exclusive mode)
				master_palette.set_active('files', False)
				master_palette.set_active('pathways', False)
				master_palette.set_active('topology', False)
				master_palette.set_active('report', False)
				
				# Show this panel (in stack if hanged, or floating if detached)
				right_panel_loader.show_in_stack()
				# Expand left paned to show stack only if panel is hanged
				if right_panel_loader.is_hanged and left_paned:
					try:
						left_paned.set_position(280)
					except Exception:
						pass
			else:
				right_panel_loader.hide_in_stack()
				# Hide stack when last panel is hidden
				if left_dock_stack:
					left_dock_stack.set_visible(False)
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass

		def on_pathway_toggle(is_active):
			"""Handle Pathways panel toggle from Master Palette.
			
			EXCLUSIVE MODE: Only one panel active at a time.
			When button is activated, deactivate others.
			"""
			if not pathway_panel_loader:
				return
			
			if is_active:
				# Deactivate other panels (exclusive mode)
				master_palette.set_active('files', False)
				master_palette.set_active('analyses', False)
				master_palette.set_active('topology', False)
				master_palette.set_active('report', False)
				
				# Show this panel (in stack if hanged, or floating if detached)
				pathway_panel_loader.show_in_stack()
				# Expand left paned to show stack only if panel is hanged
				if pathway_panel_loader.is_hanged and left_paned:
					try:
						left_paned.set_position(270)
					except Exception:
						pass
			else:
				pathway_panel_loader.hide_in_stack()
				# Hide stack when last panel is hidden
				if left_dock_stack:
					left_dock_stack.set_visible(False)
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass

		def on_topology_toggle(is_active):
			"""Handle Topology panel toggle from Master Palette.
			
			EXCLUSIVE MODE: Only one panel active at a time.
			When button is activated, deactivate others.
			"""
			if not topology_panel_loader:
				return
			
			if is_active:
				# Deactivate other panels (exclusive mode)
				master_palette.set_active('files', False)
				master_palette.set_active('pathways', False)
				master_palette.set_active('analyses', False)
				master_palette.set_active('report', False)
				
				# Show this panel (in stack if hanged, or floating if detached)
				topology_panel_loader.show_in_stack()
				# Expand left paned to show stack only if panel is hanged
				if topology_panel_loader.is_hanged and left_paned:
					try:
						left_paned.set_position(320)  # Match Report panel width
					except Exception:
						pass
			else:
				topology_panel_loader.hide_in_stack()
				# Hide stack when last panel is hidden
				if left_dock_stack:
					left_dock_stack.set_visible(False)
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass

		def on_report_toggle(is_active):
			"""Handle Report panel toggle from Master Palette.
			
			EXCLUSIVE MODE: Only one panel active at a time.
			When button is activated, deactivate others.
			"""
			if not report_panel_container:
				return
			
			if is_active:
				# Deactivate other panels (exclusive mode)
				master_palette.set_active('files', False)
				master_palette.set_active('pathways', False)
				master_palette.set_active('analyses', False)
				master_palette.set_active('topology', False)
				
				# Show report panel in stack
				if left_dock_stack:
					left_dock_stack.set_visible_child_name('report')
					left_dock_stack.set_visible(True)
				# Expand left paned to show report panel
				if left_paned:
					try:
						left_paned.set_position(320)
					except Exception:
						pass
				# Show report container
				if report_panel_container:
					report_panel_container.set_visible(True)
			else:
				# Hide report panel
				if report_panel_container:
					report_panel_container.set_visible(False)
				# Hide stack when last panel is hidden
				if left_dock_stack:
					left_dock_stack.set_visible(False)
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass

		# Set up callbacks to manage paned position when panels float/attach (detach button)
		def on_left_float():
			"""Collapse left paned when Files panel floats."""
			if left_paned:
				try:
					left_paned.set_position(0)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks
		
		def on_left_attach():
			"""Expand left paned when Files panel attaches."""
			if left_paned:
				try:
					left_paned.set_position(250)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks
		
		def on_right_float():
			"""Collapse left paned when Analyses panel floats (now docks LEFT)."""
			if left_paned:
				try:
					left_paned.set_position(0)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks
		
		def on_right_attach():
			"""Expand left paned when Analyses panel attaches (now docks LEFT)."""
			if left_paned:
				try:
					left_paned.set_position(280)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: DO NOT call master_palette.set_active() here - creates circular callbacks
		
		# Define float/attach callbacks for topology panel
		def on_topology_float():
			"""Collapse left paned when Topology panel floats."""
			if left_paned:
				try:
					left_paned.set_position(0)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks
		
		def on_topology_attach():
			"""Expand left paned when Topology panel attaches."""
			if left_paned:
				try:
					left_paned.set_position(400)
				except Exception:
					pass  # Ignore paned errors
			# NOTE: Do NOT call master_palette.set_active() here - creates circular callbacks
		
		# Wire up callbacks
		left_panel_loader.on_float_callback = on_left_float
		left_panel_loader.on_attach_callback = on_left_attach
		right_panel_loader.on_float_callback = on_right_float
		right_panel_loader.on_attach_callback = on_right_attach
		if topology_panel_loader:
			topology_panel_loader.on_float_callback = on_topology_float
			topology_panel_loader.on_attach_callback = on_topology_attach

		# ====================================================================
		# Wire Master Palette buttons to toggle handlers
		# ====================================================================
		# Connect palette buttons directly to toggle handlers
		master_palette.connect('files', on_left_toggle)
		master_palette.connect('pathways', on_pathway_toggle)
		master_palette.connect('analyses', on_right_toggle)
		master_palette.connect('topology', on_topology_toggle)
		master_palette.connect('report', on_report_toggle)
		
		# Enable topology button if panel loaded successfully
		if topology_panel_loader:
			master_palette.set_sensitive('topology', True)
			# Update tooltip to remove "Coming Soon"
			if 'topology' in master_palette.buttons:
				master_palette.buttons['topology'].widget.set_tooltip_text('Topology Analysis')
		
		# Both maximize and minimize buttons removed for Wayland compatibility
		# Users can:
		# - Double-click title bar to maximize/restore
		# - Use window manager controls to minimize
		
		# Save window geometry on close and check for unsaved changes
		def on_window_delete(window, event):
			"""Handle window close event.
			
			1. Check for unsaved changes in all open document tabs
			2. Prompt user to save if needed for each dirty document
			3. Save window geometry if closing is allowed
			
			Returns:
				bool: True to prevent closing, False to allow closing
			"""
			# Check for unsaved changes in all tabs
			if model_canvas_loader and hasattr(model_canvas_loader, 'notebook'):
				notebook = model_canvas_loader.notebook
				num_pages = notebook.get_n_pages()
				
				# Check each tab for unsaved changes
				for page_num in range(num_pages):
					# Switch to this tab to make it active (so persistency tracks the right document)
					notebook.set_current_page(page_num)
					
					# Use the canvas loader's existing check logic
					# This will prompt the user for each dirty document
					if persistency and persistency.is_dirty:
						# Prompt user about unsaved changes
						# Defensive check for parent window (Wayland compatibility)
						parent = window if window else None
						dialog = Gtk.MessageDialog(
							parent=parent,
							modal=True,
							message_type=Gtk.MessageType.WARNING,
							buttons=Gtk.ButtonsType.NONE,
							text='Unsaved changes'
						)
						dialog.set_keep_above(True)  # Ensure dialog stays on top
						dialog.format_secondary_text(
							f"Document '{persistency.get_display_name()}' has unsaved changes.\n"
							"Do you want to save before closing?"
						)
						dialog.add_button('Cancel', Gtk.ResponseType.CANCEL)
						dialog.add_button('Close Without Saving', Gtk.ResponseType.NO)
						dialog.add_button('Save', Gtk.ResponseType.YES)
						dialog.set_default_response(Gtk.ResponseType.YES)
						
						response = dialog.run()
						dialog.destroy()
						
						if response == Gtk.ResponseType.YES:
							# Get the current page and its manager
							page_widget = notebook.get_nth_page(page_num)
							drawing_area = None
							if isinstance(page_widget, Gtk.Overlay):
								scrolled = page_widget.get_child()
								if isinstance(scrolled, Gtk.ScrolledWindow):
									drawing_area = scrolled.get_child()
									if hasattr(drawing_area, 'get_child'):
										drawing_area = drawing_area.get_child()
							
							if drawing_area and drawing_area in model_canvas_loader.canvas_managers:
								manager = model_canvas_loader.canvas_managers[drawing_area]
								document = manager.to_document_model() if hasattr(manager, 'to_document_model') else None
								
								if document:
									# Check if it's using default filename
									is_default_filename = getattr(manager, '_is_default_filename', False)
									
									# Attempt to save
									success = persistency.save_document(
										document,
										save_as=False,
										is_default_filename=is_default_filename
									)
									if not success:
										# Save failed or was cancelled - prevent closing
										return True
						elif response == Gtk.ResponseType.CANCEL:
							# User cancelled - prevent closing
							return True
						# else: response == NO, discard changes for this document and continue
			
			# No unsaved changes or user chose to discard/save all - save window geometry
			width, height = window.get_size()
			x, y = window.get_position()
			maximized = window.is_maximized()
			workspace_settings.set_window_geometry(width, height, x, y, maximized)
			
			return False  # Allow window to close
		
		window.connect('delete-event', on_window_delete)

		# Window already presented earlier (before toggle handlers)
		# This was moved up to fix Wayland initialization timing

	app.connect('activate', on_activate)
	
	try:
		return app.run(argv)
	except KeyboardInterrupt:
		return 0


if __name__ == '__main__':
	try:
		exit_code = main()
		sys.exit(exit_code if exit_code is not None else 0)
	except KeyboardInterrupt:
		sys.exit(0)
