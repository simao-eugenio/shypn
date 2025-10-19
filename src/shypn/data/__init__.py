"""
Data package for shypn.

Contains static data files and databases:
- Enzyme kinetics API (external databases with caching)
- Enzyme kinetics database (fallback for offline mode)
- Reference pathways
- Parameter sets
"""

from shypn.data.enzyme_kinetics_api import EnzymeKineticsAPI, get_api, lookup_enzyme
from shypn.data.enzyme_kinetics_db import EnzymeKineticsDB, ENZYME_KINETICS

__all__ = [
    # API-based (recommended for production)
    'EnzymeKineticsAPI',
    'get_api',
    'lookup_enzyme',
    
    # Local database (fallback for offline mode)
    'EnzymeKineticsDB', 
    'ENZYME_KINETICS'
]
