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
	
	from gi.repository import Gtk, Gdk
	
	# Initialize Gdk early to avoid initialization issues in imports
	Gdk.init(sys.argv)
except Exception as e:
	print('ERROR: GTK3 (PyGObject) not available:', e, file=sys.stderr)
	sys.exit(1)

# Import panel loaders from src/shypn/helpers/
try:
	from shypn.helpers.left_panel_loader import create_left_panel
	from shypn.helpers.right_panel_loader import create_right_panel
	from shypn.helpers.pathway_panel_loader import create_pathway_panel
	from shypn.helpers.model_canvas_loader import create_model_canvas
	from shypn.file import create_persistency_manager
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
		
		# Load main window
		main_builder = Gtk.Builder.new_from_file(UI_PATH)
		window = main_builder.get_object('main_window')
		if window is None:
			print('ERROR: `main_window` object not found in UI file.', file=sys.stderr)
			sys.exit(3)
		
		# Restore window geometry
		geom = workspace_settings.get_window_geometry()
		window.set_default_size(geom.get('width', 1200), geom.get('height', 800))
		if geom.get('x') is not None and geom.get('y') is not None:
			window.move(geom['x'], geom['y'])
		if geom.get('maximized', False):
			window.maximize()
		
		# WAYLAND FIX: Realize window early to establish window surface
		# This ensures parent window is available for dialogs/menus during initialization
		window.realize()
		
		# Add double-click on header bar to toggle maximize
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
		
		# Create and add status bar at bottom (after canvas)
		status_bar = Gtk.Statusbar()
		status_bar.set_visible(True)
		status_bar.set_margin_start(6)
		status_bar.set_margin_end(6)
		status_bar.set_margin_top(3)
		status_bar.set_margin_bottom(3)
		main_workspace.pack_start(status_bar, False, True, 0)  # Non-expanding, stays at bottom
		
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
			left_panel_loader = create_left_panel()  # Will default to models directory
		except Exception as e:
			print(f'ERROR: Failed to load left panel: {e}', file=sys.stderr)
			sys.exit(4)
		
		# ====================================================================
		# Wire File Explorer to Canvas Loader and Persistency Manager
		# ====================================================================
		
		# Get file explorer instance from left panel
		file_explorer = left_panel_loader.file_explorer
		
		if file_explorer:
			# Wire persistency manager to file explorer for UI updates and file operations
			file_explorer.set_persistency_manager(persistency)
			
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
		
		# Load pathway panel via its loader
		try:
			pathway_panel_loader = create_pathway_panel(model_canvas=model_canvas_loader)
		except Exception as e:
			print(f'WARNING: Failed to load pathway panel: {e}', file=sys.stderr)
			pathway_panel_loader = None
		
		# Wire right panel loader to canvas loader
		# This allows tab switching to update the right panel's data collector
		model_canvas_loader.set_right_panel_loader(right_panel_loader)
		
		# Wire context menu handler to canvas loader
		# This allows right-click context menus to include "Add to Analysis" options
		if hasattr(right_panel_loader, 'context_menu_handler') and right_panel_loader.context_menu_handler:
			model_canvas_loader.set_context_menu_handler(right_panel_loader.context_menu_handler)

		# Get left dock area from main window
		left_dock_area = main_builder.get_object('left_dock_area')
		if left_dock_area is None:
			print('ERROR: left_dock_area not found in main window', file=sys.stderr)
			sys.exit(6)

		# Get right dock area from main window
		right_dock_area = main_builder.get_object('right_dock_area')
		if right_dock_area is None:
			print('ERROR: right_dock_area not found in main window', file=sys.stderr)
			sys.exit(7)

		# Get paned widgets for curtain resize control
		left_paned = main_builder.get_object('left_paned')
		right_paned = main_builder.get_object('right_paned')

		# Get toggle buttons first (needed for callbacks)
		left_toggle = main_builder.get_object('left_panel_toggle')
		right_toggle = main_builder.get_object('right_panel_toggle')
		pathway_toggle = main_builder.get_object('pathway_panel_toggle')

		# WAYLAND FIX: Present window BEFORE defining complex callbacks
		# This ensures the window is fully shown and its Wayland surface is active
		# before GTK tries to process any events that might create child widgets
		if isinstance(window, Gtk.ApplicationWindow):
			window.set_application(a)
			window.show_all()  # Show all widgets
		else:
			w = Gtk.ApplicationWindow(application=a)
			w.add(window)  # GTK3 uses add() instead of set_child()
			window.show_all()  # Show all widgets

		# Define toggle handlers (needed for callbacks to reference)
		def on_left_toggle(button):
			is_active = button.get_active()
			if is_active:
				# Attach to extreme left of main window
				left_panel_loader.attach_to(left_dock_area, parent_window=window)
				# Adjust paned position to show panel (250px default)
				if left_paned:
					try:
						left_paned.set_position(250)
					except Exception:
						pass  # Ignore paned errors
				# If right panel is hidden, ensure its paned is collapsed
				if right_toggle and not right_toggle.get_active() and right_paned:
					try:
						paned_width = right_paned.get_width()
						right_paned.set_position(paned_width)
					except Exception:
						pass  # Ignore paned errors
			else:
				# Detach and hide
				left_panel_loader.hide()
				# Reset paned position to hide panel
				if left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass  # Ignore paned errors

		def on_right_toggle(button):
			is_active = button.get_active()
			if is_active:
				# Hide pathway panel if visible
				if pathway_toggle and pathway_toggle.get_active():
					pathway_toggle.handler_block_by_func(on_pathway_toggle)
					pathway_toggle.set_active(False)
					pathway_toggle.handler_unblock_by_func(on_pathway_toggle)
					if pathway_panel_loader:
						pathway_panel_loader.hide()
				
				# Attach to extreme right of main window
				right_panel_loader.attach_to(right_dock_area, parent_window=window)
				# Adjust paned position to show panel (show last 280px for right panel)
				if right_paned:
					try:
						# Get current paned width and set position to leave space for panel
						paned_width = right_paned.get_width()
						if paned_width > 280:
							right_paned.set_position(paned_width - 280)
					except Exception:
						pass  # Ignore paned errors
				# If left panel is hidden, ensure its paned is collapsed
				if left_toggle and not left_toggle.get_active() and left_paned:
					try:
						left_paned.set_position(0)
					except Exception:
						pass  # Ignore paned errors
			else:
				# Detach and hide
				right_panel_loader.hide()
				# Reset paned position to hide panel (full width)
				if right_paned:
					try:
						paned_width = right_paned.get_width()
						right_paned.set_position(paned_width)
					except Exception:
						pass  # Ignore paned errors

		# Set up callbacks to manage paned position when panels float/attach
		def on_left_float():
			"""Collapse left paned when panel floats."""
			if left_paned:
				try:
					left_paned.set_position(0)
				except Exception:
					pass  # Ignore paned errors
		
		def on_left_attach():
			"""Expand left paned when panel attaches."""
			if left_paned:
				try:
					left_paned.set_position(250)
				except Exception:
					pass  # Ignore paned errors
		
		def on_right_float():
			"""Collapse right paned when panel floats."""
			if right_paned:
				try:
					paned_width = right_paned.get_width()
					right_paned.set_position(paned_width)
				except Exception:
					pass  # Ignore paned errors
			# Sync header toggle button to off when panel floats
			if right_toggle and right_toggle.get_active():
				right_toggle.handler_block_by_func(on_right_toggle)
				right_toggle.set_active(False)
				right_toggle.handler_unblock_by_func(on_right_toggle)
		
		def on_right_attach():
			"""Expand right paned when panel attaches."""
			if right_paned:
				try:
					paned_width = right_paned.get_width()
					if paned_width > 280:
						right_paned.set_position(paned_width - 280)
				except Exception:
					pass  # Ignore paned errors
			# Sync header toggle button to on when panel attaches
			if right_toggle and not right_toggle.get_active():
				right_toggle.handler_block_by_func(on_right_toggle)
				right_toggle.set_active(True)
				right_toggle.handler_unblock_by_func(on_right_toggle)
		
		# Define pathway panel toggle handler (if panel loaded)
		def on_pathway_toggle(button):
			"""Toggle pathway panel docked in right area (mutually exclusive with Analyses)."""
			if not pathway_panel_loader:
				return  # Panel not loaded
			
			is_active = button.get_active()
			if is_active:
				# Hide analyses panel if visible
				if right_toggle and right_toggle.get_active():
					right_toggle.handler_block_by_func(on_right_toggle)
					right_toggle.set_active(False)
					right_toggle.handler_unblock_by_func(on_right_toggle)
					right_panel_loader.hide()
				
				# Attach pathway panel to right dock area
				pathway_panel_loader.attach_to(right_dock_area, parent_window=window)
				# Adjust paned position to show right panel (show last 320px for pathway panel)
				if right_paned:
					try:
						paned_width = right_paned.get_width()
						if paned_width > 320:
							right_paned.set_position(paned_width - 320)
					except Exception:
						pass  # Ignore paned errors
			else:
				# Detach and hide
				pathway_panel_loader.hide()
				# Reset paned position to hide panel (full width)
				if right_paned:
					try:
						paned_width = right_paned.get_width()
						right_paned.set_position(paned_width)
					except Exception:
						pass  # Ignore paned errors
		
		# Wire up callbacks
		left_panel_loader.on_float_callback = on_left_float
		left_panel_loader.on_attach_callback = on_left_attach
		right_panel_loader.on_float_callback = on_right_float
		right_panel_loader.on_attach_callback = on_right_attach

		# Connect toggle buttons to handlers
		if left_toggle is not None:
			left_toggle.connect('toggled', on_left_toggle)

		if right_toggle is not None:
			right_toggle.connect('toggled', on_right_toggle)
		
		if pathway_toggle is not None and pathway_panel_loader:
			pathway_toggle.connect('toggled', on_pathway_toggle)
		
		# Get minimize/maximize buttons
		minimize_button = main_builder.get_object('minimize_button')
		maximize_button = main_builder.get_object('maximize_button')
		maximize_image = main_builder.get_object('maximize_image')
		
		# Define minimize handler
		def on_minimize_clicked(button):
			"""Minimize (iconify) the window."""
			window.iconify()
		
		# Define maximize/restore handler
		def on_maximize_clicked(button):
			"""Toggle between maximized and normal window state."""
			if window.is_maximized():
				window.unmaximize()
				# Update icon to maximize
				if maximize_image:
					maximize_image.set_from_icon_name('window-maximize-symbolic', Gtk.IconSize.BUTTON)
				button.set_tooltip_text('Maximize window')
			else:
				window.maximize()
				# Update icon to restore
				if maximize_image:
					maximize_image.set_from_icon_name('window-restore-symbolic', Gtk.IconSize.BUTTON)
				button.set_tooltip_text('Restore window')
		
		# Connect minimize/maximize buttons
		if minimize_button is not None:
			minimize_button.connect('clicked', on_minimize_clicked)
		
		if maximize_button is not None:
			maximize_button.connect('clicked', on_maximize_clicked)
		
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
		print("\n✋ Application interrupted by user (Ctrl+C)")
		return 0


if __name__ == '__main__':
	try:
		exit_code = main()
		sys.exit(exit_code if exit_code is not None else 0)
	except KeyboardInterrupt:
		print("\n✋ Shutting down gracefully...")
		sys.exit(0)
