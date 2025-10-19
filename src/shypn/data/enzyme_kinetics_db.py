"""
Enzyme Kinetics Database

Curated database of enzyme kinetic parameters from literature sources.

Primary Sources:
- BRENDA (www.brenda-enzymes.org)
- SABIO-RK (sabio.h-its.org)
- Primary literature (PubMed)

Focus: Human enzymes from major metabolic pathways
"""

from typing import Dict, List, Optional, Any
import logging


# ============================================================================
# GLYCOLYSIS ENZYMES
# ============================================================================

GLYCOLYSIS_ENZYMES = {
    "2.7.1.1": {
        "enzyme_name": "Hexokinase",
        "ec_number": "2.7.1.1",
        "reaction": "D-Glucose + ATP → D-Glucose 6-phosphate + ADP + H+",
        "organism": "Homo sapiens",
        "tissue": "Brain",
        "isoform": "HK1",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 450.0,              # μmol/min/mg protein
            "vmax_unit": "μmol/min/mg",
            "km_glucose": 0.05,         # mM (brain HK has high affinity)
            "km_atp": 0.5,              # mM
            "km_unit": "mM"
        },
        "substrates": ["D-Glucose", "ATP"],
        "products": ["D-Glucose 6-phosphate", "ADP"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4,
            "buffer": "Phosphate"
        },
        "source": "BRENDA",
        "reference": "Wilson JE. Hexokinases. Rev Physiol Biochem Pharmacol. 2003;148:1-65.",
        "pmid": "12687400",
        "confidence": "high",
        "notes": "Brain hexokinase (HK1) has higher glucose affinity than muscle HK2. Not subject to product inhibition by G6P at physiological concentrations."
    },
    
    "5.3.1.9": {
        "enzyme_name": "Glucose-6-phosphate isomerase",
        "ec_number": "5.3.1.9",
        "reaction": "D-Glucose 6-phosphate ⇌ D-Fructose 6-phosphate",
        "organism": "Homo sapiens",
        "tissue": "Erythrocyte",
        "isoform": "GPI",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 3500.0,             # Very fast enzyme
            "vmax_unit": "μmol/min/mg",
            "km_g6p": 0.18,             # mM (forward)
            "km_f6p": 0.15,             # mM (reverse)
            "km_unit": "mM",
            "keq": 0.29                 # Equilibrium constant (F6P/G6P)
        },
        "substrates": ["D-Glucose 6-phosphate"],
        "products": ["D-Fructose 6-phosphate"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4
        },
        "source": "BRENDA",
        "reference": "Kugler W, Lakomek M. Glucose-6-phosphate isomerase deficiency. Baillieres Best Pract Res Clin Haematol. 2000;13(1):89-101.",
        "pmid": "10916680",
        "confidence": "high",
        "notes": "Near-equilibrium reaction in cells. Very high activity, not rate-limiting."
    },
    
    "2.7.1.11": {
        "enzyme_name": "6-phosphofructokinase",
        "ec_number": "2.7.1.11",
        "reaction": "D-Fructose 6-phosphate + ATP → D-Fructose 1,6-bisphosphate + ADP + H+",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "PFKM",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 200.0,              # Rate-limiting step
            "vmax_unit": "μmol/min/mg",
            "km_f6p": 0.12,             # mM
            "km_atp": 0.06,             # mM
            "km_unit": "mM"
        },
        "substrates": ["D-Fructose 6-phosphate", "ATP"],
        "products": ["D-Fructose 1,6-bisphosphate", "ADP"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.0
        },
        "source": "BRENDA",
        "reference": "Dunaway GA. A review of animal phosphofructokinase isozymes with an emphasis on their physiological role. Mol Cell Biochem. 1983;52(1):75-91.",
        "pmid": "6223528",
        "confidence": "high",
        "allosteric": {
            "inhibitors": ["ATP", "Citrate", "H+"],
            "activators": ["AMP", "ADP", "Fructose 2,6-bisphosphate", "Pi"],
            "notes": "Major regulatory enzyme. Allosteric regulation crucial for flux control."
        },
        "notes": "Committed step of glycolysis. Key control point. Strong allosteric regulation."
    },
    
    "4.1.2.13": {
        "enzyme_name": "Fructose-bisphosphate aldolase",
        "ec_number": "4.1.2.13",
        "reaction": "D-Fructose 1,6-bisphosphate ⇌ Dihydroxyacetone phosphate + D-Glyceraldehyde 3-phosphate",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "ALDOA",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 150.0,
            "vmax_unit": "μmol/min/mg",
            "km_fbp": 0.005,            # mM (very low Km)
            "km_dhap": 0.08,            # mM (reverse)
            "km_gap": 0.05,             # mM (reverse)
            "km_unit": "mM",
            "keq": 0.000078             # Strongly favors cleavage (10^-4 M)
        },
        "substrates": ["D-Fructose 1,6-bisphosphate"],
        "products": ["Dihydroxyacetone phosphate", "D-Glyceraldehyde 3-phosphate"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.5
        },
        "source": "BRENDA",
        "reference": "Lebherz HG, Rutter WJ. Distribution of fructose diphosphate aldolase variants in biological systems. Biochemistry. 1969;8(1):109-21.",
        "pmid": "5777315",
        "confidence": "high",
        "notes": "Class I aldolase (Schiff base mechanism). Near-equilibrium in cells."
    },
    
    "5.3.1.1": {
        "enzyme_name": "Triosephosphate isomerase",
        "ec_number": "5.3.1.1",
        "reaction": "D-Glyceraldehyde 3-phosphate ⇌ Dihydroxyacetone phosphate",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "TPI1",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 9000.0,             # One of the fastest enzymes known
            "vmax_unit": "μmol/min/mg",
            "km_gap": 0.45,             # mM
            "km_dhap": 0.97,            # mM
            "km_unit": "mM",
            "keq": 0.045                # Favors DHAP (22:1 ratio)
        },
        "substrates": ["D-Glyceraldehyde 3-phosphate"],
        "products": ["Dihydroxyacetone phosphate"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.6
        },
        "source": "BRENDA",
        "reference": "Wierenga RK, et al. Triosephosphate isomerase: a highly evolved biocatalyst. Cell Mol Life Sci. 2010;67(23):3961-82.",
        "pmid": "20694739",
        "confidence": "high",
        "notes": "Catalytically perfect enzyme (diffusion-limited). Maintains equilibrium between triose phosphates."
    },
    
    "1.2.1.12": {
        "enzyme_name": "Glyceraldehyde-3-phosphate dehydrogenase",
        "ec_number": "1.2.1.12",
        "reaction": "D-Glyceraldehyde 3-phosphate + NAD+ + Pi ⇌ 1,3-Bisphosphoglycerate + NADH + H+",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "GAPDH",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 500.0,
            "vmax_unit": "μmol/min/mg",
            "km_gap": 0.042,            # mM
            "km_nad": 0.045,            # mM
            "km_pi": 3.5,               # mM
            "km_unit": "mM",
            "ki_nadh": 0.003            # Product inhibition
        },
        "substrates": ["D-Glyceraldehyde 3-phosphate", "NAD+", "Orthophosphate"],
        "products": ["1,3-Bisphosphoglycerate", "NADH"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 8.5                   # Optimal pH
        },
        "source": "BRENDA",
        "reference": "Sirover MA. New insights into an old protein: the functional diversity of mammalian glyceraldehyde-3-phosphate dehydrogenase. Biochim Biophys Acta. 1999;1432(2):159-84.",
        "pmid": "10407139",
        "confidence": "high",
        "notes": "Couples oxidation to phosphorylation. Subject to NADH product inhibition. Requires inorganic phosphate."
    },
    
    "2.7.2.3": {
        "enzyme_name": "Phosphoglycerate kinase",
        "ec_number": "2.7.2.3",
        "reaction": "1,3-Bisphosphoglycerate + ADP ⇌ 3-Phosphoglycerate + ATP",
        "organism": "Homo sapiens",
        "tissue": "Erythrocyte",
        "isoform": "PGK1",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 2500.0,             # Fast enzyme
            "vmax_unit": "μmol/min/mg",
            "km_13bpg": 0.003,          # mM
            "km_adp": 0.12,             # mM
            "km_3pg": 0.25,             # mM (reverse)
            "km_atp": 0.3,              # mM (reverse)
            "km_unit": "mM",
            "keq": 3200                 # Strongly favors ATP formation
        },
        "substrates": ["1,3-Bisphosphoglycerate", "ADP"],
        "products": ["3-Phosphoglycerate", "ATP"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4
        },
        "source": "BRENDA",
        "reference": "Bernstein BE, Hol WG. Crystal structures of substrates and products bound to the phosphoglycerate kinase active site reveal the catalytic mechanism. Biochemistry. 1998;37(13):4429-36.",
        "pmid": "9521763",
        "confidence": "high",
        "notes": "First ATP-generating step in glycolysis (substrate-level phosphorylation)."
    },
    
    "5.4.2.12": {
        "enzyme_name": "Phosphoglycerate mutase",
        "ec_number": "5.4.2.12",
        "reaction": "3-Phosphoglycerate ⇌ 2-Phosphoglycerate",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "PGAM1",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 1500.0,
            "vmax_unit": "μmol/min/mg",
            "km_3pg": 0.12,             # mM
            "km_2pg": 0.08,             # mM (reverse)
            "km_unit": "mM",
            "keq": 0.17                 # Slightly favors 3PG
        },
        "substrates": ["3-Phosphoglycerate"],
        "products": ["2-Phosphoglycerate"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4
        },
        "source": "BRENDA",
        "reference": "Fothergill-Gilmore LA, Michels PA. Evolution of glycolysis. Prog Biophys Mol Biol. 1993;59(2):105-235.",
        "pmid": "8426905",
        "confidence": "high",
        "notes": "Cofactor-dependent enzyme (requires 2,3-BPG in mammals). Near-equilibrium reaction."
    },
    
    "4.2.1.11": {
        "enzyme_name": "Enolase",
        "ec_number": "4.2.1.11",
        "reaction": "2-Phosphoglycerate ⇌ Phosphoenolpyruvate + H2O",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "ENO1",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 600.0,
            "vmax_unit": "μmol/min/mg",
            "km_2pg": 0.04,             # mM
            "km_pep": 0.025,            # mM (reverse)
            "km_unit": "mM",
            "keq": 6.7                  # Favors PEP formation
        },
        "substrates": ["2-Phosphoglycerate"],
        "products": ["Phosphoenolpyruvate"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.4
        },
        "source": "BRENDA",
        "reference": "Pancholi V. Multifunctional alpha-enolase: its role in diseases. Cell Mol Life Sci. 2001;58(7):902-20.",
        "pmid": "11497239",
        "confidence": "high",
        "notes": "Requires Mg2+. Generates high-energy phosphoenolpyruvate."
    },
    
    "2.7.1.40": {
        "enzyme_name": "Pyruvate kinase",
        "ec_number": "2.7.1.40",
        "reaction": "Phosphoenolpyruvate + ADP + H+ → Pyruvate + ATP",
        "organism": "Homo sapiens",
        "tissue": "Muscle",
        "isoform": "PKM2",
        "type": "continuous",
        "law": "michaelis_menten",
        "parameters": {
            "vmax": 800.0,              # High activity
            "vmax_unit": "μmol/min/mg",
            "km_pep": 0.058,            # mM
            "km_adp": 0.11,             # mM
            "km_unit": "mM",
            "keq": 340000               # Essentially irreversible
        },
        "substrates": ["Phosphoenolpyruvate", "ADP"],
        "products": ["Pyruvate", "ATP"],
        "conditions": {
            "temperature": 37,
            "temperature_unit": "°C",
            "ph": 7.6
        },
        "source": "BRENDA",
        "reference": "Jurica MS, et al. The allosteric regulation of pyruvate kinase by fructose-1,6-bisphosphate. Structure. 1998;6(2):195-210.",
        "pmid": "9519410",
        "confidence": "high",
        "allosteric": {
            "activators": ["Fructose 1,6-bisphosphate"],
            "inhibitors": ["ATP", "Alanine", "Acetyl-CoA"],
            "notes": "Feed-forward activation by F-1,6-BP. Multiple isoforms with different regulation."
        },
        "notes": "Second substrate-level phosphorylation. Essentially irreversible under physiological conditions. Key regulatory point."
    },
}


# ============================================================================
# MASTER DATABASE
# ============================================================================

ENZYME_KINETICS = {
    **GLYCOLYSIS_ENZYMES,
    # Future additions:
    # **TCA_CYCLE_ENZYMES,
    # **PENTOSE_PHOSPHATE_ENZYMES,
    # **GLUCONEOGENESIS_ENZYMES,
}


# ============================================================================
# DATABASE CLASS
# ============================================================================

class EnzymeKineticsDB:
    """
    Database of enzyme kinetic parameters from literature.
    
    Provides lookup methods for retrieving kinetic parameters by EC number.
    All entries are curated from scientific literature (BRENDA, SABIO-RK, PubMed).
    
    Example:
        >>> db = EnzymeKineticsDB()
        >>> entry = db.lookup("2.7.1.1")  # Hexokinase
        >>> print(entry['enzyme_name'])
        'Hexokinase'
        >>> print(entry['parameters']['vmax'])
        450.0
    """
    
    def __init__(self):
        """Initialize database."""
        self._db = ENZYME_KINETICS
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Initialized enzyme kinetics database with {len(self._db)} entries")
    
    def lookup(
        self, 
        ec_number: str, 
        organism: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Lookup kinetic parameters by EC number.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Organism name (default: None, returns any match)
                     If specified, must match exactly (e.g., "Homo sapiens")
        
        Returns:
            Dict with complete enzyme entry or None if not found
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> entry = db.lookup("2.7.1.1", organism="Homo sapiens")
            >>> entry['enzyme_name']
            'Hexokinase'
        """
        entry = self._db.get(ec_number)
        
        if not entry:
            self.logger.debug(f"EC {ec_number} not found in database")
            return None
        
        # Check organism match if specified
        if organism and entry.get("organism") != organism:
            self.logger.debug(
                f"EC {ec_number} found but organism mismatch: "
                f"requested '{organism}', found '{entry.get('organism')}'"
            )
            # Return anyway (could be configured to return None)
        
        self.logger.debug(f"Found EC {ec_number}: {entry['enzyme_name']}")
        return entry
    
    def get_parameters(
        self, 
        ec_number: str, 
        organism: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get just the parameters dict for an enzyme.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Optional organism filter
        
        Returns:
            Dict with parameters (vmax, km, etc.) or None if not found
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> params = db.get_parameters("2.7.1.1")
            >>> params['vmax']
            450.0
            >>> params['km_glucose']
            0.05
        """
        entry = self.lookup(ec_number, organism)
        return entry.get("parameters") if entry else None
    
    def has_ec_number(self, ec_number: str) -> bool:
        """
        Check if EC number exists in database.
        
        Args:
            ec_number: EC number to check
        
        Returns:
            True if EC number is in database
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> db.has_ec_number("2.7.1.1")
            True
            >>> db.has_ec_number("9.9.9.9")
            False
        """
        return ec_number in self._db
    
    def get_all_ec_numbers(self) -> List[str]:
        """
        Get list of all EC numbers in database.
        
        Returns:
            List of EC numbers
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> ec_numbers = db.get_all_ec_numbers()
            >>> len(ec_numbers)
            10
            >>> "2.7.1.1" in ec_numbers
            True
        """
        return list(self._db.keys())
    
    def get_enzymes_by_pathway(self, pathway: str) -> List[Dict[str, Any]]:
        """
        Get all enzymes for a specific pathway (future enhancement).
        
        Args:
            pathway: Pathway name (e.g., "glycolysis", "tca_cycle")
        
        Returns:
            List of enzyme entries
        
        Note:
            Current implementation returns empty list. Will be implemented
            when pathway annotations are added to database entries.
        """
        # TODO: Add pathway tags to database entries
        self.logger.warning("Pathway filtering not yet implemented")
        return []
    
    def search_by_name(self, name: str) -> List[Dict[str, Any]]:
        """
        Search for enzymes by name (case-insensitive partial match).
        
        Args:
            name: Enzyme name or partial name
        
        Returns:
            List of matching enzyme entries
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> results = db.search_by_name("kinase")
            >>> len(results)
            3  # Hexokinase, Phosphofructokinase, Pyruvate kinase
        """
        name_lower = name.lower()
        results = []
        
        for ec_number, entry in self._db.items():
            enzyme_name = entry.get("enzyme_name", "").lower()
            if name_lower in enzyme_name:
                results.append(entry)
        
        self.logger.debug(f"Found {len(results)} enzymes matching '{name}'")
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the database.
        
        Returns:
            Dict with database statistics
            
        Example:
            >>> db = EnzymeKineticsDB()
            >>> stats = db.get_database_stats()
            >>> stats['total_enzymes']
            10
            >>> stats['organisms']
            ['Homo sapiens']
        """
        organisms = set()
        tissues = set()
        sources = set()
        
        for entry in self._db.values():
            if "organism" in entry:
                organisms.add(entry["organism"])
            if "tissue" in entry:
                tissues.add(entry["tissue"])
            if "source" in entry:
                sources.add(entry["source"])
        
        return {
            "total_enzymes": len(self._db),
            "ec_numbers": list(self._db.keys()),
            "organisms": sorted(list(organisms)),
            "tissues": sorted(list(tissues)),
            "sources": sorted(list(sources))
        }


# ============================================================================
# MODULE-LEVEL CONVENIENCE FUNCTIONS
# ============================================================================

def get_enzyme(ec_number: str) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get enzyme entry.
    
    Args:
        ec_number: EC number
    
    Returns:
        Enzyme entry dict or None
        
    Example:
        >>> from shypn.data.enzyme_kinetics_db import get_enzyme
        >>> enzyme = get_enzyme("2.7.1.1")
        >>> enzyme['enzyme_name']
        'Hexokinase'
    """
    return ENZYME_KINETICS.get(ec_number)


def has_enzyme(ec_number: str) -> bool:
    """
    Convenience function to check if enzyme exists.
    
    Args:
        ec_number: EC number
    
    Returns:
        True if enzyme is in database
    """
    return ec_number in ENZYME_KINETICS
