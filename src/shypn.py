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
		# Load main window
		main_builder = Gtk.Builder.new_from_file(UI_PATH)
		window = main_builder.get_object('main_window')
		if window is None:
			print('ERROR: `main_window` object not found in UI file.', file=sys.stderr)
			sys.exit(3)

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
		
		# Add canvas to workspace
		canvas_container = model_canvas_loader.container
		main_workspace.pack_start(canvas_container, True, True, 0)  # GTK3 uses pack_start

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
			
			print("[Main] File explorer wired to canvas loader and persistency manager")
			print("[Main] File operations now handled by FileExplorerPanel")
			
			# Wire file explorer's open request to load into canvas
			def on_file_open_requested(filepath):
				"""Handle file open request from file explorer (double-click or context menu).
				
				This callback just delegates to FileExplorerPanel which has all the
				file loading logic. This keeps shypn.py as a simple launcher/wiring file.
				
				Args:
					filepath: Full path to the file to open
				"""
				# Delegate to FileExplorerPanel which handles all file loading logic
				file_explorer._open_file_from_path(filepath)
			
			file_explorer.on_file_open_requested = on_file_open_requested

		# Load right panel via its loader
		try:
			right_panel_loader = create_right_panel()
		except Exception as e:
			print(f'ERROR: Failed to load right panel: {e}', file=sys.stderr)
			sys.exit(5)

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

		# Set up and present the window
		if isinstance(window, Gtk.ApplicationWindow):
			window.set_application(a)
			window.present()
		else:
			w = Gtk.ApplicationWindow(application=a)
			w.add(window)  # GTK3 uses add() instead of set_child()
			w.present()

	app.connect('activate', on_activate)
	app.run(argv)


if __name__ == '__main__':
	main()
