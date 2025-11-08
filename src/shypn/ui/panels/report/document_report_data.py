#!/usr/bin/env python3
"""Document Report Data - Per-document container for report information.

Each canvas tab (document) has its own DocumentReportData instance that stores:
- Simulation results (time points, species data, reaction data)
- Model metadata
- Analysis results
- Provenance information

The Report Panel displays data from the currently active document.
"""


class DocumentReportData:
    """Container for per-document report data.
    
    This is stored per canvas tab in model_canvas_loader.overlay_managers[drawing_area].
    """
    
    def __init__(self, drawing_area=None):
        """Initialize document report data.
        
        Args:
            drawing_area: The DrawingArea widget this data belongs to
        """
        self.drawing_area = drawing_area
        
        # Simulation results (captured at simulation completion)
        self.last_simulation_data = None  # DataCollector snapshot
        self.last_simulation_time = None  # When simulation completed
        self.simulation_count = 0  # Number of simulations run on this document
        
        # Model metadata
        self.model_name = None
        self.model_id = None
        self.num_places = 0
        self.num_transitions = 0
        self.num_arcs = 0
        
        # Analysis results
        self.species_metrics = []
        self.reaction_metrics = []
        
        # Simulation parameters
        self.last_time_step = None
        self.last_duration = None
        self.last_time_scale = None
    
    def capture_simulation_results(self, controller):
        """Capture simulation results from controller.
        
        Args:
            controller: SimulationController with completed simulation
        """
        if not controller or not hasattr(controller, 'data_collector'):
            return
        
        data_collector = controller.data_collector
        if not data_collector or not data_collector.has_data():
            return
        
        from datetime import datetime
        
        # Store timestamp
        self.last_simulation_time = datetime.now()
        self.simulation_count += 1
        
        # Capture simulation parameters for metadata
        time_step = None
        target_duration = None
        time_scale = None
        actual_duration = getattr(controller, 'time', 0)  # Actual elapsed simulation time
        
        if hasattr(controller, 'settings') and controller.settings:
            settings = controller.settings
            time_step = getattr(settings, 'time_step', None)
            target_duration = getattr(settings, 'duration', None)
            time_scale = getattr(settings, 'time_scale', None)
            self.last_time_step = time_step
            self.last_duration = target_duration
            self.last_time_scale = time_scale
        
        # Capture data collector state (make a snapshot)
        self.last_simulation_data = {
            'time_points': list(data_collector.time_points),
            'place_data': {k: list(v) for k, v in data_collector.place_data.items()},
            'transition_data': {k: list(v) for k, v in data_collector.transition_data.items()},
            'metadata': {
                'timestamp': self.last_simulation_time.strftime("%Y-%m-%d %H:%M:%S"),
                'time_step': time_step,
                'target_duration': target_duration,
                'duration': actual_duration,
                'time_scale': time_scale,
            }
        }
        
        # Capture model metadata
        if hasattr(controller, 'model') and controller.model:
            model = controller.model
            self.model_name = getattr(model, 'name', getattr(model, 'id', 'Untitled'))
            self.model_id = getattr(model, 'id', None)
            self.num_places = len(getattr(model, 'places', []))
            self.num_transitions = len(getattr(model, 'transitions', []))
            self.num_arcs = len(getattr(model, 'arcs', []))
    
    def has_simulation_data(self):
        """Check if this document has simulation data.
        
        Returns:
            bool: True if simulation data is available
        """
        return self.last_simulation_data is not None
    
    def get_summary(self):
        """Get summary text for this document's simulation.
        
        Returns:
            str: Summary text or None if no data
        """
        if not self.has_simulation_data():
            return None
        
        from datetime import datetime
        
        time_str = self.last_simulation_time.strftime("%Y-%m-%d %H:%M:%S") if self.last_simulation_time else "Unknown"
        
        data = self.last_simulation_data
        num_time_points = len(data['time_points'])
        
        # Calculate total firings
        total_firings = 0
        for firing_series in data['transition_data'].values():
            if firing_series:
                total_firings += firing_series[-1]
        
        return f"""<b>Simulation Summary</b>

<b>Date/Time:</b> {time_str}
<b>Model:</b> {self.model_name or 'Unknown'}
<b>Network Size:</b> {self.num_places} places, {self.num_transitions} transitions

<b>Simulation Count:</b> {self.simulation_count}
<b>Time Points:</b> {num_time_points}
<b>Total Firings:</b> {total_firings}"""
