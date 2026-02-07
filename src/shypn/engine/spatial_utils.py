#!/usr/bin/env python3
"""Spatial Signal Property Integration Utilities.

This module provides helper classes for transitions to read and use spatial
properties from connected signal places (Layer 1 of signal hierarchy).

Components:
    - BoundaryValidator: Check boundary crossing constraints
    - GradientModulator: Apply gradient-based rate modulation
    - VolumeAdaptiveSelector: Choose stochastic vs continuous based on volume
    - SpatialRateBuilder: Generate rate functions from spatial properties
"""

import math
from typing import Dict, Tuple, Optional, List, Any
from shypn.netobjs.place import BoundaryType


class BoundaryValidator:
    """Validates boundary crossing for spatial signal transport.
    
    Reads boundary_type and neighbor_compartments from places to determine
    if a transition can fire across compartment boundaries.
    
    Boundary Types:
        - PERMEABLE: Free diffusion, always allowed
        - SELECTIVE: Requires transition marked as transport + neighbor validation
        - IMPERMEABLE: Cannot cross boundary (same compartment only)
    
    Usage:
        validator = BoundaryValidator(model)
        can_cross, reason = validator.validate_crossing(
            source_place, target_place, transition
        )
    """
    
    def __init__(self, model):
        """Initialize validator with model context.
        
        Args:
            model: PetriNetModel instance for place access
        """
        self.model = model
    
    def validate_crossing(
        self,
        source_place,
        target_place,
        transition
    ) -> Tuple[bool, str]:
        """Validate if transition can transport signal across boundary.
        
        Args:
            source_place: Source Place object
            target_place: Target Place object
            transition: Transition object attempting crossing
        
        Returns:
            Tuple of (valid: bool, reason: str)
            - valid: True if crossing allowed, False otherwise
            - reason: Explanation ("valid-crossing", "boundary-impermeable", etc.)
        """
        # If source is not a spatial signal, no boundary constraints
        if not (hasattr(source_place, 'is_spatial_signal') and 
                source_place.is_spatial_signal()):
            return True, "not-spatial-signal"
        
        # Check boundary type
        boundary_type = getattr(source_place, 'boundary_type', None)
        
        # No boundary type set = assume permeable
        if boundary_type is None:
            return True, "boundary-not-set"
        
        # PERMEABLE: Always allow crossing
        if boundary_type == BoundaryType.PERMEABLE:
            return True, "boundary-permeable"
        
        # Check if same compartment (always allowed)
        source_compartment = getattr(source_place, 'module_id', None)
        target_compartment = getattr(target_place, 'module_id', None)
        
        if source_compartment == target_compartment:
            return True, "same-compartment"
        
        # IMPERMEABLE: Cannot cross to different compartment
        if boundary_type == BoundaryType.IMPERMEABLE:
            return False, "boundary-impermeable"
        
        # SELECTIVE: Requires transport transition AND neighbor validation
        if boundary_type == BoundaryType.SELECTIVE:
            # Check if transition is marked as transport
            is_transport = getattr(transition, 'is_transport', False)
            if not is_transport:
                return False, "boundary-requires-transport"
            
            # Check if target is in neighbor list
            if hasattr(source_place, 'is_neighbor'):
                if not source_place.is_neighbor(target_place.id):
                    return False, "not-neighbor-compartment"
            
            return True, "valid-selective-transport"
        
        # Unknown boundary type - default to permeable
        return True, "unknown-boundary-type"
    
    def validate_transition_arcs(
        self,
        transition,
        input_arcs: List,
        output_arcs: List,
        get_place_func
    ) -> Tuple[bool, str]:
        """Validate all arcs for a transition respect boundary constraints.
        
        Args:
            transition: Transition object
            input_arcs: List of input Arc objects
            output_arcs: List of output Arc objects
            get_place_func: Function to retrieve place by ID
        
        Returns:
            Tuple of (valid: bool, reason: str)
        """
        # Check all input → output combinations
        for input_arc in input_arcs:
            source_place = get_place_func(input_arc.source_id)
            if source_place is None:
                continue
            
            for output_arc in output_arcs:
                target_place = get_place_func(output_arc.target_id)
                if target_place is None:
                    continue
                
                # Validate this crossing
                valid, reason = self.validate_crossing(
                    source_place, target_place, transition
                )
                
                if not valid:
                    return False, f"{source_place.id}→{target_place.id}:{reason}"
        
        return True, "all-crossings-valid"


class GradientModulator:
    """Applies gradient-based rate modulation for spatial signals.
    
    Reads gradient_vector from source places and calculates alignment with
    transport direction to amplify (aligned) or attenuate (opposed) rates.
    
    Modulation Formula:
        rate_modulated = rate_base × (1.0 + alignment)
        where alignment ∈ [-1, 1] from dot product of gradient and direction
    
    Usage:
        modulator = GradientModulator()
        modulated_rate = modulator.apply_gradient(
            base_rate=5.0,
            source_place=place_A,
            target_place=place_B
        )
    """
    
    def __init__(self):
        """Initialize gradient modulator."""
        pass
    
    def apply_gradient(
        self,
        base_rate: float,
        source_place,
        target_place
    ) -> float:
        """Apply gradient-based modulation to rate.
        
        Args:
            base_rate: Base firing rate
            source_place: Source Place object
            target_place: Target Place object
        
        Returns:
            Modulated rate (base_rate × gradient_factor)
        """
        # Check if source has gradient vector
        if not hasattr(source_place, 'gradient_vector'):
            return base_rate
        
        gradient_vector = source_place.gradient_vector
        if gradient_vector is None:
            return base_rate
        
        gx, gy, gz = gradient_vector
        
        # Check if places have spatial positions
        if not (hasattr(source_place, 'spatial_position') and
                hasattr(target_place, 'spatial_position')):
            # No positions - can't calculate direction
            return base_rate
        
        source_pos = source_place.spatial_position
        target_pos = target_place.spatial_position
        
        if source_pos is None or target_pos is None:
            return base_rate
        
        # Calculate transport direction vector
        x1, y1, z1 = source_pos
        x2, y2, z2 = target_pos
        dx, dy, dz = x2 - x1, y2 - y1, z2 - z1
        
        # Normalize transport direction
        length = math.sqrt(dx*dx + dy*dy + dz*dz)
        if length < 1e-10:  # Same position
            return base_rate
        
        dx, dy, dz = dx/length, dy/length, dz/length
        
        # Calculate dot product (alignment)
        # Positive = aligned (amplify), negative = opposed (attenuate)
        alignment = gx*dx + gy*dy + gz*dz
        
        # Apply modulation: rate × (1.0 + alignment)
        # alignment = +1 → 2× amplification
        # alignment =  0 → 1× no change
        # alignment = -1 → 0× complete block
        modulation_factor = 1.0 + alignment
        
        return base_rate * max(0.0, modulation_factor)  # Ensure non-negative
    
    def get_gradient_magnitude(self, place) -> Optional[float]:
        """Get magnitude of gradient vector from place.
        
        Args:
            place: Place object
        
        Returns:
            Gradient magnitude or None if not set
        """
        if not hasattr(place, 'get_gradient_magnitude'):
            return None
        
        return place.get_gradient_magnitude()


class VolumeAdaptiveSelector:
    """Selects transition type based on compartment volume.
    
    Uses compartment_volume to decide if stochastic or continuous semantics
    are more appropriate. Small volumes require stochastic (discrete) dynamics,
    large volumes can use continuous (ODE) integration.
    
    Threshold (default): 1.0 fL (femtoliter)
    - Volume < threshold → Use stochastic
    - Volume ≥ threshold → Use continuous
    
    Usage:
        selector = VolumeAdaptiveSelector(threshold_fL=1.0)
        should_stochastic = selector.should_use_stochastic(place)
    """
    
    def __init__(self, threshold_fL: float = 1.0):
        """Initialize selector with volume threshold.
        
        Args:
            threshold_fL: Volume threshold in femtoliters (default 1.0 fL)
        """
        self.threshold_fL = threshold_fL
    
    def should_use_stochastic(self, place) -> bool:
        """Check if place volume suggests stochastic dynamics.
        
        Args:
            place: Place object
        
        Returns:
            True if should use stochastic, False for continuous
        """
        # Check compartment volume
        if not hasattr(place, 'compartment_volume') or place.compartment_volume is None:
            return False  # No volume set - default to continuous
        
        return place.compartment_volume < self.threshold_fL
    
    def analyze_transition(
        self,
        input_places: List,
        output_places: List
    ) -> Tuple[bool, Dict[str, Any]]:
        """Analyze all connected places and recommend transition type.
        
        Args:
            input_places: List of input Place objects
            output_places: List of output Place objects
        
        Returns:
            Tuple of (use_stochastic: bool, details: dict)
        """
        # Collect volumes from all places
        volumes = []
        
        for place in input_places + output_places:
            # Check compartment volume
            if hasattr(place, 'compartment_volume') and place.compartment_volume is not None:
                volumes.append(place.compartment_volume)
        
        if not volumes:
            # No volumes set - default to continuous
            return False, {
                'recommendation': 'continuous',
                'reason': 'no-volumes-set',
                'volumes': []
            }
        
        # Use minimum volume (most restrictive)
        min_volume = min(volumes)
        
        use_stochastic = min_volume < self.threshold_fL
        
        return use_stochastic, {
            'recommendation': 'stochastic' if use_stochastic else 'continuous',
            'reason': 'volume-based',
            'min_volume': min_volume,
            'threshold': self.threshold_fL,
            'volumes': volumes
        }


class SpatialRateBuilder:
    """Generates rate functions from spatial properties.
    
    Provides templates for common spatial phenomena:
    - Diffusion (Fick's first law)
    - Distance-dependent degradation
    - Gradient-driven flow
    
    Usage:
        builder = SpatialRateBuilder()
        rate_func = builder.build_diffusion_rate(
            source_place=place_A,
            target_place=place_B
        )
    """
    
    def __init__(self):
        """Initialize rate builder."""
        pass
    
    def build_diffusion_rate(
        self,
        source_place,
        target_place,
        base_rate: float = 1.0
    ) -> str:
        """Generate Fick's law diffusion rate formula.
        
        Formula: rate = D × |C_target - C_source| / distance²
        
        Args:
            source_place: Source Place object
            target_place: Target Place object
            base_rate: Multiplier for rate (default 1.0)
        
        Returns:
            Rate function string
        """
        # Get diffusion coefficient
        D = getattr(source_place, 'diffusion_coefficient', 1.0) or 1.0
        
        # Get distance
        if hasattr(source_place, 'get_spatial_distance'):
            distance = source_place.get_spatial_distance(target_place)
            if distance is None:
                distance = 1.0
        else:
            distance = 1.0
        
        # Build formula
        source_id = source_place.id
        target_id = target_place.id
        
        formula = f"{D * base_rate / (distance ** 2)} * abs({target_id} - {source_id})"
        
        return formula
    
    def build_gradient_flow_rate(
        self,
        source_place,
        target_place,
        base_rate: float = 1.0
    ) -> str:
        """Generate gradient-driven flow rate formula.
        
        Args:
            source_place: Source Place object with gradient_vector
            target_place: Target Place object
            base_rate: Base flow rate
        
        Returns:
            Rate function string
        """
        # Get gradient magnitude
        if hasattr(source_place, 'get_gradient_magnitude'):
            gradient_mag = source_place.get_gradient_magnitude() or 1.0
        else:
            gradient_mag = 1.0
        
        source_id = source_place.id
        target_id = target_place.id
        
        formula = f"{base_rate * gradient_mag} * ({source_id} - {target_id})"
        
        return formula
    
    def build_distance_decay_rate(
        self,
        source_place,
        target_place,
        base_rate: float = 1.0,
        decay_constant: float = 1.0
    ) -> str:
        """Generate distance-dependent decay rate.
        
        Formula: rate = base_rate × exp(-decay_constant × distance)
        
        Args:
            source_place: Source Place object
            target_place: Target Place object
            base_rate: Base decay rate
            decay_constant: Exponential decay constant (1/μm)
        
        Returns:
            Rate function string
        """
        # Get distance
        if hasattr(source_place, 'get_spatial_distance'):
            distance = source_place.get_spatial_distance(target_place)
            if distance is None:
                distance = 0.0
        else:
            distance = 0.0
        
        decay_factor = math.exp(-decay_constant * distance)
        
        formula = f"{base_rate * decay_factor} * {source_place.id}"
        
        return formula
