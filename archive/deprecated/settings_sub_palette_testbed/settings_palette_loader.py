"""
Settings Palette Loader for Testbed

This prototype loader demonstrates the settings sub-palette functionality
before integrating into production code.
"""

import os
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject


class SettingsPaletteLoader(GObject.GObject):
    """Prototype loader for settings sub-palette testing."""
    
    __gsignals__ = {
        'step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, simulation, ui_dir):
        super().__init__()
        self.simulation = simulation
        self.ui_dir = ui_dir
        self.ui_path = os.path.join(ui_dir, 'settings_palette_prototype.ui')
        
        # Widget references
        self.builder = None
        self.simulate_tools_revealer = None
        self.simulate_tools_container = None
        
        # Control buttons
        self.run_button = None
        self.step_button = None
        self.stop_button = None
        self.reset_button = None
        self.settings_button = None
        
        # Duration controls
        self.duration_entry = None
        self.time_units_combo = None
        self.progress_bar = None
        self.time_display_label = None
        
        # ⭐ Settings sub-palette widgets
        self.settings_revealer = None
        self.settings_event_box = None
        self.settings_frame = None
        self.settings_container = None
        
        # Time Step controls  
        self.dt_auto_radio = None
        self.dt_manual_entry = None
        
        # Speed controls (⭐ NEW - 4 presets: 0.1x, 1x, 10x, 60x)
        self.speed_0_1x_button = None
        self.speed_1x_button = None
        self.speed_10x_button = None
        self.speed_60x_button = None
        self.time_scale_spin = None
        
        # Conflict policy
        self.conflict_policy_combo = None
        
        # Action buttons
        self.settings_apply_button = None
        self.settings_reset_button = None
        
        # State
        self._was_running_before_settings = False
        
        self._load_ui()
        self._apply_styling()
        self._load_settings_into_ui()
        
        # Listen to simulation steps
        self.simulation.add_step_listener(self._on_simulation_step)
    
    def _load_ui(self):
        """Load UI from file and get widget references."""
        if not os.path.exists(self.ui_path):
            raise FileNotFoundError(f'UI file not found: {self.ui_path}')
        
        self.builder = Gtk.Builder.new_from_file(self.ui_path)
        
        # Main palette widgets
        self.simulate_tools_revealer = self.builder.get_object('simulate_tools_revealer')
        self.simulate_tools_container = self.builder.get_object('simulate_tools_container')
        
        # Control buttons
        self.run_button = self.builder.get_object('run_simulation_button')
        self.step_button = self.builder.get_object('step_simulation_button')
        self.stop_button = self.builder.get_object('stop_simulation_button')
        self.reset_button = self.builder.get_object('reset_simulation_button')
        self.settings_button = self.builder.get_object('settings_simulation_button')
        
        # Duration controls
        self.duration_entry = self.builder.get_object('duration_entry')
        self.time_units_combo = self.builder.get_object('time_units_combo')
        self.progress_bar = self.builder.get_object('simulation_progress_bar')
        self.time_display_label = self.builder.get_object('time_display_label')
        
        # ⭐ Settings sub-palette
        self.settings_revealer = self.builder.get_object('settings_revealer')
        self.settings_event_box = self.builder.get_object('settings_event_box')
        self.settings_frame = self.builder.get_object('settings_frame')
        self.settings_container = self.builder.get_object('settings_container')
        
        # Time Step controls
        self.dt_auto_radio = self.builder.get_object('dt_auto_radio')
        self.dt_manual_entry = self.builder.get_object('dt_manual_entry')
        
        # Speed controls (4 presets: 0.1x, 1x, 10x, 60x)
        self.speed_0_1x_button = self.builder.get_object('speed_0_1x_button')
        self.speed_1x_button = self.builder.get_object('speed_1x_button')
        self.speed_10x_button = self.builder.get_object('speed_10x_button')
        self.speed_60x_button = self.builder.get_object('speed_60x_button')
        self.time_scale_spin = self.builder.get_object('time_scale_spin')
        
        # Conflict policy
        self.conflict_policy_combo = self.builder.get_object('conflict_policy_combo')
        
        # Action buttons
        self.settings_apply_button = self.builder.get_object('settings_apply_button')
        self.settings_reset_button = self.builder.get_object('settings_reset_button')
        
        # Connect signals
        self._connect_signals()
    
    def _connect_signals(self):
        """Connect all widget signals."""
        # Control buttons
        self.run_button.connect('clicked', self._on_run_clicked)
        self.step_button.connect('clicked', self._on_step_clicked)
        self.stop_button.connect('clicked', self._on_stop_clicked)
        self.reset_button.connect('clicked', self._on_reset_clicked)
        
        # ⭐ Settings toggle (changed from 'clicked' to 'toggled')
        self.settings_button.connect('toggled', self._on_settings_toggled)
        
        # Duration controls
        self.duration_entry.connect('changed', self._on_duration_changed)
        
        # ⭐ Settings sub-palette signals
        self._connect_settings_signals()
    
    def _connect_settings_signals(self):
        """Connect settings sub-palette widget signals."""
        # Time Step
        self.dt_auto_radio.connect('toggled', self._on_dt_mode_changed)
        self.dt_manual_entry.connect('changed', self._on_dt_manual_changed)
        
        # Speed presets (⭐ 4 buttons: 0.1x, 1x, 10x, 60x)
        speed_buttons = [
            (self.speed_0_1x_button, 0.1),
            (self.speed_1x_button, 1.0),
            (self.speed_10x_button, 10.0),
            (self.speed_60x_button, 60.0)
        ]
        for button, value in speed_buttons:
            button.connect('toggled', self._on_speed_preset_toggled, value)
            # Debug: Add button-press-event to see if clicks reach the buttons
            button.connect('button-press-event', self._on_speed_button_clicked, value)
        
        # Custom speed
        self.time_scale_spin.connect('value-changed', self._on_time_scale_changed)
        
        # Conflict policy
        self.conflict_policy_combo.connect('changed', self._on_conflict_policy_changed)
        
        # Debug: Test if combo is receiving events
        self.conflict_policy_combo.connect('button-press-event', self._on_combo_clicked)
        
        # Debug: Test if event box is capturing clicks
        if self.settings_event_box:
            self.settings_event_box.connect('button-press-event', self._on_settings_event_box_clicked)
        
        # Action buttons
        self.settings_apply_button.connect('clicked', self._on_settings_apply_clicked)
        self.settings_reset_button.connect('clicked', self._on_settings_reset_clicked)
    
    # ═══════════════════════════════════════════════════════════════════
    # Control Button Handlers
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_run_clicked(self, button):
        """Handle Run button click."""
        print("▶️  Run clicked")
        self.simulation.run()
        self._update_button_states(running=True)
    
    def _on_step_clicked(self, button):
        """Handle Step button click."""
        print("⏭️  Step clicked")
        success = self.simulation.step()
        if not success or self.simulation.is_simulation_complete():
            self._update_button_states(running=False, completed=True)
    
    def _on_stop_clicked(self, button):
        """Handle Stop button click."""
        print("⏸️  Stop clicked")
        self.simulation.stop()
        self._update_button_states(running=False)
    
    def _on_reset_clicked(self, button):
        """Handle Reset button click."""
        print("🔄 Reset clicked")
        self.simulation.reset()
        self.emit('reset-executed')
        self._update_progress_display()
        self._update_button_states(running=False, reset=True)
    
    # ═══════════════════════════════════════════════════════════════════
    # ⭐ Settings Toggle Handler (NEW)
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_settings_toggled(self, toggle_button):
        """Handle Settings toggle - show/hide settings sub-palette."""
        is_active = toggle_button.get_active()
        
        print(f"⚙️  Settings toggled: {'EXPAND' if is_active else 'COLLAPSE'}")
        
        if is_active:
            # Expand settings sub-palette
            self.settings_revealer.set_reveal_child(True)
            print("   Settings panel: VISIBLE")
            
            # Optional: Pause simulation while editing settings
            self._was_running_before_settings = self.simulation.is_running()
            if self._was_running_before_settings:
                print("   (Pausing simulation while settings open)")
                self.simulation.stop()
                self._update_button_states(running=False)
        else:
            # Collapse settings sub-palette
            self.settings_revealer.set_reveal_child(False)
            print("   Settings panel: HIDDEN")
            
            # Optional: Resume simulation if it was running
            if self._was_running_before_settings:
                print("   (Resuming simulation)")
                self.simulation.run()
                self._update_button_states(running=True)
                self._was_running_before_settings = False
    
    # ═══════════════════════════════════════════════════════════════════
    # Time Step Handlers
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_dt_mode_changed(self, radio_button):
        """Handle time step mode change (Auto checkbox)."""
        is_auto = radio_button.get_active()
        mode_str = "Auto" if is_auto else "Manual"
        print(f"⏱️  Time step mode: {mode_str}")
        
        # Enable/disable manual entry (opposite of auto checkbox)
        self.dt_manual_entry.set_sensitive(not is_auto)
        
        # Update simulation settings
        if not is_auto:  # Manual mode
            try:
                dt = float(self.dt_manual_entry.get_text())
                self.simulation.settings.dt_manual = dt
                print(f"   Manual dt: {dt}s")
            except ValueError:
                pass
        else:  # Auto mode
            self.simulation.settings.dt_manual = None
            print(f"   Auto dt: {self.simulation.settings.dt_auto}s")
    
    def _on_dt_manual_changed(self, entry):
        """Handle manual time step entry change."""
        if self.dt_auto_radio.get_active():  # Skip if in auto mode
            return
        
        try:
            dt = float(entry.get_text().strip())
            if dt > 0:
                self.simulation.settings.dt_manual = dt
                print(f"⏱️  Manual dt changed: {dt}s")
        except ValueError:
            pass
    
    # ═══════════════════════════════════════════════════════════════════
    # ⭐ Speed (Time Scale) Handlers (NEW)
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_speed_preset_toggled(self, toggle_button, speed_value):
        """Handle speed preset button toggle."""
        if not toggle_button.get_active():
            return
        
        print(f"🚀 Speed preset: {speed_value}x")
        
        # Uncheck other preset buttons (radio behavior) - 4 buttons
        speed_buttons = [
            self.speed_0_1x_button,
            self.speed_1x_button,
            self.speed_10x_button,
            self.speed_60x_button
        ]
        for btn in speed_buttons:
            if btn and btn != toggle_button:
                btn.handler_block_by_func(self._on_speed_preset_toggled)
                btn.set_active(False)
                btn.handler_unblock_by_func(self._on_speed_preset_toggled)
        
        # Update spin button
        self.time_scale_spin.set_value(speed_value)
        
        # Update simulation settings
        self.simulation.settings.time_scale = speed_value
        
        # Update time display
        self._update_progress_display()
        
        # If simulation is running, restart with new speed
        if self.simulation.is_running():
            print("   (Restarting simulation with new speed)")
            self.simulation.stop()
            self.simulation.run()
    
    def _on_time_scale_changed(self, spin_button):
        """Handle custom time scale spin button change."""
        value = spin_button.get_value()
        
        print(f"🚀 Custom speed: {value}x")
        
        # Uncheck all preset buttons (custom speed active) - 4 buttons
        speed_buttons = [
            self.speed_0_1x_button,
            self.speed_1x_button,
            self.speed_10x_button,
            self.speed_60x_button
        ]
        for btn in speed_buttons:
            if btn:
                btn.handler_block_by_func(self._on_speed_preset_toggled)
                btn.set_active(False)
                btn.handler_unblock_by_func(self._on_speed_preset_toggled)
        
        # Update simulation settings
        self.simulation.settings.time_scale = value
        
        # Update time display
        self._update_progress_display()
        
        # If simulation is running, restart with new speed
        if self.simulation.is_running():
            print("   (Restarting simulation with new speed)")
            self.simulation.stop()
            self.simulation.run()
    
    # ═══════════════════════════════════════════════════════════════════
    # Other Settings Handlers
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_conflict_policy_changed(self, combo):
        """Handle conflict policy combo change."""
        policy_str = combo.get_active_text()
        if policy_str:
            self.simulation.settings.conflict_policy = policy_str
            print(f"⚔️  Conflict policy: {policy_str}")
            # Emit settings changed signal
            self.emit('settings-changed')
    
    def _on_combo_clicked(self, widget, event):
        """Debug handler to verify combo is receiving clicks."""
        print(f"🖱️  Combo clicked! Button: {event.button}, Widget: {widget.get_name()}")
        print(f"   Sensitive: {widget.get_sensitive()}, Visible: {widget.get_visible()}")
        print(f"   Has items: {widget.get_model() is not None}")
        return False  # Let the event propagate
    
    def _on_settings_event_box_clicked(self, widget, event):
        """Debug handler to verify event box is capturing clicks."""
        print(f"📦 Settings EventBox clicked! Button: {event.button}")
        print(f"   Position: ({event.x:.0f}, {event.y:.0f})")
        # Don't block the event - let it propagate to children
        return False
    
    def _on_speed_button_clicked(self, button, event, speed_value):
        """Debug handler to verify speed buttons are receiving clicks."""
        print(f"⚡ Speed button clicked: {speed_value}x")
        print(f"   Button: {button.get_label()}, Active: {button.get_active()}")
        return False  # Let the event propagate to trigger 'toggled'
    
    def _on_duration_changed(self, entry):
        """Handle duration entry change."""
        try:
            duration = float(entry.get_text().strip())
            if duration > 0:
                self.simulation.settings.duration = duration
                print(f"⏲️  Duration: {duration}s")
                self._update_progress_display()
        except ValueError:
            pass
    
    # ═══════════════════════════════════════════════════════════════════
    # Action Button Handlers
    # ═══════════════════════════════════════════════════════════════════
    
    def _on_settings_apply_clicked(self, button):
        """Handle Apply button click - apply settings and close panel."""
        print("✅ Apply settings clicked")
        
        # Settings are applied in real-time via handlers
        # Just close the sub-palette
        self.settings_button.set_active(False)
        
        # Emit signal for potential external listeners
        self.emit('settings-changed')
    
    def _on_settings_reset_clicked(self, button):
        """Handle Reset button click - reset all settings to defaults."""
        print("🔄 Reset to defaults clicked")
        
        # Reset simulation settings
        self.simulation.settings.reset_to_defaults()
        
        # Update UI to reflect defaults
        self._load_settings_into_ui()
        
        # Emit signal
        self.emit('settings-changed')
    
    # ═══════════════════════════════════════════════════════════════════
    # UI Update Methods
    # ═══════════════════════════════════════════════════════════════════
    
    def _load_settings_into_ui(self):
        """Load current settings into UI widgets."""
        settings = self.simulation.settings
        
        # Duration
        self.duration_entry.set_text(str(settings.duration))
        
        # Time Step (Auto checkbox only, no Manual radio)
        if settings.dt_manual is None:
            self.dt_auto_radio.set_active(True)
            self.dt_manual_entry.set_sensitive(False)
        else:
            self.dt_auto_radio.set_active(False)
            self.dt_manual_entry.set_text(str(settings.dt_manual))
            self.dt_manual_entry.set_sensitive(True)
        
        # Time Scale
        time_scale = settings.time_scale
        self.time_scale_spin.set_value(time_scale)
        
        # Check matching preset button (4 presets: 0.1x, 1x, 10x, 60x)
        preset_map = {
            0.1: self.speed_0_1x_button,
            1.0: self.speed_1x_button,
            10.0: self.speed_10x_button,
            60.0: self.speed_60x_button
        }
        
        # Uncheck all first
        for btn in preset_map.values():
            if btn:
                btn.set_active(False)
        
        # Check matching preset (if any)
        if time_scale in preset_map:
            preset_map[time_scale].set_active(True)
        
        # Conflict Policy
        policy_index = ['Random', 'Oldest', 'Youngest', 'Priority'].index(settings.conflict_policy)
        self.conflict_policy_combo.set_active(policy_index)
    
    def _update_button_states(self, running=False, completed=False, reset=False):
        """Update button sensitivity based on simulation state."""
        if running:
            self.run_button.set_sensitive(False)
            self.step_button.set_sensitive(False)
            self.stop_button.set_sensitive(True)
            self.reset_button.set_sensitive(False)
            self.settings_button.set_sensitive(False)
        elif completed:
            self.run_button.set_sensitive(False)
            self.step_button.set_sensitive(False)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(True)
            self.settings_button.set_sensitive(True)
        elif reset:
            self.run_button.set_sensitive(True)
            self.step_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(False)
            self.settings_button.set_sensitive(True)
        else:
            self.run_button.set_sensitive(True)
            self.step_button.set_sensitive(True)
            self.stop_button.set_sensitive(False)
            self.reset_button.set_sensitive(True)
            self.settings_button.set_sensitive(True)
    
    def _on_simulation_step(self, controller, time):
        """Callback from simulation after each step."""
        self.emit('step-executed', time)
        self._update_progress_display()
    
    def _update_progress_display(self):
        """Update progress bar and time display label."""
        settings = self.simulation.settings
        
        # Update progress bar
        progress = self.simulation.get_progress()
        self.progress_bar.set_fraction(min(progress, 1.0))
        self.progress_bar.set_text(f"{int(progress * 100)}%")
        
        # Update time display with speed indication
        duration = settings.get_duration_seconds()
        current = self.simulation.time
        
        # Show speed if not 1.0x
        if abs(settings.time_scale - 1.0) > 0.01:
            speed_text = f" @ {settings.time_scale:.1f}x"
        else:
            speed_text = ""
        
        self.time_display_label.set_text(f"Time: {current:.1f} / {duration:.1f} s{speed_text}")
    
    def _apply_styling(self):
        """Apply CSS styling to widgets."""
        css = '''
        .simulate-tools-palette {
            background: linear-gradient(to bottom, #34495e, #2c3e50);
            border: 2px solid #1a252f;
            border-radius: 8px;
            padding: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
        }
        
        .sim-tool-button {
            background: linear-gradient(to bottom, #5d6d7e, #566573);
            border: 2px solid #34495e;
            border-radius: 4px;
            font-size: 14px;
            font-weight: bold;
            color: white;
            min-width: 40px;
            min-height: 40px;
        }
        
        .sim-tool-button:hover {
            background: linear-gradient(to bottom, #6c7a89, #5d6d7e);
        }
        
        .run-button { background: linear-gradient(to bottom, #27ae60, #229954); }
        .step-button { background: linear-gradient(to bottom, #16a085, #138d75); }
        .stop-button { background: linear-gradient(to bottom, #e74c3c, #c0392b); }
        .reset-button { background: linear-gradient(to bottom, #f39c12, #e67e22); }
        
        .settings-toggle-button { background: linear-gradient(to bottom, #5d6db9, #4a5899); }
        .settings-toggle-button:checked {
            background: linear-gradient(to bottom, #6c7dc9, #5d6db9);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .sim-control-label, .settings-control-label {
            color: white;
            font-size: 11px;
            font-weight: bold;
        }
        
        .sim-time-display {
            color: white;
            font-size: 12px;
            font-weight: bold;
        }
        
        /* Settings panel frame - Dark blue-gray */
        .settings-panel-frame {
            background: linear-gradient(to bottom, #3e5266, #2c3e50);
            border: 2px solid #1c2833;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }
        
        .settings-panel {
            background: rgba(44, 62, 80, 0.95);
        }
        
        .settings-header {
            color: #ecf0f1;
            font-size: 13px;
            font-weight: bold;
        }
        
        .settings-section-label {
            color: #bdc3c7;
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 0.5px;
        }
        
        .settings-label-small {
            color: #ecf0f1;
            font-size: 11px;
        }
        
        .settings-unit {
            color: #95a5a6;
            font-size: 11px;
        }
        
        .settings-radio {
            color: #ecf0f1;
        }
        
        .settings-entry-small {
            background: rgba(52, 73, 94, 0.8);
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 3px;
        }
        
        .settings-spin {
            background: rgba(52, 73, 94, 0.8);
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 3px;
        }
        
        .settings-combo {
            background: rgba(52, 73, 94, 0.8);
            color: #ecf0f1;
            border: 1px solid #34495e;
            border-radius: 3px;
            padding: 4px;
            min-height: 28px;
        }
        
        .settings-combo combobox button {
            background: rgba(52, 73, 94, 0.8);
            color: #ecf0f1;
            border: 1px solid #34495e;
        }
        
        .settings-combo combobox button:hover {
            background: rgba(62, 83, 104, 0.9);
        }
        
        /* Combo popup menu */
        .settings-combo menu {
            background: #2c3e50;
            color: #ecf0f1;
            border: 1px solid #1c2833;
        }
        
        .settings-combo menuitem {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 6px 12px;
        }
        
        .settings-combo menuitem:hover {
            background: #34495e;
            color: white;
        }
        
        .settings-button {
            background: linear-gradient(to bottom, #5d6d7e, #566573);
            border: 1px solid #34495e;
            border-radius: 4px;
            color: #ecf0f1;
            font-size: 11px;
            font-weight: bold;
        }
        
        .settings-button-primary {
            background: linear-gradient(to bottom, #3498db, #2980b9);
            border-color: #1f5a8b;
        }
        
        .settings-button:hover {
            background: linear-gradient(to bottom, #6c7a89, #5d6d7e);
        }
        
        .settings-button-primary:hover {
            background: linear-gradient(to bottom, #5dade2, #3498db);
        }
        
        /* Settings sub-palette frame (legacy) */
        .settings-sub-palette-frame {
            background: linear-gradient(to bottom, #273746, #212f3c);
            border: 2px solid #1a252f;
            border-radius: 6px;
            box-shadow: inset 0 2px 6px rgba(0, 0, 0, 0.4);
        }
        
        /* Speed preset buttons */
        .speed-preset-button {
            background: linear-gradient(to bottom, #5d6d7e, #566573);
            border: 2px solid #34495e;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: white;
            min-width: 50px;
            min-height: 30px;
        }
        
        .speed-preset-button:checked {
            background: linear-gradient(to bottom, #3498db, #2980b9);
            border-color: #1f5a8b;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .speed-preset-button:hover {
            background: linear-gradient(to bottom, #6c7a89, #5d6d7e);
        }
        '''
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        
        # Apply to all widgets
        Gtk.StyleContext.add_provider_for_screen(
            self.simulate_tools_container.get_screen(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def get_widget(self):
        """
        Get the root widget for adding to container.
        Returns an overlay with the main palette and settings panel.
        """
        # Create an overlay to allow both revealers to position independently
        overlay = Gtk.Overlay()
        
        # Add a transparent spacer as base (to keep overlay sizing)
        spacer = Gtk.Box()
        overlay.add(spacer)
        
        # Add both widgets as overlays (order matters for input events)
        # Settings panel must be added AFTER main palette to be on top
        overlay.add_overlay(self.simulate_tools_revealer)
        overlay.add_overlay(self.settings_revealer)
        
        # Don't set frame insensitive - we'll handle events differently
        
        return overlay
