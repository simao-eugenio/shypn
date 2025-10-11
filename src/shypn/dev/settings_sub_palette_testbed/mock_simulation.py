"""
Mock Simulation Controller for Settings Sub-Palette Testbed

This is a simplified mock of the real SimulationController that provides
just enough functionality to test the settings sub-palette UI without
needing a full Petri Net model.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, GObject


class MockSimulationSettings:
    """Mock simulation settings (simplified version of real SimulationSettings)."""
    
    def __init__(self):
        # Time settings
        self.duration = 60.0  # seconds
        self.time_units = "seconds"
        
        # Time step settings
        self.dt_auto = 0.1  # Auto-calculated time step
        self.dt_manual = None  # Manual time step (None = use auto)
        
        # ⭐ Time scale (playback speed multiplier)
        self.time_scale = 1.0  # 1.0 = real-time
        
        # Conflict resolution
        self.conflict_policy = "Random"
    
    def get_effective_dt(self):
        """Get the effective time step (manual or auto)."""
        if self.dt_manual is not None:
            return self.dt_manual
        return self.dt_auto
    
    def get_duration_seconds(self):
        """Get duration in seconds."""
        # In real implementation, this converts from time_units
        return self.duration
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.duration = 60.0
        self.time_units = "seconds"
        self.dt_auto = 0.1
        self.dt_manual = None
        self.time_scale = 1.0
        self.conflict_policy = "Random"


class MockSimulationController(GObject.GObject):
    """Mock simulation controller for UI testing.
    
    This mock provides:
    - Basic run/stop/step/reset functionality
    - Time tracking
    - Progress calculation
    - Step callbacks (for UI updates)
    
    It does NOT:
    - Execute actual Petri Net transitions
    - Handle conflicts (no transitions to fire)
    - Collect real simulation data
    """
    
    def __init__(self):
        super().__init__()
        self.settings = MockSimulationSettings()
        self.time = 0.0
        self._running = False
        self._timeout_id = None
        self._step_listeners = []
    
    def add_step_listener(self, callback):
        """Add a callback to be notified after each step.
        
        Args:
            callback: Function(controller, time) to call after each step
        """
        self._step_listeners.append(callback)
    
    def _notify_step_listeners(self):
        """Notify all step listeners."""
        for callback in self._step_listeners:
            try:
                callback(self, self.time)
            except Exception as e:
                print(f"Error in step listener: {e}")
    
    def run(self):
        """Start continuous simulation (mock version)."""
        if self._running:
            return
        
        self._running = True
        
        # Calculate steps per callback based on time_scale
        gui_interval_ms = 100  # 100ms GUI updates
        gui_interval_s = gui_interval_ms / 1000.0
        
        # How much model time should pass per GUI update?
        # time_scale = model_seconds / real_seconds
        dt = self.settings.get_effective_dt()
        model_time_per_gui_update = gui_interval_s * self.settings.time_scale
        steps_per_callback = max(1, int(model_time_per_gui_update / dt))
        
        print(f"🏃 Mock simulation running:")
        print(f"  Time scale: {self.settings.time_scale}x")
        print(f"  dt: {dt}s")
        print(f"  Steps per GUI update: {steps_per_callback}")
        
        def _simulation_loop():
            """Execute simulation steps in batches."""
            if not self._running:
                return False
            
            # Execute batch of steps
            for _ in range(steps_per_callback):
                self.time += dt
                
                # Check if completed
                if self.time >= self.settings.get_duration_seconds():
                    self.time = self.settings.get_duration_seconds()
                    self.stop()
                    print("✓ Mock simulation completed")
                    break
            
            # Notify listeners (updates UI)
            self._notify_step_listeners()
            
            return self._running  # Continue if still running
        
        # Schedule periodic execution
        self._timeout_id = GLib.timeout_add(gui_interval_ms, _simulation_loop)
    
    def stop(self):
        """Stop simulation."""
        if not self._running:
            return
        
        self._running = False
        
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None
        
        print(f"⏸️ Mock simulation stopped at t={self.time:.2f}s")
    
    def step(self):
        """Execute one simulation step (mock version)."""
        if self._running:
            return False
        
        dt = self.settings.get_effective_dt()
        self.time += dt
        
        # Check completion
        if self.time >= self.settings.get_duration_seconds():
            self.time = self.settings.get_duration_seconds()
            print("✓ Mock simulation completed")
            self._notify_step_listeners()
            return False
        
        self._notify_step_listeners()
        return True
    
    def reset(self):
        """Reset simulation to initial state."""
        was_running = self._running
        if was_running:
            self.stop()
        
        self.time = 0.0
        print(f"🔄 Mock simulation reset")
        
        self._notify_step_listeners()
    
    def is_running(self):
        """Check if simulation is currently running."""
        return self._running
    
    def is_simulation_complete(self):
        """Check if simulation has reached duration limit."""
        return self.time >= self.settings.get_duration_seconds()
    
    def get_progress(self):
        """Get simulation progress (0.0 to 1.0)."""
        duration = self.settings.get_duration_seconds()
        if duration <= 0:
            return 0.0
        return min(self.time / duration, 1.0)


# Quick test
if __name__ == '__main__':
    print("Testing MockSimulationController...")
    
    controller = MockSimulationController()
    
    def on_step(ctrl, time):
        progress = ctrl.get_progress()
        print(f"  Step: t={time:.2f}s, progress={progress*100:.1f}%")
    
    controller.add_step_listener(on_step)
    
    # Test basic functionality
    print("\n1. Test step()")
    controller.step()
    controller.step()
    
    print("\n2. Test reset()")
    controller.reset()
    
    print("\n3. Test time_scale effect")
    controller.settings.time_scale = 10.0  # 10x speed
    print(f"Set time_scale to {controller.settings.time_scale}x")
    
    print("\n4. Test run() for 2 seconds (will exit automatically)")
    controller.settings.duration = 2.0
    controller.run()
    
    # Run GTK main loop briefly
    from gi.repository import Gtk
    GLib.timeout_add(3000, lambda: Gtk.main_quit())  # Exit after 3s
    
    try:
        Gtk.main()
    except KeyboardInterrupt:
        pass
    
    print("\n✓ MockSimulationController test complete")
