# Kinetic Parameter Heuristics - Architecture Design

**Created**: October 18, 2025  
**Status**: 🏗️ ARCHITECTURE DESIGN  
**Pattern**: OOP with Base Class + Specialized Estimators

---

## Architecture Overview

### Design Principles

1. ✅ **OOP with Base Class**: Abstract `KineticEstimator` base
2. ✅ **Separate Modules**: Each estimator in own file
3. ✅ **Minimal Loader Code**: Thin facade in PathwayConverter
4. ✅ **Heuristic Package**: All under `src/shypn/heuristic/`
5. ✅ **Documentation**: All docs under `doc/heuristic/`

---

## Module Structure

```
src/shypn/heuristic/
├── __init__.py                          # Package exports
├── base.py                              # KineticEstimator (abstract base)
├── michaelis_menten.py                  # MichaelisMentenEstimator
├── stochastic.py                        # StochasticEstimator (exponential)
├── mass_action.py                       # MassActionEstimator
└── factory.py                           # EstimatorFactory (simple facade)

doc/heuristic/
├── README.md                            # Overview and quick start
├── ARCHITECTURE.md                      # Design patterns
├── MICHAELIS_MENTEN_HEURISTICS.md      # MM estimation rules
├── STOCHASTIC_HEURISTICS.md            # Exponential distribution
└── MASS_ACTION_HEURISTICS.md           # Mass action kinetics
```

---

## Class Hierarchy

```
KineticEstimator (ABC)
├── MichaelisMentenEstimator
│   ├── estimate_parameters() → (vmax, km)
│   └── build_rate_function() → "michaelis_menten(...)"
│
├── StochasticEstimator
│   ├── estimate_parameters() → (lambda_rate, distribution)
│   └── build_rate_function() → "exponential(...)"
│
└── MassActionEstimator
    ├── estimate_parameters() → (k,)
    └── build_rate_function() → "mass_action(...)"
```

---

## Base Class Design

### File: `src/shypn/heuristic/base.py`

```python
"""
Base class for kinetic parameter estimation.

Defines the interface for all kinetic estimators.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Any
from shypn.netobjs.place import Place
from shypn.data.pathway.pathway_data import Reaction


class KineticEstimator(ABC):
    """
    Abstract base class for kinetic parameter estimation.
    
    All estimators must implement:
    - estimate_parameters(): Calculate kinetic parameters
    - build_rate_function(): Generate rate function string
    """
    
    def __init__(self):
        """Initialize estimator with defaults."""
        self.logger = self._setup_logger()
        self.parameter_cache = {}
    
    @abstractmethod
    def estimate_parameters(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Dict[str, Any]:
        """
        Estimate kinetic parameters from reaction data.
        
        Args:
            reaction: Reaction object with stoichiometry
            substrate_places: Input places
            product_places: Output places
            
        Returns:
            Dictionary of parameter names and values
            
        Example:
            {'vmax': 10.0, 'km': 5.0}
        """
        pass
    
    @abstractmethod
    def build_rate_function(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build rate function string from parameters.
        
        Args:
            reaction: Reaction object
            substrate_places: Input places
            product_places: Output places
            parameters: Estimated parameters
            
        Returns:
            Rate function string
            
        Example:
            "michaelis_menten(P_Glucose, 10.0, 5.0)"
        """
        pass
    
    def estimate_and_build(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Tuple[Dict[str, Any], str]:
        """
        Convenience method: estimate + build in one call.
        
        Returns:
            (parameters_dict, rate_function_string)
        """
        parameters = self.estimate_parameters(
            reaction, substrate_places, product_places
        )
        rate_function = self.build_rate_function(
            reaction, substrate_places, product_places, parameters
        )
        return parameters, rate_function
    
    def _make_cache_key(self, reaction: Reaction) -> str:
        """Create cache key from reaction properties."""
        reactants = tuple(sorted(rid for rid, _ in reaction.reactants))
        products = tuple(sorted(pid for pid, _ in reaction.products))
        return f"{reaction.name}_{reactants}_{products}"
    
    def _setup_logger(self):
        """Setup logger for this estimator."""
        import logging
        return logging.getLogger(self.__class__.__name__)
```

---

## Michaelis-Menten Estimator

### File: `src/shypn/heuristic/michaelis_menten.py`

```python
"""
Michaelis-Menten kinetic parameter estimator.

Estimates Vmax and Km from reaction stoichiometry and substrate concentrations.
"""

from typing import Dict, List, Any
from shypn.netobjs.place import Place
from shypn.data.pathway.pathway_data import Reaction
from .base import KineticEstimator


class MichaelisMentenEstimator(KineticEstimator):
    """
    Estimates Michaelis-Menten parameters (Vmax, Km).
    
    Heuristic Rules:
    - Vmax = 10.0 * max(product_stoichiometry)
    - Km = mean(substrate_concentrations) / 2
    - Adjustments for reversibility
    """
    
    def __init__(self):
        super().__init__()
        self.default_vmax = 10.0
        self.default_km = 5.0
    
    def estimate_parameters(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Dict[str, Any]:
        """
        Estimate Vmax and Km.
        
        Returns:
            {'vmax': float, 'km': float}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate Vmax
        vmax = self._estimate_vmax(reaction, product_places)
        
        # Estimate Km
        km = self._estimate_km(reaction, substrate_places)
        
        parameters = {'vmax': vmax, 'km': km}
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        self.logger.info(
            f"Estimated MM parameters for {reaction.id}: "
            f"Vmax={vmax:.2f}, Km={km:.2f}"
        )
        
        return parameters
    
    def build_rate_function(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build Michaelis-Menten rate function.
        
        Single substrate:
            michaelis_menten(S, Vmax, Km)
        
        Multiple substrates (sequential):
            michaelis_menten(S1, Vmax, Km) * (S2/(Km+S2)) * (S3/(Km+S3))
        """
        if not substrate_places:
            raise ValueError("No substrate places for Michaelis-Menten")
        
        vmax = parameters['vmax']
        km = parameters['km']
        
        # Single substrate - standard MM
        if len(substrate_places) == 1:
            return f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
        
        # Multiple substrates - sequential MM
        rate_func = f"michaelis_menten({substrate_places[0].name}, {vmax}, {km})"
        
        for substrate in substrate_places[1:]:
            rate_func += f" * ({substrate.name} / ({km} + {substrate.name}))"
        
        return rate_func
    
    def _estimate_vmax(
        self,
        reaction: Reaction,
        product_places: List[Place]
    ) -> float:
        """
        Estimate Vmax from product stoichiometry.
        
        Rule: Vmax = 10.0 * max(product_stoichiometry)
        """
        if not reaction.products:
            return self.default_vmax
        
        # Get maximum product stoichiometry
        max_stoich = max(stoich for _, stoich in reaction.products)
        
        # Base Vmax
        vmax = self.default_vmax * max_stoich
        
        # Adjust for reversibility
        if reaction.reversible:
            vmax *= 0.8  # Reversible reactions slightly slower
        
        return vmax
    
    def _estimate_km(
        self,
        reaction: Reaction,
        substrate_places: List[Place]
    ) -> float:
        """
        Estimate Km from substrate concentrations.
        
        Rule: Km ≈ mean(substrate_concentrations) / 2
        """
        if not substrate_places:
            return self.default_km
        
        # Get concentrations (tokens)
        concentrations = [
            p.tokens for p in substrate_places
            if p.tokens > 0
        ]
        
        if not concentrations:
            return self.default_km
        
        # Mean concentration / 2
        mean_conc = sum(concentrations) / len(concentrations)
        km = mean_conc / 2.0
        
        # Ensure minimum
        km = max(0.5, km)
        
        return km
```

---

## Stochastic Estimator (Exponential)

### File: `src/shypn/heuristic/stochastic.py`

```python
"""
Stochastic kinetic parameter estimator (exponential distribution).

Estimates lambda (rate) parameter for exponential transitions.
"""

from typing import Dict, List, Any
from shypn.netobjs.place import Place
from shypn.data.pathway.pathway_data import Reaction
from .base import KineticEstimator


class StochasticEstimator(KineticEstimator):
    """
    Estimates parameters for stochastic (exponential) transitions.
    
    Heuristic Rules:
    - Lambda = base_rate * reactant_stoichiometry
    - Adjust for reaction complexity
    - Pre-fill exponential distribution
    """
    
    def __init__(self):
        super().__init__()
        self.default_lambda = 1.0
    
    def estimate_parameters(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Dict[str, Any]:
        """
        Estimate lambda (rate) for exponential distribution.
        
        Returns:
            {'lambda': float, 'distribution': 'exponential'}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate lambda
        lambda_rate = self._estimate_lambda(reaction, substrate_places)
        
        parameters = {
            'lambda': lambda_rate,
            'distribution': 'exponential'
        }
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        self.logger.info(
            f"Estimated stochastic parameters for {reaction.id}: "
            f"lambda={lambda_rate:.2f}"
        )
        
        return parameters
    
    def build_rate_function(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build exponential rate function.
        
        Format: "exponential(lambda_rate)"
        """
        lambda_rate = parameters['lambda']
        return f"exponential({lambda_rate})"
    
    def _estimate_lambda(
        self,
        reaction: Reaction,
        substrate_places: List[Place]
    ) -> float:
        """
        Estimate lambda from reaction properties.
        
        Rules:
        - Base rate = 1.0
        - Scale by total reactant stoichiometry
        - Adjust for substrate availability
        """
        if not reaction.reactants:
            return self.default_lambda
        
        # Sum of reactant stoichiometries
        total_stoich = sum(stoich for _, stoich in reaction.reactants)
        
        # Base lambda scaled by stoichiometry
        lambda_rate = self.default_lambda * total_stoich
        
        # Adjust for substrate availability
        if substrate_places:
            # If substrates have low concentration, reduce rate
            min_tokens = min(p.tokens for p in substrate_places if p.tokens > 0)
            if min_tokens < 10:
                lambda_rate *= 0.5  # Slower for low concentrations
        
        return lambda_rate
```

---

## Mass Action Estimator

### File: `src/shypn/heuristic/mass_action.py`

```python
"""
Mass action kinetic parameter estimator.

Estimates rate constant k for mass action kinetics.
"""

from typing import Dict, List, Any
from shypn.netobjs.place import Place
from shypn.data.pathway.pathway_data import Reaction
from .base import KineticEstimator


class MassActionEstimator(KineticEstimator):
    """
    Estimates rate constant for mass action kinetics.
    
    Heuristic Rules:
    - k = base_rate / number_of_reactants
    - Bimolecular reactions slower than unimolecular
    """
    
    def __init__(self):
        super().__init__()
        self.default_k = 1.0
    
    def estimate_parameters(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place]
    ) -> Dict[str, Any]:
        """
        Estimate rate constant k.
        
        Returns:
            {'k': float}
        """
        # Check cache
        cache_key = self._make_cache_key(reaction)
        if cache_key in self.parameter_cache:
            return self.parameter_cache[cache_key]
        
        # Estimate k
        k = self._estimate_k(reaction, substrate_places)
        
        parameters = {'k': k}
        
        # Cache results
        self.parameter_cache[cache_key] = parameters
        
        self.logger.info(
            f"Estimated mass action parameter for {reaction.id}: k={k:.2f}"
        )
        
        return parameters
    
    def build_rate_function(
        self,
        reaction: Reaction,
        substrate_places: List[Place],
        product_places: List[Place],
        parameters: Dict[str, Any]
    ) -> str:
        """
        Build mass action rate function.
        
        Format: "mass_action(R1, R2, k)"
        """
        k = parameters['k']
        
        if len(substrate_places) >= 2:
            return f"mass_action({substrate_places[0].name}, {substrate_places[1].name}, {k})"
        elif len(substrate_places) == 1:
            return f"mass_action({substrate_places[0].name}, 1.0, {k})"
        else:
            return f"{k}"
    
    def _estimate_k(
        self,
        reaction: Reaction,
        substrate_places: List[Place]
    ) -> float:
        """
        Estimate rate constant k.
        
        Rules:
        - Unimolecular: k = 1.0
        - Bimolecular: k = 0.1 (slower)
        - Trimolecular: k = 0.01 (much slower)
        """
        num_reactants = len(reaction.reactants)
        
        if num_reactants == 1:
            return 1.0  # Unimolecular
        elif num_reactants == 2:
            return 0.1  # Bimolecular
        else:
            return 0.01  # Trimolecular or more
```

---

## Factory (Facade)

### File: `src/shypn/heuristic/factory.py`

```python
"""
Factory for creating appropriate kinetic estimators.

Simple facade for selecting estimator based on kinetic type.
"""

from typing import Optional
from .base import KineticEstimator
from .michaelis_menten import MichaelisMentenEstimator
from .stochastic import StochasticEstimator
from .mass_action import MassActionEstimator


class EstimatorFactory:
    """
    Factory for creating kinetic estimators.
    
    Usage:
        estimator = EstimatorFactory.create('michaelis_menten')
        params, rate_func = estimator.estimate_and_build(...)
    """
    
    # Registry of estimators
    _estimators = {
        'michaelis_menten': MichaelisMentenEstimator,
        'stochastic': StochasticEstimator,
        'mass_action': MassActionEstimator,
    }
    
    @classmethod
    def create(cls, kinetic_type: str) -> Optional[KineticEstimator]:
        """
        Create estimator for given kinetic type.
        
        Args:
            kinetic_type: 'michaelis_menten', 'stochastic', or 'mass_action'
            
        Returns:
            Estimator instance or None if type not found
        """
        estimator_class = cls._estimators.get(kinetic_type)
        if estimator_class:
            return estimator_class()
        return None
    
    @classmethod
    def available_types(cls):
        """Get list of available kinetic types."""
        return list(cls._estimators.keys())
```

---

## Package Initialization

### File: `src/shypn/heuristic/__init__.py`

```python
"""
Kinetic Parameter Heuristics Package

Provides intelligent estimation of kinetic parameters from stoichiometry.

Usage:
    from shypn.heuristic import EstimatorFactory
    
    estimator = EstimatorFactory.create('michaelis_menten')
    params, rate_func = estimator.estimate_and_build(reaction, substrates, products)
"""

from .base import KineticEstimator
from .michaelis_menten import MichaelisMentenEstimator
from .stochastic import StochasticEstimator
from .mass_action import MassActionEstimator
from .factory import EstimatorFactory

__all__ = [
    'KineticEstimator',
    'MichaelisMentenEstimator',
    'StochasticEstimator',
    'MassActionEstimator',
    'EstimatorFactory',
]
```

---

## Minimal Loader Integration

### File: `src/shypn/data/pathway/pathway_converter.py` (MODIFICATION)

```python
from shypn.heuristic import EstimatorFactory

class ReactionConverter(BaseConverter):
    def __init__(self, pathway, document, species_to_place=None):
        super().__init__(pathway, document)
        self.species_to_place = species_to_place or {}
        # No local estimator - use factory
    
    def _configure_transition_kinetics(self, transition, reaction):
        """Configure transition kinetics based on reaction kinetic law."""
        
        if not reaction.kinetic_law:
            # NO KINETIC LAW → Estimate using heuristics
            self._setup_estimated_kinetics(transition, reaction)
            return
        
        # Has kinetic law → Handle as before
        kinetic = reaction.kinetic_law
        
        if kinetic.rate_type == "michaelis_menten":
            self._setup_michaelis_menten(transition, reaction, kinetic)
        elif kinetic.rate_type == "mass_action":
            self._setup_mass_action(transition, reaction, kinetic)
        else:
            transition.transition_type = "continuous"
            transition.rate = 1.0
    
    def _setup_estimated_kinetics(self, transition, reaction):
        """
        Setup kinetics using heuristic estimation.
        
        NEW METHOD: Minimal code, delegates to heuristic package.
        """
        # Get places
        substrate_places = [
            self.species_to_place.get(sid)
            for sid, _ in reaction.reactants
            if self.species_to_place.get(sid)
        ]
        product_places = [
            self.species_to_place.get(sid)
            for sid, _ in reaction.products
            if self.species_to_place.get(sid)
        ]
        
        if not substrate_places:
            transition.transition_type = "continuous"
            transition.rate = 1.0
            return
        
        # DEFAULT: Assume Michaelis-Menten for continuous
        estimator = EstimatorFactory.create('michaelis_menten')
        
        if estimator:
            # Estimate parameters and build rate function
            params, rate_func = estimator.estimate_and_build(
                reaction, substrate_places, product_places
            )
            
            # Apply to transition
            transition.transition_type = "continuous"
            transition.rate = params.get('vmax', 1.0)
            transition.properties['rate_function'] = rate_func
            
            self.logger.info(
                f"  Estimated kinetics: {rate_func}"
            )
        else:
            # Fallback
            transition.transition_type = "continuous"
            transition.rate = 1.0
```

**Key Point**: Loader code is **MINIMAL** (~20 lines), delegates to heuristic package.

---

## Summary

### Module Structure
```
src/shypn/heuristic/
├── __init__.py              # 15 lines
├── base.py                  # 120 lines (abstract base)
├── michaelis_menten.py      # 150 lines
├── stochastic.py            # 120 lines (NEW - exponential)
├── mass_action.py           # 100 lines
└── factory.py               # 40 lines

Total: ~545 lines (well-organized OOP)
```

### Documentation Structure
```
doc/heuristic/
├── README.md                          # Overview
├── ARCHITECTURE.md                    # This file
├── MICHAELIS_MENTEN_HEURISTICS.md    # MM rules
├── STOCHASTIC_HEURISTICS.md          # Exponential rules (NEW)
└── MASS_ACTION_HEURISTICS.md         # MA rules
```

### Key Benefits

1. ✅ **Clean OOP**: Base class + specialized estimators
2. ✅ **Separated Modules**: Each estimator in own file
3. ✅ **Minimal Loader**: ~20 lines in PathwayConverter
4. ✅ **Easy Testing**: Each estimator independently testable
5. ✅ **Extensible**: Add new estimators by extending base
6. ✅ **Factory Pattern**: Simple estimator creation

### Usage Example

```python
# In PathwayConverter
from shypn.heuristic import EstimatorFactory

estimator = EstimatorFactory.create('michaelis_menten')
params, rate_func = estimator.estimate_and_build(reaction, substrates, products)

transition.properties['rate_function'] = rate_func
```

---

**Status**: 🏗️ Architecture Design Complete  
**Next**: Implement modules + documentation  
**Estimated**: 3-4 days for complete implementation
