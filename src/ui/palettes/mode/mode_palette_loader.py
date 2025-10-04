import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

class ModePaletteLoader(GObject.GObject):
    __gsignals__ = {
        'mode-changed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        builder = Gtk.Builder()
        builder.add_from_file('ui/palettes/mode/mode_palette.ui')
        self.container = builder.get_object('mode_palette_container')
        self.edit_button = builder.get_object('edit_mode_button')
        self.sim_button = builder.get_object('sim_mode_button')
        self.edit_button.connect('clicked', self.on_edit_clicked)
        self.sim_button.connect('clicked', self.on_sim_clicked)
        self.current_mode = 'edit'
        self.update_button_states()

    def on_edit_clicked(self, button):
        if self.current_mode != 'edit':
            self.current_mode = 'edit'
            self.emit('mode-changed', 'edit')
            self.update_button_states()

    def on_sim_clicked(self, button):
        if self.current_mode != 'sim':
            self.current_mode = 'sim'
            self.emit('mode-changed', 'sim')
            self.update_button_states()

    def update_button_states(self):
        self.edit_button.set_sensitive(self.current_mode != 'edit')
        self.sim_button.set_sensitive(self.current_mode != 'sim')

    def get_widget(self):
        return self.container
