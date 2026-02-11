#!/usr/bin/env python3
"""
Property managers for netobjects.

Business logic layer for property editing:
- Property validation
- Value transformations
- Computed properties
- Change tracking

Separates business logic from UI (testable without GTK).
"""

import logging
from typing import Dict, Any, Tuple, List, Callable, Optional

logger = logging.getLogger(__name__)


class PropertyManager:
    """Base class for managing netobject properties.
    
    Encapsulates business logic:
    - Property validation
    - Value transformations
    - Computed properties
    - Change tracking
    
    Subclasses implement:
    - get_all_properties(): Return dict of all properties
    - _create_validators(): Return dict of validator functions
    - _apply_updates(): Apply validated changes to netobject
    """
    
    def __init__(self, netobject):
        """Initialize property manager.
        
        Args:
            netobject: Place, Transition, or Arc object
        """
        self.netobject = netobject
        self.validators = self._create_validators()
        self.original_values: Optional[Dict[str, Any]] = None
    
    def get_all_properties(self) -> Dict[str, Any]:
        """Get all properties as dict for UI population.
        
        Must be implemented by subclasses.
        
        Returns:
            Dictionary of property_name -> value
        """
        raise NotImplementedError("Subclasses must implement get_all_properties()")
    
    def update_properties(self, data: Dict[str, Any]) -> None:
        """Update netobject from validated data dict.
        
        Args:
            data: Dictionary of property_name -> new_value
            
        Raises:
            ValueError: If validation fails
        """
        # Validate first
        is_valid, errors = self.validate_properties(data)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise ValueError(f"Invalid properties:\n{error_msg}")
        
        # Apply updates
        self._apply_updates(data)
        
        logger.debug(f"Updated {type(self.netobject).__name__} properties: {list(data.keys())}")
    
    def validate_properties(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate property values.
        
        Args:
            data: Dictionary of property_name -> value
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        for key, value in data.items():
            if key in self.validators:
                validator = self.validators[key]
                is_valid, error = validator(value)
                if not is_valid:
                    errors.append(f"{key}: {error}")
        
        return (len(errors) == 0, errors)
    
    def _create_validators(self) -> Dict[str, Callable]:
        """Create validator functions for each property.
        
        Must be implemented by subclasses.
        
        Returns:
            Dictionary of property_name -> validator_function
            
        Validator function signature:
            (value: Any) -> Tuple[bool, str]
            Returns (is_valid, error_message)
        """
        raise NotImplementedError("Subclasses must implement _create_validators()")
    
    def _apply_updates(self, data: Dict[str, Any]) -> None:
        """Apply validated updates to netobject.
        
        Must be implemented by subclasses.
        
        Args:
            data: Validated dictionary of property_name -> new_value
        """
        raise NotImplementedError("Subclasses must implement _apply_updates()")
    
    def snapshot(self) -> None:
        """Save current property values for change tracking."""
        self.original_values = self.get_all_properties().copy()
    
    def has_changes(self) -> bool:
        """Check if properties have changed since snapshot.
        
        Returns:
            True if any property changed
        """
        if self.original_values is None:
            return False
        
        current = self.get_all_properties()
        
        for key, original_value in self.original_values.items():
            if key in current and current[key] != original_value:
                return True
        
        return False
    
    def get_changes(self) -> Dict[str, Tuple[Any, Any]]:
        """Get changed properties.
        
        Returns:
            Dictionary of property_name -> (old_value, new_value)
        """
        if self.original_values is None:
            return {}
        
        changes = {}
        current = self.get_all_properties()
        
        for key, original_value in self.original_values.items():
            if key in current:
                new_value = current[key]
                if new_value != original_value:
                    changes[key] = (original_value, new_value)
        
        return changes


class PlacePropertyManager(PropertyManager):
    """Property manager for Place objects.
    
    Handles:
    - Basic properties (position, size, marking)
    - Signal place properties
    - Spatial properties (compartment, diffusion, etc.)
    - Color management (semantic vs custom)
    """
    
    def get_all_properties(self) -> Dict[str, Any]:
        """Get all Place properties.
        
        Returns:
            Dictionary of all Place properties
        """
        return {
            # Identity
            'id': self.netobject.id,
            'name': self.netobject.name,
            'label': self.netobject.label or '',
            
            # Position (not editable in dialog, but included for completeness)
            'x': self.netobject.x,
            'y': self.netobject.y,
            
            # Appearance
            'radius': self.netobject.radius,
            'border_color': self.netobject.border_color,
            'border_width': self.netobject.border_width,
            
            # Marking
            'tokens': self.netobject.tokens,
            'initial_marking': self.netobject.initial_marking,
            'capacity': self.netobject.capacity,
            
            # Signal place properties (13-tuple Bio-PN: Ψ)
            'is_signal_place': self.netobject.is_signal_place,
            'signal_type': self.netobject.signal_type,
            
            # Compartment properties
            'is_compartment_place': self.netobject.is_compartment_place,
            'is_regulatory_place': self.netobject.is_regulatory_place,
            
            # Spatial properties (Layer 1)
            'compartment_volume': self.netobject.compartment_volume,
            'diffusion_coefficient': self.netobject.diffusion_coefficient,
            'boundary_type': self.netobject.boundary_type,
            'module_id': self.netobject.module_id,
            'gradient_vector': self.netobject.gradient_vector,
            'spatial_position': self.netobject.spatial_position,
            'neighbor_compartments': self.netobject.neighbor_compartments,
        }
    
    def _create_validators(self) -> Dict[str, Callable]:
        """Create validators for Place properties.
        
        Returns:
            Dictionary of property_name -> validator_function
        """
        return {
            'radius': lambda r: (r > 0, "Radius must be positive"),
            'tokens': lambda t: (t >= 0, "Tokens cannot be negative"),
            'initial_marking': lambda m: (m >= 0, "Initial marking cannot be negative"),
            'capacity': self._validate_capacity,
            'border_width': lambda w: (w >= 0.5, "Border width must be >= 0.5"),
            'compartment_volume': lambda v: (v is None or v > 0, "Volume must be positive"),
            'diffusion_coefficient': lambda d: (d is None or d >= 0, "Diffusion coefficient must be non-negative"),
        }
    
    def _validate_capacity(self, capacity: float) -> Tuple[bool, str]:
        """Validate capacity value.
        
        Args:
            capacity: Capacity value
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if capacity == float('inf'):
            return (True, "")
        
        if capacity <= 0:
            return (False, "Capacity must be positive or infinite")
        
        return (True, "")
    
    def _apply_updates(self, data: Dict[str, Any]) -> None:
        """Apply validated updates to Place object.
        
        Args:
            data: Validated property updates
        """
        # Apply simple attribute updates
        for key, value in data.items():
            if hasattr(self.netobject, key):
                setattr(self.netobject, key, value)
        
        # Handle special cases
        
        # Sync initial_marking with tokens if tokens changed
        if 'tokens' in data and 'initial_marking' not in data:
            self.netobject.initial_marking = data['tokens']
        
        # Update color schema if signal place status changed
        if 'is_signal_place' in data or 'signal_type' in data:
            from shypn.utils.color_schema_manager import ColorSchemaManager
            if self.netobject.is_signal_place:
                ColorSchemaManager.reset_place_color(self.netobject)
        
        # Update compartment place flag if compartment_volume is set
        if 'compartment_volume' in data:
            if data['compartment_volume'] is not None and data['compartment_volume'] > 0:
                # Has compartment volume -> could be compartment place
                # But don't override if explicitly set
                pass


class TransitionPropertyManager(PropertyManager):
    """Property manager for Transition objects.
    
    Handles:
    - Basic properties (type, rate, guard, priority)
    - Rate functions and expressions
    - Source/sink markers
    - Signal dependencies (quorum sensing)
    - Adaptive properties
    - Timed transition windows
    """
    
    def get_all_properties(self) -> Dict[str, Any]:
        """Get all Transition properties.
        
        Returns:
            Dictionary of all Transition properties
        """
        return {
            # Identity
            'id': self.netobject.id,
            'name': self.netobject.name,
            'label': self.netobject.label or '',
            
            # Position (not editable in dialog)
            'x': self.netobject.x,
            'y': self.netobject.y,
            'width': self.netobject.width,
            'height': self.netobject.height,
            'horizontal': self.netobject.horizontal,
            
            # Appearance
            'border_color': self.netobject.border_color,
            'border_width': self.netobject.border_width,
            'fill_color': self.netobject.fill_color,
            
            # Behavior
            'transition_type': self.netobject.transition_type,
            'enabled': self.netobject.enabled,
            'firing_policy': self.netobject.firing_policy,
            'priority': self.netobject.priority,
            
            # Rates and functions
            'rate': self.netobject.rate,
            'rate_function': self.netobject.rate_function,
            'rate_forward': self.netobject.rate_forward,
            'rate_reverse': self.netobject.rate_reverse,
            'guard': self.netobject.guard,
            
            # Source/Sink
            'is_source': self.netobject.is_source,
            'is_sink': self.netobject.is_sink,
            
            # Signal dependencies (13-tuple: Ψ)
            'signal_places': getattr(self.netobject, 'signal_places', []),
            'is_environment_aware': getattr(self.netobject, 'is_environment_aware', False),
            
            # Module
            'module_id': getattr(self.netobject, 'module_id', None),
            
            # Timed transition window
            'earliest_time': getattr(self.netobject, 'earliest_time', None),
            'latest_time': getattr(self.netobject, 'latest_time', None),
            
            # Adaptive properties (from properties dict)
            'adaptive_filter': self.netobject.properties.get('adaptive_filter', 'inputs_only'),
            'volume_threshold': self.netobject.properties.get('volume_threshold', 1.0),
        }
    
    def _create_validators(self) -> Dict[str, Callable]:
        """Create validators for Transition properties.
        
        Returns:
            Dictionary of property_name -> validator_function
        """
        return {
            'rate': lambda r: (r > 0, "Rate must be positive"),
            'rate_function': self._validate_rate_function,
            'guard': self._validate_guard_expression,
            'priority': lambda p: (p >= 0, "Priority must be non-negative"),
            'earliest_time': lambda t: (t is None or t >= 0, "Earliest time must be non-negative"),
            'latest_time': self._validate_latest_time,
            'border_width': lambda w: (w >= 0.5, "Border width must be >= 0.5"),
            'width': lambda w: (w > 0, "Width must be positive"),
            'height': lambda h: (h > 0, "Height must be positive"),
        }
    
    def _validate_rate_function(self, expr: Optional[str]) -> Tuple[bool, str]:
        """Validate rate function expression.
        
        Args:
            expr: Rate function expression
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Continuous and adaptive transitions require rate functions
        if not expr and self.netobject.transition_type in ['continuous', 'adaptive']:
            return (False, f"{self.netobject.transition_type} transitions require a rate function")
        
        # Empty is OK for other types
        if not expr:
            return (True, "")
        
        # Use existing expression validator
        try:
            from shypn.data.validation import ExpressionValidator
            validator = ExpressionValidator()
            return validator.validate(expr)
        except ImportError:
            # Fallback: basic check
            return (True, "")
    
    def _validate_guard_expression(self, expr: Optional[str]) -> Tuple[bool, str]:
        """Validate guard expression.
        
        Args:
            expr: Guard expression
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Guards can be empty (defaults to 1 = always enabled)
        if not expr:
            return (True, "")
        
        try:
            from shypn.data.validation import ExpressionValidator
            validator = ExpressionValidator()
            return validator.validate(expr)
        except ImportError:
            return (True, "")
    
    def _validate_latest_time(self, latest: Optional[float]) -> Tuple[bool, str]:
        """Validate latest time is after earliest time.
        
        Args:
            latest: Latest firing time
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if latest is None:
            return (True, "")
        
        earliest = getattr(self.netobject, 'earliest_time', None)
        if earliest is not None and latest < earliest:
            return (False, "Latest time must be >= earliest time")
        
        return (True, "")
    
    def _apply_updates(self, data: Dict[str, Any]) -> None:
        """Apply validated updates to Transition object.
        
        Args:
            data: Validated property updates
        """
        # Apply simple attribute updates
        for key, value in data.items():
            # Handle properties dict specially
            if key in ['adaptive_filter', 'volume_threshold']:
                self.netobject.properties[key] = value
            elif hasattr(self.netobject, key):
                setattr(self.netobject, key, value)
        
        # Handle special cases
        
        # Update is_environment_aware based on signal_places
        if 'signal_places' in data:
            self.netobject.is_environment_aware = len(data['signal_places']) > 0


class ArcPropertyManager(PropertyManager):
    """Property manager for Arc objects.
    
    Handles:
    - Arc type (normal, inhibitor, test, etc.)
    - Weight and threshold
    - Visual properties
    """
    
    def get_all_properties(self) -> Dict[str, Any]:
        """Get all Arc properties.
        
        Returns:
            Dictionary of all Arc properties
        """
        return {
            'id': self.netobject.id,
            'name': self.netobject.name,
            'arc_type': getattr(self.netobject, 'arc_type', 'normal'),
            'weight': self.netobject.weight,
            'threshold': self.netobject.threshold,
            'color': self.netobject.color,
            'width': self.netobject.width,
        }
    
    def _create_validators(self) -> Dict[str, Callable]:
        """Create validators for Arc properties.
        
        Returns:
            Dictionary of property_name -> validator_function
        """
        return {
            'weight': lambda w: (w > 0, "Weight must be positive"),
            'threshold': lambda t: (t >= 0, "Threshold must be non-negative"),
            'width': lambda w: (w > 0, "Width must be positive"),
        }
    
    def _apply_updates(self, data: Dict[str, Any]) -> None:
        """Apply validated updates to Arc object.
        
        Args:
            data: Validated property updates
        """
        for key, value in data.items():
            if hasattr(self.netobject, key):
                setattr(self.netobject, key, value)
