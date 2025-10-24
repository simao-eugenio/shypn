"""Menu action handlers for File, Edit, View, Help menus.

This module contains all the action handlers for the main menu bar.
Keeping menu logic separate from the main loader maintains clean architecture.
"""

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
			self._show_error_dialog("New Document Error", f"Failed to create new document: {e}")
	
	def on_file_open(self, action, param):
		"""Open an existing file."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.open_document()
		except Exception as e:
			self._show_error_dialog("Open Document Error", f"Failed to open document: {e}")
	
	def on_file_save(self, action, param):
		"""Save the current file."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.save_current_document()
		except Exception as e:
			self._show_error_dialog("Save Document Error", f"Failed to save document: {e}")
	
	def on_file_save_as(self, action, param):
		"""Save the current file with a new name."""
		try:
			if self.file_explorer_panel:
				self.file_explorer_panel.save_current_document_as()
		except Exception as e:
			self._show_error_dialog("Save As Error", f"Failed to save document: {e}")
	
	def on_file_quit(self, action, param):
		"""Quit the application."""
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
	
	def on_edit_undo(self, action, param):
		"""Undo the last action."""
		# TODO: Implement undo logic
		pass
	
	def on_edit_redo(self, action, param):
		"""Redo the last undone action."""
		# TODO: Implement redo logic
		pass
	
	def on_edit_cut(self, action, param):
		"""Cut the selected content."""
		# TODO: Implement cut logic
		pass
	
	def on_edit_copy(self, action, param):
		"""Copy the selected content."""
		# TODO: Implement copy logic
		pass
	
	def on_edit_paste(self, action, param):
		"""Paste the clipboard content."""
		# TODO: Implement paste logic
		pass
	
	def on_edit_preferences(self, action, param):
		"""Open preferences dialog."""
		# TODO: Implement preferences dialog
		pass	# ====================================================================
	# View Menu Actions
	# ====================================================================
	
	def on_view_zoom_in(self, action, param):
		"""Zoom in the view."""
		# TODO: Implement zoom in
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.zoom_in()
		pass
	
	def on_view_zoom_out(self, action, param):
		"""Zoom out the view."""
		# TODO: Implement zoom out
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.zoom_out()
		pass
	
	def on_view_zoom_reset(self, action, param):
		"""Reset zoom to 100%."""
		# TODO: Implement zoom reset
		# if self.model_canvas_loader:
		#     self.model_canvas_loader.reset_zoom()
		pass
	
	def on_view_fullscreen(self, action, param):
		"""Toggle fullscreen mode."""
		if self.window.is_maximized():
			self.window.unmaximize()
		else:
			self.window.maximize()	# ====================================================================
	# Help Menu Actions
	# ====================================================================
	
	def on_help_contents(self, action, param):
		"""Show help contents."""
		# TODO: Implement help dialog
		pass
	
	def on_help_shortcuts(self, action, param):
		"""Show keyboard shortcuts."""
		# TODO: Implement shortcuts window
		pass
	
	def on_help_about(self, action, param):
		"""Show about dialog."""
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
		self._register_action("new", self.on_file_new, "<Primary>n")
		self._register_action("open", self.on_file_open, "<Primary>o")
		self._register_action("save", self.on_file_save, "<Primary>s")
		self._register_action("save-as", self.on_file_save_as, "<Primary><Shift>s")
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


__all__ = ['MenuActions']
