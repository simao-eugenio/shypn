"""
Temporal metadata section.

Tracks timing information for sweep and individual experiments.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from .base import MetadataSection


class TemporalMetadata(MetadataSection):
    """Metadata about execution timing."""
    
    def __init__(self):
        super().__init__("Temporal Metadata")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect timing information from context.
        
        Expected context keys:
            - sweep_start_time: datetime
            - experiment_start_time: datetime
            - experiment_end_time: datetime (if completed)
            - elapsed_time: float (seconds)
        """
        sweep_start = context.get('sweep_start_time')
        if sweep_start:
            self.add_field('Sweep_Start_Time', sweep_start)
        
        exp_start = context.get('experiment_start_time')
        if exp_start:
            self.add_field('Experiment_Start_Time', exp_start)
        
        exp_end = context.get('experiment_end_time')
        if exp_end:
            self.add_field('Experiment_End_Time', exp_end)
        
        elapsed = context.get('elapsed_time')
        if elapsed is not None:
            self.add_field('Elapsed_Time', f"{elapsed:.3f} seconds")
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate temporal metadata."""
        # Check timing consistency
        start = self.get_field('Experiment_Start_Time')
        end = self.get_field('Experiment_End_Time')
        
        if start and end:
            if isinstance(start, datetime) and isinstance(end, datetime):
                if end < start:
                    return False, "End time before start time"
        
        return True, None


class ReferenceMetadata(MetadataSection):
    """Metadata containing references to related documentation and analyses."""
    
    def __init__(self):
        super().__init__("References")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect reference information from context.
        
        Expected context keys:
            - phase: Phase identifier
            - documentation: Path to related documentation
            - related_analysis: Path to analysis file
            - manuscript_reference: Citation or path
        """
        phase = context.get('phase')
        if phase:
            self.add_field('Phase', phase)
        
        docs = context.get('documentation')
        if docs:
            self.add_field('Documentation', docs)
        
        analysis = context.get('related_analysis')
        if analysis:
            self.add_field('Related_Analysis', analysis)
        
        manuscript = context.get('manuscript_reference')
        if manuscript:
            self.add_field('Manuscript_Reference', manuscript)
        
        # Add project context
        project = context.get('project_name')
        if project:
            self.add_field('Project', project)
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate references."""
        return True, None
