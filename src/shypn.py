#!/usr/bin/env python3
"""GTK4 Main Application Loader.

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
	gi.require_version('Gtk', '4.0')
	from gi.repository import Gtk
except Exception as e:
	print('ERROR: GTK4 (PyGObject) not available:', e, file=sys.stderr)
	sys.exit(1)

# Import panel loaders from src/shypn/helpers/
try:
	from shypn.helpers.left_panel_loader import create_left_panel
	from shypn.helpers.right_panel_loader import create_right_panel
	from shypn.helpers.model_canvas_loader import create_model_canvas
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

		print('✓ Main window loaded')

		# Load model canvas
		try:
			model_canvas_loader = create_model_canvas()
			# Set parent window for zoom palette window
			model_canvas_loader.parent_window = window
		except Exception as e:
			print(f'ERROR: Failed to load model canvas: {e}', file=sys.stderr)
			sys.exit(8)

		# Get main workspace and add canvas
		main_workspace = main_builder.get_object('main_workspace')
		if main_workspace is None:
			print('ERROR: main_workspace not found in main window', file=sys.stderr)
			sys.exit(9)
		
		# Add canvas to workspace
		canvas_container = model_canvas_loader.container
		main_workspace.append(canvas_container)
		print('✓ Model canvas integrated into workspace')

		# Load left panel via its loader
		try:
			left_panel_loader = create_left_panel()
		except Exception as e:
			print(f'ERROR: Failed to load left panel: {e}', file=sys.stderr)
			sys.exit(4)
		
		# Connect new document button to create new tabs
		new_doc_button = left_panel_loader.builder.get_object('new_document_button')
		if new_doc_button:
			def on_new_document(button):
				"""Create a new document tab."""
				model_canvas_loader.add_document()
			new_doc_button.connect('clicked', on_new_document)
			print('✓ New document button connected')
		else:
			print('WARNING: new_document_button not found in left panel')

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

		# Set up callbacks to manage paned position when panels float/attach
		def on_left_float():
			"""Collapse left paned when panel floats."""
			if left_paned:
				try:
					left_paned.set_position(0)
				except Exception as e:
					print(f"Warning: Could not collapse left paned: {e}")
		
		def on_left_attach():
			"""Expand left paned when panel attaches."""
			if left_paned:
				try:
					left_paned.set_position(250)
				except Exception as e:
					print(f"Warning: Could not expand left paned: {e}")
		
		def on_right_float():
			"""Collapse right paned when panel floats."""
			if right_paned:
				try:
					paned_width = right_paned.get_width()
					right_paned.set_position(paned_width)
				except Exception as e:
					print(f"Warning: Could not collapse right paned: {e}")
		
		def on_right_attach():
			"""Expand right paned when panel attaches."""
			if right_paned:
				try:
					paned_width = right_paned.get_width()
					if paned_width > 280:
						right_paned.set_position(paned_width - 280)
				except Exception as e:
					print(f"Warning: Could not expand right paned: {e}")
		
		# Wire up callbacks
		left_panel_loader.on_float_callback = on_left_float
		left_panel_loader.on_attach_callback = on_left_attach
		right_panel_loader.on_float_callback = on_right_float
		right_panel_loader.on_attach_callback = on_right_attach

		# Get toggle button and wire it to attach/detach behavior
		left_toggle = main_builder.get_object('left_panel_toggle')
		right_toggle = main_builder.get_object('right_panel_toggle')
		
		if left_toggle is not None:
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
			
			left_toggle.connect('toggled', on_left_toggle)
			print('✓ Left panel toggle connected for attach/detach')
		else:
			print('WARNING: left_panel_toggle button not found in HeaderBar')

		# Get right toggle button and wire it to attach/detach behavior
		# Get right toggle button and wire it to attach/detach behavior
		if right_toggle is not None:
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
			
			right_toggle.connect('toggled', on_right_toggle)
			print('✓ Right panel toggle connected for attach/detach')
		else:
			print('WARNING: right_panel_toggle button not found in HeaderBar')

		# Set up and present the window
		if isinstance(window, Gtk.ApplicationWindow):
			window.set_application(a)
			window.present()
		else:
			w = Gtk.ApplicationWindow(application=a)
			w.set_child(window)
			w.present()

		print('✓ Attach/detach architecture ready')

	app.connect('activate', on_activate)
	app.run(argv)


if __name__ == '__main__':
	main()
