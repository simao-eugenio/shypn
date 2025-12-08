"""
Playback controls for experiment trajectory visualization.

Allows users to replay simulation trajectories on the canvas,
stepping through time to see how token distributions evolve.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
from typing import Optional, Callable, Dict, List


class PlaybackControls(Gtk.Box):
    """Playback controls for trajectory visualization.
    
    Provides:
    - Play/Pause button
    - Time slider
    - Speed control
    - Current time display
    - Step forward/backward buttons
    """
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        
        # Playback state
        self.is_playing = False
        self.current_time_index = 0
        self.time_points: List[float] = []
        self.trajectory_data: Dict[str, List[float]] = {}
        self.playback_speed = 1.0  # 1x = real-time
        self.playback_timer_id: Optional[int] = None
        
        # Callbacks
        self.on_time_changed: Optional[Callable[[int, float], None]] = None
        
        self._build_ui()
        self._set_enabled(False)
    
    def _build_ui(self):
        """Build the playback control UI."""
        
        # === Top row: Transport controls ===
        transport_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.pack_start(transport_box, False, False, 0)
        
        # Step backward button
        self.step_back_btn = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("media-skip-backward", Gtk.IconSize.BUTTON)
        self.step_back_btn.set_image(icon)
        self.step_back_btn.set_tooltip_text("Step backward")
        self.step_back_btn.connect("clicked", self._on_step_back)
        transport_box.pack_start(self.step_back_btn, False, False, 0)
        
        # Play/Pause button
        self.play_btn = Gtk.Button()
        self.play_icon = Gtk.Image.new_from_icon_name("media-playback-start", Gtk.IconSize.BUTTON)
        self.pause_icon = Gtk.Image.new_from_icon_name("media-playback-pause", Gtk.IconSize.BUTTON)
        self.play_btn.set_image(self.play_icon)
        self.play_btn.set_tooltip_text("Play")
        self.play_btn.connect("clicked", self._on_play_pause)
        transport_box.pack_start(self.play_btn, False, False, 0)
        
        # Step forward button
        self.step_forward_btn = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("media-skip-forward", Gtk.IconSize.BUTTON)
        self.step_forward_btn.set_image(icon)
        self.step_forward_btn.set_tooltip_text("Step forward")
        self.step_forward_btn.connect("clicked", self._on_step_forward)
        transport_box.pack_start(self.step_forward_btn, False, False, 0)
        
        # Reset button
        reset_btn = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("media-skip-backward", Gtk.IconSize.BUTTON)
        reset_btn.set_image(icon)
        reset_btn.set_label("Reset")
        reset_btn.set_tooltip_text("Reset to start")
        reset_btn.connect("clicked", self._on_reset)
        transport_box.pack_start(reset_btn, False, False, 0)
        
        # Spacer
        transport_box.pack_start(Gtk.Label(), True, True, 0)
        
        # Speed control
        speed_label = Gtk.Label(label="Speed:")
        transport_box.pack_start(speed_label, False, False, 0)
        
        self.speed_combo = Gtk.ComboBoxText()
        for speed, label in [(0.25, "0.25×"), (0.5, "0.5×"), (1.0, "1×"), 
                             (2.0, "2×"), (4.0, "4×"), (8.0, "8×")]:
            self.speed_combo.append(str(speed), label)
        self.speed_combo.set_active_id("1.0")
        self.speed_combo.connect("changed", self._on_speed_changed)
        transport_box.pack_start(self.speed_combo, False, False, 0)
        
        # === Time slider ===
        slider_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.pack_start(slider_box, False, False, 0)
        
        # Current time label
        self.time_label = Gtk.Label(label="Time: 0.00 s")
        self.time_label.set_width_chars(15)
        slider_box.pack_start(self.time_label, False, False, 0)
        
        # Time slider
        self.time_adjustment = Gtk.Adjustment(value=0, lower=0, upper=100, 
                                               step_increment=1, page_increment=10)
        self.time_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL,
                                      adjustment=self.time_adjustment)
        self.time_slider.set_draw_value(False)
        self.time_slider.connect("value-changed", self._on_slider_changed)
        slider_box.pack_start(self.time_slider, True, True, 0)
        
        # Duration label
        self.duration_label = Gtk.Label(label="/ 100.0 s")
        self.duration_label.set_width_chars(12)
        slider_box.pack_start(self.duration_label, False, False, 0)
    
    def load_trajectory(self, time_points: List[float], place_data: Dict[str, List[float]]):
        """Load trajectory data for playback.
        
        Args:
            time_points: List of time values
            place_data: Dictionary mapping place IDs to token count trajectories
        """
        self.time_points = time_points
        self.trajectory_data = place_data
        
        if not time_points:
            self._set_enabled(False)
            return
        
        # Update slider range
        self.time_adjustment.set_upper(len(time_points) - 1)
        self.time_adjustment.set_value(0)
        
        # Update labels
        self.duration_label.set_text(f"/ {time_points[-1]:.2f} s")
        self.time_label.set_text(f"Time: {time_points[0]:.2f} s")
        
        # Reset state
        self.current_time_index = 0
        self._set_enabled(True)
        
        # Notify initial state
        if self.on_time_changed:
            self.on_time_changed(0, time_points[0])
    
    def _set_enabled(self, enabled: bool):
        """Enable or disable controls."""
        self.play_btn.set_sensitive(enabled)
        self.step_back_btn.set_sensitive(enabled)
        self.step_forward_btn.set_sensitive(enabled)
        self.time_slider.set_sensitive(enabled)
        self.speed_combo.set_sensitive(enabled)
    
    def _on_play_pause(self, button):
        """Handle play/pause button click."""
        if self.is_playing:
            self._pause()
        else:
            self._play()
    
    def _play(self):
        """Start playback."""
        if not self.time_points:
            return
        
        self.is_playing = True
        self.play_btn.set_image(self.pause_icon)
        self.play_btn.set_tooltip_text("Pause")
        
        # Calculate interval based on speed
        # If we have dt=0.01s between points and speed=1x, update every 10ms
        if len(self.time_points) >= 2:
            dt = self.time_points[1] - self.time_points[0]
            interval_ms = int((dt / self.playback_speed) * 1000)
            interval_ms = max(10, interval_ms)  # Min 10ms
        else:
            interval_ms = 100
        
        # Start timer
        self.playback_timer_id = GLib.timeout_add(interval_ms, self._on_playback_tick)
    
    def _pause(self):
        """Pause playback."""
        self.is_playing = False
        self.play_btn.set_image(self.play_icon)
        self.play_btn.set_tooltip_text("Play")
        
        # Stop timer
        if self.playback_timer_id is not None:
            GLib.source_remove(self.playback_timer_id)
            self.playback_timer_id = None
    
    def _on_playback_tick(self) -> bool:
        """Handle playback timer tick.
        
        Returns:
            bool: True to continue, False to stop timer
        """
        if not self.is_playing:
            return False
        
        # Advance to next time point
        self.current_time_index += 1
        
        # Check if we've reached the end
        if self.current_time_index >= len(self.time_points):
            self.current_time_index = len(self.time_points) - 1
            self._pause()
            return False
        
        # Update UI
        self._update_display()
        
        # Notify callback
        if self.on_time_changed:
            time = self.time_points[self.current_time_index]
            self.on_time_changed(self.current_time_index, time)
        
        return True
    
    def _on_step_back(self, button):
        """Step backward one frame."""
        if self.current_time_index > 0:
            self.current_time_index -= 1
            self._update_display()
            
            if self.on_time_changed:
                time = self.time_points[self.current_time_index]
                self.on_time_changed(self.current_time_index, time)
    
    def _on_step_forward(self, button):
        """Step forward one frame."""
        if self.current_time_index < len(self.time_points) - 1:
            self.current_time_index += 1
            self._update_display()
            
            if self.on_time_changed:
                time = self.time_points[self.current_time_index]
                self.on_time_changed(self.current_time_index, time)
    
    def _on_reset(self, button):
        """Reset to start."""
        self._pause()
        self.current_time_index = 0
        self._update_display()
        
        if self.on_time_changed and self.time_points:
            self.on_time_changed(0, self.time_points[0])
    
    def _on_slider_changed(self, slider):
        """Handle slider value change."""
        if not self.time_points:
            return
        
        # Update current time index
        self.current_time_index = int(slider.get_value())
        
        # Update time label
        time = self.time_points[self.current_time_index]
        self.time_label.set_text(f"Time: {time:.2f} s")
        
        # Notify callback
        if self.on_time_changed:
            self.on_time_changed(self.current_time_index, time)
    
    def _on_speed_changed(self, combo):
        """Handle speed selection change."""
        speed_str = combo.get_active_id()
        if speed_str:
            self.playback_speed = float(speed_str)
            
            # If playing, restart timer with new speed
            if self.is_playing:
                self._pause()
                self._play()
    
    def _update_display(self):
        """Update time display and slider."""
        if not self.time_points:
            return
        
        time = self.time_points[self.current_time_index]
        self.time_label.set_text(f"Time: {time:.2f} s")
        
        # Update slider without triggering callback
        self.time_slider.handler_block_by_func(self._on_slider_changed)
        self.time_slider.set_value(self.current_time_index)
        self.time_slider.handler_unblock_by_func(self._on_slider_changed)
    
    def cleanup(self):
        """Clean up resources."""
        self._pause()
        self.time_points = []
        self.trajectory_data = {}
