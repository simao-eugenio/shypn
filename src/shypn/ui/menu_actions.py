"""Menu action handlers for File, Edit, View, Help menus.

This module contains all the action handlers for the main menu bar.
Keeping menu logic separate from the main loader maintains clean architecture.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio


class MenuActions:
	"""Centralized menu action handlers for the application."""
	
	def __init__(self, app, window):
		"""Initialize menu actions.
		
		Args:
			app: The Gtk.Application instance
			window: The main application window
		"""
		self.app = app
		self.window = window
		self.persistency = None  # Set later if needed
		self.model_canvas_loader = None  # Set later if needed
		self.file_explorer_panel = None  # Set later if needed
		self._clipboard: list = []  # Serialized {type, data} dicts for cut/copy/paste
		
	def set_persistency(self, persistency):
		"""Set the persistency manager for file operations."""
		self.persistency = persistency
	
	def set_canvas_loader(self, canvas_loader):
		"""Set the canvas loader for view operations."""
		self.model_canvas_loader = canvas_loader
	
	def set_file_explorer_panel(self, file_explorer_panel):
		"""Set the file explorer panel for file operations."""
		self.file_explorer_panel = file_explorer_panel

	
	# ====================================================================
	# File Menu Actions
	# ====================================================================
	
	def on_file_new(self, action, param):
		"""Create a new file/model."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.new_document()
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("New Document Error", f"Failed to create new document: {e}")
	
	def on_file_open(self, action, param):
		"""Open an existing file."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.open_document()
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("Open Document Error", f"Failed to open document: {e}")
	
	def on_file_save(self, action, param):
		"""Save the current file."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.save_current_document()
			else:

				self._show_error_dialog("Save Error", "File explorer panel not initialized")
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("Save Document Error", f"Failed to save document: {e}")
	
	def on_file_save_as(self, action, param):
		"""Save the current file with a new name."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.save_current_document_as()
			else:

				self._show_error_dialog("Save As Error", "File explorer panel not initialized")
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("Save As Error", f"Failed to save document: {e}")
	
	def on_file_export_pdf(self, action, param):
		"""Export current model to PDF."""
		try:
			if not self.model_canvas_loader:
				self._show_error_dialog("Export Error", "No canvas available")
				return
			
			# Get current document
			drawing_area = self.model_canvas_loader.get_current_document()
			if not drawing_area:
				self._show_info_dialog("Export to PDF", "No model is currently open.")
				return
			
			# Get canvas manager
			manager = self.model_canvas_loader.get_canvas_manager(drawing_area)
			if not manager:
				self._show_error_dialog("Export Error", "Failed to access model data")
				return
			
			# Import exporter (lazy import to avoid circular dependencies)
			from shypn.export import PDFExporter, ExportError
			
			# Create exporter with Wayland-safe parent window
			exporter = PDFExporter(parent_window=self.window)
			
			# Show file dialog
			default_filename = manager.filename if manager.filename != "default" else "model"
			filepath = exporter.show_file_dialog(default_filename=default_filename)
			
			if filepath:
				# Perform export
				success = exporter.export(manager, filepath)
				
				if success:
					import os
					self._show_info_dialog("Export Successful", 
						f"Model exported to:\n{os.path.basename(filepath)}")
				
		except ExportError as e:
			self._show_error_dialog("Export Failed", str(e))
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("Export PDF Error", f"Failed to export: {e}")
	
	def on_file_reset_canvas(self, action, param):
		"""Reset the current canvas (clear all elements, restart IDs).
		
		PHASE 5: Canvas lifecycle - reset current canvas to initial state.
		Clears all places, transitions, arcs and resets ID sequence to P1, T1, A1.
		Shows confirmation dialog before resetting.
		"""
		try:
			if not self.model_canvas_loader:
				return
			
			# Get current canvas info
			info = self.model_canvas_loader.get_current_canvas_info()
			if not info:
				self._show_info_dialog("No Canvas", "No canvas is currently open.")
				return
			
			# Show confirmation dialog
			dialog = Gtk.MessageDialog(
				transient_for=self.window,
				flags=0,
				message_type=Gtk.MessageType.WARNING,
				buttons=Gtk.ButtonsType.YES_NO,
				text="Reset Current Canvas?"
			)
			dialog.format_secondary_text(
				f"This will clear all elements in the current canvas and reset IDs.\n\n"
				f"Canvas: {info.get('scope_name', 'Unknown')}\n"
				f"Elements: {info.get('element_count', 0)} (places, transitions, arcs)\n\n"
				f"This action cannot be undone. Continue?"
			)
			
			response = dialog.run()
			dialog.destroy()
			
			if response == Gtk.ResponseType.YES:
				# Reset the canvas
				success = self.model_canvas_loader.reset_current_canvas()
				if success:
					self._show_info_dialog("Canvas Reset", "Canvas has been reset successfully.")
				else:
					self._show_error_dialog("Reset Failed", "Failed to reset canvas.")
					
		except Exception as e:
			import traceback
			traceback.print_exc()
			self._show_error_dialog("Reset Canvas Error", f"Failed to reset canvas: {e}")
	
	def on_file_quit(self, action, param):
		"""Quit the application."""
		self.app.quit()
	
	# ====================================================================
	# Edit Menu Actions
	# ====================================================================
	
	def on_edit_undo(self, action, param):
		"""Undo the last action for the active document."""
		try:
			if not self.model_canvas_loader:
				return
			da = self.model_canvas_loader.get_current_document()
			if not da:
				return
			manager = self.model_canvas_loader.get_canvas_manager(da)
			if manager and hasattr(manager, 'undo_manager') and manager.undo_manager:
				if manager.undo_manager.undo(manager):
					try:
						da.queue_draw()
					except (TypeError, AttributeError) as e:
						from shypn.utils.logging import get_logger
						logger = get_logger(__name__)
						logger.debug(f"Failed to queue draw after undo: {e}")
		except (AttributeError, TypeError) as e:
			# Keep menu action resilient
			from shypn.utils.logging import get_logger
			logger = get_logger(__name__)
			logger.debug(f"Undo menu action failed: {e}")
	
	def on_edit_redo(self, action, param):
		"""Redo the last undone action for the active document."""
		try:
			if not self.model_canvas_loader:
				return
			da = self.model_canvas_loader.get_current_document()
			if not da:
				return
			manager = self.model_canvas_loader.get_canvas_manager(da)
			if manager and hasattr(manager, 'undo_manager') and manager.undo_manager:
				if manager.undo_manager.redo(manager):
					try:
						da.queue_draw()
					except (TypeError, AttributeError) as e:
						from shypn.utils.logging import get_logger
						logger = get_logger(__name__)
						logger.debug(f"Failed to queue draw after redo: {e}")
		except (AttributeError, TypeError) as e:
			# Keep menu action resilient
			from shypn.utils.logging import get_logger
			logger = get_logger(__name__)
			logger.debug(f"Redo menu action failed: {e}")
	
	def on_edit_cut(self, action, param):
		"""Cut selected Places and Transitions to the internal clipboard."""
		try:
			self._copy_selection_to_clipboard()
			if not self._clipboard:
				return
			if not self.model_canvas_loader:
				return
			da = self.model_canvas_loader.get_current_document()
			if not da:
				return
			manager = self.model_canvas_loader.get_canvas_manager(da)
			if not manager:
				return
			selected = manager.selection_manager.get_selected_objects(manager)
			for obj in selected:
				self.model_canvas_loader._delete_object(manager, obj)
			da.queue_draw()
		except (AttributeError, TypeError) as e:
			from shypn.utils.logging import get_logger
			get_logger(__name__).debug(f"Cut failed: {e}")

	def on_edit_copy(self, action, param):
		"""Copy selected Places and Transitions to the internal clipboard."""
		try:
			self._copy_selection_to_clipboard()
		except (AttributeError, TypeError) as e:
			from shypn.utils.logging import get_logger
			get_logger(__name__).debug(f"Copy failed: {e}")

	def on_edit_paste(self, action, param):
		"""Paste clipboard contents onto the current canvas with a 20 px offset."""
		if not self._clipboard:
			return
		try:
			if not self.model_canvas_loader:
				return
			da = self.model_canvas_loader.get_current_document()
			if not da:
				return
			manager = self.model_canvas_loader.get_canvas_manager(da)
			if not manager:
				return
			OFFSET = 20  # world-space paste offset so copies are visually distinct
			for entry in self._clipboard:
				obj_type = entry.get('type')
				data = entry.get('data', {})
				x = data.get('x', 100) + OFFSET
				y = data.get('y', 100) + OFFSET
				name = data.get('name', '')
				if obj_type == 'place':
					new_obj = manager.add_place(x, y, label=name, tokens=data.get('tokens', 0))
				elif obj_type == 'transition':
					new_obj = manager.add_transition(x, y, label=name,
						transition_type=data.get('transition_type', 'immediate'))
				else:
					continue
				if new_obj:
					new_obj.name = name
				da.queue_draw()
		except (AttributeError, TypeError, KeyError) as e:
			from shypn.utils.logging import get_logger
			get_logger(__name__).debug(f"Paste failed: {e}")

	def _copy_selection_to_clipboard(self) -> None:
		"""Serialise the current canvas selection into ``self._clipboard``.

		Only Places and Transitions are copied; Arcs are intentionally skipped
		because their source/target IDs would be stale on paste.
		"""
		from shypn.netobjs import Place, Transition
		if not self.model_canvas_loader:
			return
		da = self.model_canvas_loader.get_current_document()
		if not da:
			return
		manager = self.model_canvas_loader.get_canvas_manager(da)
		if not manager or not hasattr(manager, 'selection_manager'):
			return
		selected = manager.selection_manager.get_selected_objects(manager)
		self._clipboard = []
		for obj in selected:
			if isinstance(obj, Place):
				self._clipboard.append({'type': 'place', 'data': obj.to_dict()})
			elif isinstance(obj, Transition):
				self._clipboard.append({'type': 'transition', 'data': obj.to_dict()})

	def on_edit_preferences(self, action, param):
		"""Open a stub preferences dialog."""
		dialog = Gtk.MessageDialog(
			transient_for=self.window,
			modal=True,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.CLOSE,
			text="Preferences",
		)
		dialog.format_secondary_text(
			"A full preferences panel is planned for a future release.\n"
			"Current simulation and display settings are available in the\n"
			"Swiss-Knife palette on each canvas."
		)
		dialog.run()
		dialog.destroy()

	# ====================================================================
	# View Menu Actions
	# ====================================================================
	
	def on_view_zoom_in(self, action, param):
		"""Zoom in the current canvas view."""
		self._apply_zoom(lambda vc: vc.zoom_in())

	def on_view_zoom_out(self, action, param):
		"""Zoom out the current canvas view."""
		self._apply_zoom(lambda vc: vc.zoom_out())

	def on_view_zoom_reset(self, action, param):
		"""Reset the current canvas zoom to 100 %."""
		self._apply_zoom(lambda vc: vc.set_zoom(1.0))

	def _apply_zoom(self, zoom_fn) -> None:
		"""Call *zoom_fn* on the active canvas's ViewportController.

		Args:
			zoom_fn: Callable that receives a ViewportController instance.
		"""
		try:
			if not self.model_canvas_loader:
				return
			da = self.model_canvas_loader.get_current_document()
			if not da:
				return
			manager = self.model_canvas_loader.get_canvas_manager(da)
			if manager and hasattr(manager, 'viewport_controller'):
				zoom_fn(manager.viewport_controller)
				da.queue_draw()
		except (AttributeError, TypeError) as e:
			from shypn.utils.logging import get_logger
			get_logger(__name__).debug(f"Zoom action failed: {e}")
	
	def on_view_fullscreen(self, action, param):
		"""Toggle fullscreen mode."""
		if self.window.is_maximized():
			self.window.unmaximize()
		else:
			self.window.maximize()	# ====================================================================
	# Help Menu Actions
	# ====================================================================
	
	def on_help_contents(self, action, param):
		"""Open the project documentation in the default web browser."""
		try:
			import webbrowser
			webbrowser.open("https://github.com/simao-eugenio/shypn")
		except Exception as e:
			self._show_error_dialog("Help", f"Could not open browser: {e}")

	def on_help_shortcuts(self, action, param):
		"""Show a keyboard-shortcuts reference dialog."""
		SHORTCUTS = [
			("File", [
				("Ctrl+N", "New canvas"),
				("Ctrl+O", "Open file"),
				("Ctrl+S", "Save"),
				("Ctrl+Shift+S", "Save as"),
				("Ctrl+Shift+N", "Reset canvas"),
				("Ctrl+Q", "Quit"),
			]),
			("Edit", [
				("Ctrl+Z", "Undo"),
				("Ctrl+Shift+Z", "Redo"),
				("Ctrl+X", "Cut"),
				("Ctrl+C", "Copy"),
				("Ctrl+V", "Paste"),
			]),
			("View", [
				("Ctrl++", "Zoom in"),
				("Ctrl+-", "Zoom out"),
				("Ctrl+0", "Reset zoom"),
			]),
		]
		lines = []
		for section, items in SHORTCUTS:
			lines.append(f"── {section} ──")
			for key, desc in items:
				lines.append(f"  {key:<20} {desc}")
			lines.append("")
		dialog = Gtk.MessageDialog(
			transient_for=self.window,
			modal=True,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.CLOSE,
			text="Keyboard Shortcuts",
		)
		dialog.format_secondary_text("\n".join(lines))
		dialog.run()
		dialog.destroy()
	
	def on_help_about(self, action, param):
		"""Show about dialog."""
		from shypn import __version__, __version_name__
		
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_transient_for(self.window)
		about_dialog.set_modal(True)
		about_dialog.set_program_name("SHYpn")
		about_dialog.set_version(f"{__version__} ({__version_name__})")
		about_dialog.set_comments("Signal Hierarchical Petri Nets for Systems Biology")
		about_dialog.set_website("https://github.com/simao-eugenio/shypn")
		about_dialog.set_license_type(Gtk.License.MIT_X11)
		about_dialog.set_authors(["Eugénio Simão"])
		about_dialog.set_copyright("Copyright © 2024-2026 Eugénio Simão")
		about_dialog.run()
		about_dialog.destroy()
	
	# ====================================================================
	# Action Registration
	# ====================================================================
	
	def register_all_actions(self):
		"""Register all menu actions with the application."""
		
		# File menu actions
		self._register_action("new", self.on_file_new, "<Primary>n")
		self._register_action("open", self.on_file_open, "<Primary>o")
		self._register_action("save", self.on_file_save, "<Primary>s")
		self._register_action("save-as", self.on_file_save_as, "<Primary><Shift>s")
		self._register_action("export-pdf", self.on_file_export_pdf, "<Primary>e")
		self._register_action("reset-canvas", self.on_file_reset_canvas, "<Primary><Shift>n")
		self._register_action("quit", self.on_file_quit, "<Primary>q")
		
		# Edit menu actions
		self._register_action("undo", self.on_edit_undo, "<Primary>z")
		self._register_action("redo", self.on_edit_redo, "<Primary><Shift>z")
		self._register_action("cut", self.on_edit_cut, "<Primary>x")
		self._register_action("copy", self.on_edit_copy, "<Primary>c")
		self._register_action("paste", self.on_edit_paste, "<Primary>v")
		self._register_action("preferences", self.on_edit_preferences)
		
		# View menu actions
		self._register_action("zoom-in", self.on_view_zoom_in, "<Primary>plus")
		self._register_action("zoom-out", self.on_view_zoom_out, "<Primary>minus")
		self._register_action("zoom-reset", self.on_view_zoom_reset, "<Primary>0")
		self._register_action("fullscreen", self.on_view_fullscreen, "F11")
		
		# Help menu actions
		self._register_action("help", self.on_help_contents, "F1")
		self._register_action("shortcuts", self.on_help_shortcuts, "<Primary>question")
		self._register_action("about", self.on_help_about)
	
	def _register_action(self, name, callback, accelerator=None):
		"""Helper to register a single action.
		
		Args:
			name: Action name (e.g., "new", "open")
			callback: Method to call when action is activated
			accelerator: Keyboard shortcut (e.g., "<Primary>n" for Ctrl+N)
		"""
		action = Gio.SimpleAction.new(name, None)
		action.connect("activate", callback)
		self.app.add_action(action)
		
		# Set keyboard accelerator if provided
		if accelerator:
			self.app.set_accels_for_action(f"app.{name}", [accelerator])
	
	# ====================================================================
	# Helper Methods
	# ====================================================================
	
	def _show_error_dialog(self, title, message):
		"""Show an error dialog to the user.
		
		Args:
			title: Dialog title
			message: Error message to display
		"""
		dialog = Gtk.MessageDialog(
			transient_for=self.window,
			modal=True,
			message_type=Gtk.MessageType.ERROR,
			buttons=Gtk.ButtonsType.OK,
			text=title
		)
		dialog.format_secondary_text(message)
		dialog.run()
		dialog.destroy()
	
	def _show_info_dialog(self, title, message):
		"""Show an information dialog to the user.
		
		Args:
			title: Dialog title
			message: Information message to display
		"""
		dialog = Gtk.MessageDialog(
			transient_for=self.window,
			modal=True,
			message_type=Gtk.MessageType.INFO,
			buttons=Gtk.ButtonsType.OK,
			text=title
		)
		dialog.format_secondary_text(message)
		dialog.run()
		dialog.destroy()


__all__ = ['MenuActions']
