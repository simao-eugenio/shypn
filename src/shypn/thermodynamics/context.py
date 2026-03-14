"""Thermodynamic Context - Environmental conditions for biochemical reactions.

This module defines dataclasses for thermodynamic properties that can be:
1. Static (document-level settings)
2. Dynamic (spatial places that change during simulation)
3. Compartment-specific (different pH in lysosome vs cytoplasm)

Architecture:
- Classes define properties (single source of truth)
- Automatic serialization via dataclass fields
- No duplicate definitions in JSON
- Type-safe with validation

Author: SHYPN Core Team
Date: February 14, 2026
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List
from enum import Enum


class ThermodynamicSource(Enum):
    """Source of thermodynamic property values."""
    DEFAULT = "default"          # Hard-coded defaults (pH 7.0, 298.15 K)
    DOCUMENT = "document"        # Document-level static settings
    PLACE = "place"              # Dynamic spatial place (e.g., pH_cytoplasm)
    COMPARTMENT = "compartment"  # Compartment-specific override
    CALCULATED = "calculated"    # Computed from other properties


@dataclass
class ThermodynamicContext:
    """Environmental conditions for biochemical reactions.
    
    This class represents the thermodynamic state at a specific location
    in the model (compartment, place, or global). Values can come from:
    - Static document settings (default)
    - Dynamic spatial places (preferred)
    - Compartment-specific overrides
    
    All properties are stored in class attributes (single source of truth).
    Serialization to JSON happens automatically via asdict().
    
    Attributes:
        ph: pH value (0-14, typically 6-8 for cells)
        temperature: Temperature in Kelvin (273-400 K typical)
        temperature_celsius: Convenience property (auto-calculated)
        ionic_strength: Ionic strength in mol/L (0.05-0.25 M typical)
        pressure: Pressure in atmospheres (default 1.0 atm)
        compartment: Optional compartment name (e.g., "cytoplasm", "lysosome")
        source: Where values came from (for debugging)
        place_names: Names of places used for dynamic lookup
    
    Physical constants (read-only):
        R: Gas constant 0.008314 kJ/(mol·K)
        R_SI: Gas constant 8.314 J/(mol·K)
        F: Faraday constant 96485 C/mol
    
    Examples:
        # Static context from document
        ctx = ThermodynamicContext(ph=7.4, temperature=310.15, source=ThermodynamicSource.DOCUMENT)
        
        # Dynamic context from places
        ctx = ThermodynamicContext.from_places(model, compartment="cytoplasm")
        
        # Lysosomal context (acidic)
        ctx = ThermodynamicContext(ph=5.0, compartment="lysosome", source=ThermodynamicSource.PLACE)
    """
    
    # Core thermodynamic properties
    ph: float = 7.0
    temperature: float = 298.15  # Kelvin
    ionic_strength: float = 0.1  # mol/L
    pressure: float = 1.0  # atmospheres
    
    # Metadata
    compartment: Optional[str] = None
    source: ThermodynamicSource = ThermodynamicSource.DEFAULT
    place_names: Dict[str, str] = field(default_factory=dict)  # {property: place_name}
    
    # Physical constants (class-level, not serialized)
    R: float = field(default=0.008314, init=False, repr=False)  # kJ/(mol·K)
    R_SI: float = field(default=8.314, init=False, repr=False)  # J/(mol·K)
    F: float = field(default=96485, init=False, repr=False)  # Faraday constant, C/mol
    
    def __post_init__(self):
        """Validate thermodynamic properties after initialization."""
        # Validate pH range
        if not (0 <= self.ph <= 14):
            raise ValueError(f"pH must be between 0 and 14, got {self.ph}")
        
        # Validate temperature (absolute zero to extreme thermophiles)
        if not (0 < self.temperature <= 500):
            raise ValueError(f"Temperature must be between 0 and 500 K, got {self.temperature}")
        
        # Validate ionic strength (cannot be negative)
        if self.ionic_strength < 0:
            raise ValueError(f"Ionic strength must be non-negative, got {self.ionic_strength}")
        
        # Validate pressure (cannot be negative)
        if self.pressure < 0:
            raise ValueError(f"Pressure must be non-negative, got {self.pressure}")
    
    @property
    def temperature_celsius(self) -> float:
        """Get temperature in Celsius.
        
        Returns:
            float: Temperature in degrees Celsius
        """
        return self.temperature - 273.15
    
    @temperature_celsius.setter
    def temperature_celsius(self, value: float):
        """Set temperature from Celsius value.
        
        Args:
            value: Temperature in degrees Celsius
        """
        self.temperature = value + 273.15
    
    @property
    def RT(self) -> float:
        """Get RT (gas constant × temperature) in kJ/mol.
        
        Commonly used in thermodynamic equations:
        - ΔG = ΔG° + RT·ln(Q)
        - K_eq = exp(-ΔG°/RT)
        
        Returns:
            float: RT in kJ/mol (typically ~2.48 at 298 K)
        """
        return self.R * self.temperature
    
    @property
    def RT_SI(self) -> float:
        """Get RT (gas constant × temperature) in J/mol.
        
        Returns:
            float: RT in J/mol (typically ~2480 at 298 K)
        """
        return self.R_SI * self.temperature
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON persistence.
        
        This is automatic - dataclass fields become dict keys.
        Only serializes stored values, not computed properties.
        
        Returns:
            dict: Serializable dictionary
        """
        data = asdict(self)
        
        # Remove computed constants (marked with init=False)
        # These are physical constants, not state to be serialized
        for key in ['R', 'R_SI', 'F']:
            data.pop(key, None)
        # Convert enum to string for JSON compatibility
        data['source'] = self.source.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThermodynamicContext':
        """Deserialize from dictionary (load from JSON).
        
        Args:
            data: Dictionary with thermodynamic properties
        
        Returns:
            ThermodynamicContext: Reconstructed context
        """
        # Convert source string back to enum
        if 'source' in data and isinstance(data['source'], str):
            data['source'] = ThermodynamicSource(data['source'])
        
        # Handle missing fields with defaults
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    @classmethod
    def from_document_settings(cls, document) -> 'ThermodynamicContext':
        """Create context from document static settings.
        
        Args:
            document: DocumentModel instance
        
        Returns:
            ThermodynamicContext: Context with document settings
        """
        settings = document.thermodynamic_settings
        return cls(
            ph=settings.get('ph', 7.0),
            temperature=settings.get('temperature', 298.15),
            ionic_strength=settings.get('ionic_strength', 0.1),
            source=ThermodynamicSource.DOCUMENT
        )
    
    @classmethod
    def from_places(cls, model, compartment: Optional[str] = None) -> 'ThermodynamicContext':
        """Create context from spatial places (DYNAMIC lookup).
        
        This is the preferred method for simulation-time thermodynamics.
        It reads current token values from places with special names:
        - "pH" or "pH_{compartment}" or "pH_global"
        - "Temperature" or "Temperature_{compartment}"
        - "IonicStrength" or "I_{compartment}"
        
        Priority order:
        1. Compartment-specific place (e.g., "pH_lysosome")
        2. Generic property place (e.g., "pH")
        3. Global place (e.g., "pH_global")
        4. Document settings
        5. Hard-coded defaults
        
        Args:
            model: PetriNet or DocumentModel with places
            compartment: Optional compartment name for scoped lookup
        
        Returns:
            ThermodynamicContext: Context with values from places
        
        Examples:
            # Generic lookup (uses "pH", "Temperature" places)
            ctx = ThermodynamicContext.from_places(model)
            
            # Compartment-specific (uses "pH_lysosome", etc.)
            ctx = ThermodynamicContext.from_places(model, compartment="lysosome")
        """
        # Build place lookup dict: label → tokens (use label, not internal name)
        places_dict = {}
        if hasattr(model, 'places'):
            # Use place.label (user-assigned like "pH") not place.name (system like "P1")
            places_dict = {place.label: place.tokens for place in model.places if place.label}
        elif hasattr(model, 'marking'):  # PetriNet interface
            places_dict = {place.label: place.tokens for place in model.marking if place.label}
        
        place_names = {}  # Track which places we used
        
        # Helper to find place with priority order
        def find_place_value(base_names: List[str], default: float) -> tuple:
            """Find place value with priority: compartment > generic > global."""
            # Try compartment-specific first
            if compartment:
                for base_name in base_names:
                    comp_name = f"{base_name}_{compartment}"
                    if comp_name in places_dict:
                        return places_dict[comp_name], comp_name
            
            # Try generic names
            for base_name in base_names:
                if base_name in places_dict:
                    return places_dict[base_name], base_name
            
            # Try global suffix
            for base_name in base_names:
                global_name = f"{base_name}_global"
                if global_name in places_dict:
                    return places_dict[global_name], global_name
            
            # Fall back to document/default
            return default, None
        
        # Get document defaults as fallback
        doc_settings = {}
        if hasattr(model, 'thermodynamic_settings'):
            doc_settings = model.thermodynamic_settings
        elif hasattr(model, 'document') and hasattr(model.document, 'thermodynamic_settings'):
            doc_settings = model.document.thermodynamic_settings
        
        # Lookup pH
        ph_value, ph_place = find_place_value(
            ['pH', 'ph', 'H+_concentration'],
            doc_settings.get('ph', 7.0)
        )
        if ph_place:
            place_names['ph'] = ph_place
        
        # Lookup temperature
        temp_value, temp_place = find_place_value(
            ['Temperature', 'temperature', 'T', 'Temperature_celsius', 'Temperature_kelvin', 
             'temperature_celsius', 'temperature_kelvin', 'Temp', 'temp'],
            doc_settings.get('temperature', 298.15)
        )
        
        # Handle Celsius vs Kelvin
        if temp_place and ('celsius' in temp_place.lower() or 'celcius' in temp_place.lower()):
            temp_value += 273.15  # Convert to Kelvin
        
        if temp_place:
            place_names['temperature'] = temp_place
        
        # Lookup ionic strength
        ionic_value, ionic_place = find_place_value(
            ['IonicStrength', 'ionic_strength', 'I'],
            doc_settings.get('ionic_strength', 0.1)
        )
        if ionic_place:
            place_names['ionic_strength'] = ionic_place
        
        # Determine source
        source = ThermodynamicSource.PLACE if place_names else ThermodynamicSource.DOCUMENT
        
        return cls(
            ph=ph_value,
            temperature=temp_value,
            ionic_strength=ionic_value,
            compartment=compartment,
            source=source,
            place_names=place_names
        )
    
    def copy_with_overrides(self, **kwargs) -> 'ThermodynamicContext':
        """Create a copy with some properties overridden.
        
        Args:
            **kwargs: Properties to override
        
        Returns:
            ThermodynamicContext: New context with overrides
        """
        data = self.to_dict()
        data.update(kwargs)
        return ThermodynamicContext.from_dict(data)
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        comp_str = f", compartment={self.compartment}" if self.compartment else ""
        return (
            f"ThermodynamicContext(pH={self.ph:.2f}, "
            f"T={self.temperature:.2f}K ({self.temperature_celsius:.1f}°C), "
            f"I={self.ionic_strength:.3f}M{comp_str}, "
            f"source={self.source.value})"
        )


@dataclass
class PlaceThermodynamics:
    """Thermodynamic properties attached to a specific place.
    
    This extends a place with compound-specific thermodynamic data.
    Stored in place.properties but defined as typed class.
    
    Architecture:
    - These properties live in Place._properties['thermodynamics']
    - But defined once here (single source of truth)
    - Automatic serialization via to_dict()
    
    Attributes:
        compound_id: Database identifier (KEGG C00002, ChEBI:15422)
        compound_name: Human-readable name
        delta_g_formation: Standard Gibbs free energy of formation (kJ/mol)
        charge: Net charge at pH 7.0
        n_protons: Protons consumed/produced in reactions
        delta_h_formation: Standard enthalpy of formation (kJ/mol), optional
        pKa_values: List of pKa values for ionizable groups
        source: Data source (eQuilibrator, MetaCyc, manual)
        uncertainty: Experimental uncertainty (±kJ/mol)
        reference_conditions: pH, T, I at which data measured
    """
    
    compound_id: Optional[str] = None
    compound_name: Optional[str] = None
    delta_g_formation: Optional[float] = None  # kJ/mol
    charge: int = 0
    n_protons: int = 0
    delta_h_formation: Optional[float] = None  # kJ/mol
    pKa_values: List[float] = field(default_factory=list)
    source: str = "unknown"
    uncertainty: float = 0.0  # kJ/mol
    reference_conditions: Dict[str, float] = field(default_factory=lambda: {
        'ph': 7.0,
        'temperature': 298.15,
        'ionic_strength': 0.1
    })
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PlaceThermodynamics':
        """Deserialize from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def __repr__(self) -> str:
        """Human-readable representation."""
        if self.compound_id:
            dg_str = f", ΔGf={self.delta_g_formation:.1f}" if self.delta_g_formation else ""
            return f"PlaceThermodynamics({self.compound_id}: {self.compound_name}{dg_str} kJ/mol)"
        return "PlaceThermodynamics(empty)"
