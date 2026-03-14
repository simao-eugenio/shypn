#!/usr/bin/env python3
"""Kinetic Parameter Unit Converter.

Handles unit validation and conversion for kinetic parameters from different sources
(SABIO-RK, BRENDA, KEGG heuristics) to ensure consistency.

Standard Units (SI-like):
- Km: mM (millimolar)
- Vmax: mM/s (millimolar per second)
- Kcat: s⁻¹ (per second)
- Ki: mM (millimolar)
"""

import re
import logging
from typing import Tuple


class KineticUnitConverter:
    """Converter for kinetic parameter units.
    
    Standardizes units across different data sources to prevent scaling errors.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Standard target units
        self.STANDARD_UNITS = {
            'Km': 'mM',
            'Ki': 'mM',
            'Vmax': 'mM/s',
            'Kcat': 's^-1'
        }
        
        # Conversion factors to standard units
        # Format: {from_unit: (multiplier, standard_unit)}
        self.CONCENTRATION_CONVERSIONS = {
            # To mM (millimolar)
            'M': (1000.0, 'mM'),
            'mol/l': (1000.0, 'mM'),
            'mol/L': (1000.0, 'mM'),
            'mM': (1.0, 'mM'),
            'mmol/l': (1.0, 'mM'),
            'mmol/L': (1.0, 'mM'),
            'µM': (0.001, 'mM'),
            'uM': (0.001, 'mM'),
            'micromol/l': (0.001, 'mM'),
            'μM': (0.001, 'mM'),
            'µmol/l': (0.001, 'mM'),
            'umol/l': (0.001, 'mM'),
            'nM': (0.000001, 'mM'),
            'nmol/l': (0.000001, 'mM'),
            'nmol/L': (0.000001, 'mM'),
            # Alternative notations
            'mol': (1000.0, 'mM'),  # Assume /L
            'mmol': (1.0, 'mM'),
            'umol': (0.001, 'mM'),
            'µmol': (0.001, 'mM'),
        }
        
        self.TIME_CONVERSIONS = {
            # To seconds
            's': (1.0, 's'),
            'sec': (1.0, 's'),
            'second': (1.0, 's'),
            'min': (60.0, 's'),
            'minute': (60.0, 's'),
            'h': (3600.0, 's'),
            'hr': (3600.0, 's'),
            'hour': (3600.0, 's'),
        }
        
        self.RATE_CONVERSIONS = {
            # To s^-1
            's^-1': (1.0, 's^-1'),
            's-1': (1.0, 's^-1'),
            's^(-1)': (1.0, 's^-1'),
            '1/s': (1.0, 's^-1'),
            'per s': (1.0, 's^-1'),
            '/s': (1.0, 's^-1'),
            'min^-1': (1.0/60.0, 's^-1'),
            'min-1': (1.0/60.0, 's^-1'),
            'min^(-1)': (1.0/60.0, 's^-1'),
            '1/min': (1.0/60.0, 's^-1'),
            'per min': (1.0/60.0, 's^-1'),
            '/min': (1.0/60.0, 's^-1'),
        }
    
    def normalize_unit_string(self, unit: str) -> str:
        """Normalize unit string for comparison.
        
        Args:
            unit: Raw unit string
        
        Returns:
            Normalized unit string (lowercase, stripped)
        """
        if not unit:
            return ''
        
        import re
        
        # Strip whitespace from ends, convert to lowercase
        normalized = unit.strip().lower()
        
        # Handle special Unicode characters that SABIO-RK might use
        # Replace various superscript minus signs with standard forms
        normalized = normalized.replace('⁻', '-')  # Unicode superscript minus
        normalized = normalized.replace('−', '-')  # Unicode minus sign
        
        # Normalize multiplication/product signs
        normalized = normalized.replace('*', '')  # Remove * (e.g., mol*s^-1)
        normalized = normalized.replace('·', '')  # Remove middle dot
        normalized = normalized.replace('.', '')  # Remove dot (e.g., mol.s-1)
        
        # Remove spaces only around operators, keep spaces in words
        normalized = re.sub(r'\s*/\s*', '/', normalized)  # Clean up around /
        normalized = re.sub(r'\s*\^\s*', '^', normalized)  # Clean up around ^
        normalized = re.sub(r'\s+-\s*', '-', normalized)  # Clean up around -
        
        # Remove remaining spaces
        normalized = normalized.replace(' ', '')
        
        return normalized
    
    def convert_parameter(self, param_type: str, value: float, units: str, 
                         source: str = 'unknown') -> Tuple[float, str, bool]:
        """Convert parameter value to standard units.
        
        Args:
            param_type: Parameter type (Km, Vmax, Kcat, Ki)
            value: Parameter value
            units: Original units
            source: Data source (for logging)
        
        Returns:
            Tuple of (converted_value, standard_units, needs_warning)
        """
        if not units:
            self.logger.warning(f"[Units] {param_type} from {source} has no units - assuming standard")
            return (value, self.STANDARD_UNITS.get(param_type, ''), True)
        
        normalized_units = self.normalize_unit_string(units)
        standard_unit = self.STANDARD_UNITS.get(param_type, '')
        needs_warning = False
        
        # Km, Ki - concentration units
        if param_type in ['Km', 'Ki']:
            if normalized_units in self.CONCENTRATION_CONVERSIONS:
                multiplier, std_unit = self.CONCENTRATION_CONVERSIONS[normalized_units]
                converted_value = value * multiplier
                self.logger.info(f"[Units] {param_type}: {value} {units} → {converted_value} {std_unit}")
                return (converted_value, std_unit, False)
            else:
                self.logger.warning(f"[Units] Unknown concentration unit '{units}' for {param_type} from {source}")
                needs_warning = True
        
        # Kcat - rate constant (1/time)
        elif param_type == 'Kcat':
            if normalized_units in self.RATE_CONVERSIONS:
                multiplier, std_unit = self.RATE_CONVERSIONS[normalized_units]
                converted_value = value * multiplier
                self.logger.info(f"[Units] {param_type}: {value} {units} → {converted_value} {std_unit}")
                return (converted_value, std_unit, False)
            else:
                self.logger.warning(f"[Units] Unknown rate unit '{units}' for {param_type} from {source}")
                needs_warning = True
        
        # Vmax - concentration/time
        elif param_type == 'Vmax':
            # Parse compound units like "mM/s", "µM/min", "µmol/min/mg"
            match = re.match(r'([^/]+)/(.+)', normalized_units)
            if match:
                conc_unit, rest = match.groups()
                
                # Handle enzyme-specific units like "µmol/min/mg" or "µM/min/mg protein"
                # These need scaling since they're per mg of enzyme
                enzyme_specific = False
                if '/mg' in rest or 'protein' in rest:
                    enzyme_specific = True
                    # Extract just the time unit
                    time_part = rest.split('/')[0]
                    time_unit = time_part.strip()
                else:
                    time_unit = rest.strip()
                
                # Convert concentration part
                conc_multiplier = 1.0
                if conc_unit in self.CONCENTRATION_CONVERSIONS:
                    conc_multiplier, _ = self.CONCENTRATION_CONVERSIONS[conc_unit]
                elif 'µmol' in conc_unit or 'umol' in conc_unit or 'micromol' in conc_unit:
                    conc_multiplier = 0.001  # µmol/L = 0.001 mM
                elif 'nmol' in conc_unit:
                    conc_multiplier = 0.000001  # nmol/L = 0.000001 mM
                else:
                    self.logger.warning(f"[Units] Unknown concentration unit '{conc_unit}' in Vmax")
                    needs_warning = True
                
                # Convert time part
                time_multiplier = 1.0
                if time_unit in self.TIME_CONVERSIONS:
                    time_multiplier, _ = self.TIME_CONVERSIONS[time_unit]
                else:
                    self.logger.warning(f"[Units] Unknown time unit '{time_unit}' in Vmax")
                    needs_warning = True
                
                # Combined conversion
                total_multiplier = conc_multiplier / time_multiplier
                converted_value = value * total_multiplier
                
                # For enzyme-specific units, apply a scaling factor to make them comparable
                # Typical enzyme concentration in vivo is ~0.1-1 µM, so scale by ~1000-10000
                if enzyme_specific:
                    scale_factor = 1000.0  # Assume ~1 µM enzyme concentration
                    converted_value = converted_value * scale_factor
                    self.logger.info(f"[Units] Vmax: {value} {units} → {converted_value} mM/s (scaled for enzyme conc)")
                    warning_msg = f"⚠️  Vmax from {source}: Enzyme-specific units '{units}' scaled by {scale_factor}x assuming ~1µM enzyme"
                    return (converted_value, 'mM/s', True)
                else:
                    self.logger.info(f"[Units] Vmax: {value} {units} → {converted_value} mM/s")
                    return (converted_value, 'mM/s', needs_warning)
            else:
                self.logger.warning(f"[Units] Cannot parse Vmax unit '{units}' from {source}")
                needs_warning = True
        
        # If we get here, couldn't convert - return original with warning
        return (value, units, needs_warning)
    
    def validate_parameter_units(self, param_type: str, value: float, units: str, 
                                 source: str) -> Tuple[float, str, str]:
        """Validate and convert parameter units with detailed feedback.
        
        Args:
            param_type: Parameter type
            value: Parameter value
            units: Original units
            source: Data source
        
        Returns:
            Tuple of (converted_value, converted_units, warning_message)
        """
        converted_value, converted_units, needs_warning = self.convert_parameter(
            param_type, value, units, source
        )
        
        warning_msg = ""
        if needs_warning:
            warning_msg = (f"⚠️  {param_type} from {source}: Unit '{units}' may need manual verification. "
                          f"Using value as-is: {value} {units}")
        
        return (converted_value, converted_units, warning_msg)


# Global converter instance
_converter = None

def get_unit_converter() -> KineticUnitConverter:
    """Get global unit converter instance."""
    global _converter
    if _converter is None:
        _converter = KineticUnitConverter()
    return _converter
