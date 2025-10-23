"""Menu action handlers for File, Edit, View, Help menus.

This module contains all the action handlers for the main menu bar.
Keeping menu logic separate from the main loader maintains clean architecture.
"""

import sys
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
		
	def set_persistency(self, persistency):
		"""Set the persistency manager for file operations."""
		self.persistency = persistency
	
	def set_canvas_loader(self, canvas_loader):
		"""Set the canvas loader for view operations."""
		self.model_canvas_loader = canvas_loader
	
	# ====================================================================
	# File Menu Actions
	# ====================================================================
	
	def on_file_new(self, action, param):
		"""Create a new file/model."""
		print("[MENU] File → New", file=sys.stderr)
		# TODO: Implement new file logic
		# if self.persistency:
		#     self.persistency.new_file()
	
	def on_file_open(self, action, param):
		"""Open an existing file."""
		print("[MENU] File → Open", file=sys.stderr)
		# TODO: Implement open file dialog
		# if self.persistency:
		#     self.persistency.load_file()
	
	def on_file_save(self, action, param):
		"""Save the current file."""
		print("[MENU] File → Save", file=sys.stderr)
		# TODO: Implement save logic
		# if self.persistency:
		#     self.persistency.save_file()
	
	def on_file_save_as(self, action, param):
		"""Save the current file with a new name."""
		print("[MENU] File → Save As", file=sys.stderr)
		# TODO: Implement save as dialog
		# if self.persistency:
		#     self.persistency.save_file_as()
	
	def on_file_quit(self, action, param):
		"""Quit the application."""
		print("[MENU] File → Quit", file=sys.stderr)
		self.app.quit()
	
	# ====================================================================
	# Edit Menu Actions
	# ====================================================================
	
	def on_edit_undo(self, action, param):
		"""Undo the last action."""
		print("[MENU] Edit → Undo", file=sys.stderr)
		# TODO: Implement undo logic
	
	def on_edit_redo(self, action, param):
		"""Redo the last undone action."""
		print("[MENU] Edit → Redo", file=sys.stderr)
		# TODO: Implement redo logic
	
	def on_edit_cut(self, action, param):
		"""Cut selected content."""
		print("[MENU] Edit → Cut", file=sys.stderr)
		# TODO: Implement cut logic
	
	def on_edit_copy(self, action, param):
		"""Copy selected content."""
		print("[MENU] Edit → Copy", file=sys.stderr)
		# TODO: Implement copy logic
	
	def on_edit_paste(self, action, param):
		"""Paste content from clipboard."""
		print("[MENU] Edit → Paste", file=sys.stderr)
		# TODO: Implement paste logic
	
	def on_edit_preferences(self, action, param):
		"""Open preferences dialog."""
		print("[MENU] Edit → Preferences", file=sys.stderr)
		# TODO: Implement preferences dialog
	
	# ====================================================================
	# View Menu Actions
	# ====================================================================
	
	def on_view_zoom_in(self, action, param):
		"""Zoom in on the canvas."""
		print("[MENU] View → Zoom In", file=sys.stderr)
		# TODO: Implement zoom in logic
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.zoom_in()
	
	def on_view_zoom_out(self, action, param):
		"""Zoom out on the canvas."""
		print("[MENU] View → Zoom Out", file=sys.stderr)
		# TODO: Implement zoom out logic
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.zoom_out()
	
	def on_view_zoom_reset(self, action, param):
		"""Reset zoom to 100%."""
		print("[MENU] View → Reset Zoom", file=sys.stderr)
		# TODO: Implement zoom reset logic
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.zoom_reset()
	
	def on_view_fullscreen(self, action, param):
		"""Toggle fullscreen mode."""
		print("[MENU] View → Fullscreen", file=sys.stderr)
		if self.window.is_maximized():
			self.window.unfullscreen()
		else:
			self.window.fullscreen()
	
	# ====================================================================
	# Help Menu Actions
	# ====================================================================
	
	def on_help_contents(self, action, param):
		"""Show help contents."""
		print("[MENU] Help → Contents", file=sys.stderr)
		# TODO: Implement help dialog
	
	def on_help_shortcuts(self, action, param):
		"""Show keyboard shortcuts."""
		print("[MENU] Help → Keyboard Shortcuts", file=sys.stderr)
		# TODO: Implement shortcuts window
	
	def on_help_about(self, action, param):
		"""Show about dialog."""
		print("[MENU] Help → About", file=sys.stderr)
		about_dialog = Gtk.AboutDialog()
		about_dialog.set_transient_for(self.window)
		about_dialog.set_modal(True)
		about_dialog.set_program_name("Shypn")
		about_dialog.set_version("0.9.0-skeleton-pattern")
		about_dialog.set_comments("Systems Biology Pathway Editor")
		about_dialog.set_website("https://github.com/simao-eugenio/shypn")
		about_dialog.set_license_type(Gtk.License.GPL_3_0)
		about_dialog.set_authors(["Simão Eugénio"])
		about_dialog.run()
		about_dialog.destroy()
	
	# ====================================================================
	# Action Registration
	# ====================================================================
	
	def register_all_actions(self):
		"""Register all menu actions with the application."""
		
		# File menu actions
		self._register_action("new", self.on_file_new)
		self._register_action("open", self.on_file_open)
		self._register_action("save", self.on_file_save)
		self._register_action("save-as", self.on_file_save_as)
		self._register_action("quit", self.on_file_quit)
		
		# Edit menu actions
		self._register_action("undo", self.on_edit_undo)
		self._register_action("redo", self.on_edit_redo)
		self._register_action("cut", self.on_edit_cut)
		self._register_action("copy", self.on_edit_copy)
		self._register_action("paste", self.on_edit_paste)
		self._register_action("preferences", self.on_edit_preferences)
		
		# View menu actions
		self._register_action("zoom-in", self.on_view_zoom_in)
		self._register_action("zoom-out", self.on_view_zoom_out)
		self._register_action("zoom-reset", self.on_view_zoom_reset)
		self._register_action("fullscreen", self.on_view_fullscreen)
		
		# Help menu actions
		self._register_action("help", self.on_help_contents)
		self._register_action("shortcuts", self.on_help_shortcuts)
		self._register_action("about", self.on_help_about)
	
	def _register_action(self, name, callback):
		"""Helper to register a single action.
		
		Args:
			name: Action name (e.g., "new", "open")
			callback: Method to call when action is activated
		"""
		action = Gio.SimpleAction.new(name, None)
		action.connect("activate", callback)
		self.app.add_action(action)


__all__ = ['MenuActions']
