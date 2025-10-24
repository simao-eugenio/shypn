# BRENDA Database - Data Reference Guide

**Date:** October 24, 2025  
**Purpose:** Comprehensive reference for data retrieval from BRENDA

---

## Overview

**BRENDA** = **BR**aunschweig **EN**zyme **DA**tabase  
**URL:** https://www.brenda-enzymes.org/  
**Type:** Comprehensive enzyme information system  
**Access:** REST API + SOAP API (requires free registration for API key)

### Why BRENDA for SHYpn?

**Metadata Enrichment:**
- Enzymes are **transitions** in Petri nets (biological reactions)
- BRENDA provides **kinetic parameters** (Km, Vmax, kcat, Ki)
- BRENDA provides **biological context** (organism, tissue, conditions)
- BRENDA provides **scientific provenance** (literature references)

**Use Case:** User models MAPK pathway → Queries BRENDA for ERK kinase → Gets Km values for different organisms → Uses in simulation → Cites BRENDA in report

---

## Core Data Categories

### 1. **EC Number Classification** (Enzyme Commission)

**What:** Hierarchical enzyme classification system

**Format:** `EC x.y.z.w`
- **x** = Main class (1-7)
- **y** = Subclass
- **z** = Sub-subclass
- **w** = Serial number

**Example:** `EC 2.7.11.24` = Mitogen-activated protein kinase (MAPK/ERK)

**Main Classes:**
1. **EC 1.x.x.x** - Oxidoreductases (redox reactions)
2. **EC 2.x.x.x** - Transferases (transfer functional groups)
3. **EC 3.x.x.x** - Hydrolases (hydrolysis reactions)
4. **EC 4.x.x.x** - Lyases (add/remove groups, form double bonds)
5. **EC 5.x.x.x** - Isomerases (isomerization)
6. **EC 6.x.x.x** - Ligases (join molecules using ATP)
7. **EC 7.x.x.x** - Translocases (move ions/molecules across membranes)

**Retrievable Data:**
```python
{
    "ec_number": "2.7.11.24",
    "systematic_name": "ATP:protein phosphotransferase (MAP kinase kinase kinase)",
    "recommended_name": "mitogen-activated protein kinase kinase kinase",
    "alternative_names": [
        "MAPKKK",
        "MAP3K",
        "MEKK",
        "Raf kinase"
    ],
    "reaction": "ATP + a protein = ADP + a phosphoprotein",
    "cofactors": ["Mg2+", "Mn2+"],
    "main_class": "Transferases",
    "subclass": "Phosphotransferases",
    "sub_subclass": "Protein-serine/threonine kinases"
}
```

**SHYpn Use:**
- Store in **TransitionMetadata**
- Display in property dialogs
- Include in reports
- Enable search by EC number

---

### 2. **Enzyme Names**

**Types of Names:**

#### A. Systematic Name (IUPAC standard)
```
ATP:protein phosphotransferase (MAP kinase kinase kinase)
```
- Precise chemical description
- Based on reaction mechanism
- Standardized nomenclature

#### B. Recommended Name (Common usage)
```
mitogen-activated protein kinase kinase kinase
```
- Most widely used in literature
- User-friendly
- Official BRENDA recommendation

#### C. Alternative Names / Synonyms
```python
[
    "MAPKKK",
    "MAP3K",
    "MEKK",
    "Raf kinase",
    "c-Raf",
    "Raf-1",
    "proto-oncogene serine/threonine-protein kinase"
]
```
- Historical names
- Organism-specific names
- Gene names
- Commercial names

**Retrievable Data:**
```python
{
    "systematic_name": "...",
    "recommended_name": "...",
    "synonyms": [...],
    "acronyms": [...],
    "obsolete_names": [...],
    "gene_names": ["RAF1", "CRAF"],
    "protein_names": ["c-Raf", "Raf-1"]
}
```

**SHYpn Use:**
- Auto-complete in transition naming
- Search by any synonym
- Display multiple names in reports
- Link gene names to UniProt

---

### 3. **Kinetic Parameters** (⭐ MOST IMPORTANT)

#### A. **Km (Michaelis Constant)**
**Meaning:** Substrate concentration at half-maximal velocity  
**Units:** mM, μM, nM (concentration)  
**Importance:** Enzyme-substrate affinity

**Example Data:**
```python
{
    "parameter": "Km",
    "substrate": "ATP",
    "value": 15.0,
    "unit": "μM",
    "organism": "Homo sapiens",
    "tissue": "brain",
    "pH": 7.4,
    "temperature": 37,
    "temperature_unit": "°C",
    "method": "spectrophotometry",
    "commentary": "recombinant enzyme",
    "literature": "PMID:12345678"
}
```

**Multiple Values:**
- Different organisms (human vs. rat vs. yeast)
- Different substrates (ATP, GTP, other)
- Different conditions (pH, temperature)
- Different isoforms (Raf-1 vs. B-Raf vs. A-Raf)

#### B. **kcat (Turnover Number)**
**Meaning:** Maximum catalytic rate per enzyme molecule  
**Units:** s⁻¹ (reactions per second)  
**Importance:** Enzyme efficiency

**Example:**
```python
{
    "parameter": "kcat",
    "value": 15.8,
    "unit": "s^-1",
    "substrate": "MEK1",
    "organism": "Homo sapiens",
    "temperature": 30,
    "pH": 7.5,
    "literature": "PMID:23456789"
}
```

#### C. **Vmax (Maximum Velocity)**
**Meaning:** Maximum reaction rate  
**Units:** μmol/min/mg protein  
**Importance:** Overall capacity

#### D. **kcat/Km (Catalytic Efficiency)**
**Meaning:** Overall enzyme performance  
**Units:** M⁻¹s⁻¹  
**Importance:** Best single metric for enzyme quality

#### E. **Ki (Inhibition Constant)**
**Meaning:** Inhibitor affinity  
**Units:** mM, μM, nM  
**Importance:** Regulatory mechanisms

**Example:**
```python
{
    "parameter": "Ki",
    "inhibitor": "U0126",
    "value": 0.07,
    "unit": "μM",
    "inhibition_type": "competitive",
    "organism": "Homo sapiens",
    "literature": "PMID:34567890"
}
```

**Full Kinetic Dataset:**
```python
{
    "ec_number": "2.7.11.24",
    "enzyme_name": "MAP kinase kinase kinase",
    "organism": "Homo sapiens",
    "kinetic_parameters": [
        {
            "type": "Km",
            "substrate": "ATP",
            "value": 15.0,
            "unit": "μM",
            "conditions": {
                "pH": 7.4,
                "temperature": 37,
                "temperature_unit": "°C",
                "buffer": "Tris-HCl"
            },
            "method": "spectrophotometry",
            "reference": {
                "pmid": "12345678",
                "authors": "Smith et al.",
                "year": 2020,
                "journal": "J Biol Chem",
                "title": "Kinetic characterization of..."
            }
        },
        {
            "type": "kcat",
            "value": 15.8,
            "unit": "s^-1",
            "substrate": "MEK1",
            # ... similar structure
        },
        {
            "type": "Ki",
            "inhibitor": "U0126",
            "value": 0.07,
            "unit": "μM",
            "inhibition_type": "competitive",
            # ... similar structure
        }
    ]
}
```

**SHYpn Use:**
- **Simulation parameters** - Use Km/Vmax in stochastic transitions
- **Parameter selection dialog** - Show multiple values, let user choose
- **Organism-specific modeling** - Filter by organism
- **Condition-specific modeling** - Adjust for pH/temperature
- **Report metadata** - Document parameter sources
- **Literature citations** - Auto-generate bibliography

---

### 4. **Substrates and Products**

**What:** Chemical compounds involved in reactions

**Substrate Data:**
```python
{
    "substrates": [
        {
            "name": "ATP",
            "chebi_id": "CHEBI:15422",
            "formula": "C10H16N5O13P3",
            "molecular_weight": 507.18,
            "role": "phosphate donor"
        },
        {
            "name": "protein serine",
            "role": "phosphate acceptor",
            "modification": "phosphorylation site"
        }
    ],
    "products": [
        {
            "name": "ADP",
            "chebi_id": "CHEBI:16761",
            "formula": "C10H15N5O10P2",
            "molecular_weight": 427.20
        },
        {
            "name": "phosphoprotein",
            "modification": "phospho-serine"
        }
    ],
    "cofactors": [
        {
            "name": "Mg2+",
            "role": "catalytic",
            "chebi_id": "CHEBI:18420"
        }
    ],
    "activators": [...],
    "inhibitors": [...]
}
```

**SHYpn Use:**
- **Arc annotations** - Label with substrate/product names
- **Place identification** - Auto-suggest compound names
- **Stoichiometry** - Multiple substrates/products
- **ChEBI integration** - Link to chemical database

---

### 5. **Organism-Specific Data**

**What:** Data organized by species

**Organism Classification:**
```python
{
    "organism": "Homo sapiens",
    "taxonomy": {
        "ncbi_tax_id": 9606,
        "kingdom": "Animalia",
        "phylum": "Chordata",
        "class": "Mammalia",
        "order": "Primates",
        "family": "Hominidae",
        "genus": "Homo",
        "species": "sapiens"
    },
    "common_name": "human",
    "tissue_specificity": [
        "brain",
        "liver",
        "heart",
        "skeletal muscle"
    ]
}
```

**Multiple Organisms:**
```python
{
    "ec_number": "2.7.11.24",
    "data_by_organism": {
        "Homo sapiens": {
            "Km_ATP": [15.0, 18.2, 12.5],  # Multiple measurements
            "kcat": [15.8],
            "references": [...]
        },
        "Mus musculus": {
            "Km_ATP": [14.5, 16.8],
            "kcat": [14.2],
            "references": [...]
        },
        "Saccharomyces cerevisiae": {
            "Km_ATP": [22.3],
            "kcat": [8.5],
            "references": [...]
        }
    }
}
```

**SHYpn Use:**
- **Organism filter** - Select organism in model metadata
- **Parameter comparison** - Compare human vs. mouse
- **Cross-species modeling** - Use appropriate parameters
- **Taxonomy display** - Show full classification in reports

---

### 6. **Reaction Information**

**Reaction String:**
```
ATP + a protein = ADP + a phosphoprotein
```

**Detailed Reaction:**
```python
{
    "reaction": {
        "equation": "ATP + protein-serine = ADP + protein-phosphoserine + H+",
        "reversibility": "irreversible",
        "direction": "forward",
        "reaction_type": "phosphoryl transfer",
        "mechanism": "sequential ordered bi bi",
        "substrates": [
            {"name": "ATP", "stoichiometry": 1, "side": "left"},
            {"name": "protein-serine", "stoichiometry": 1, "side": "left"}
        ],
        "products": [
            {"name": "ADP", "stoichiometry": 1, "side": "right"},
            {"name": "protein-phosphoserine", "stoichiometry": 1, "side": "right"},
            {"name": "H+", "stoichiometry": 1, "side": "right"}
        ],
        "cofactors_required": ["Mg2+"],
        "optimal_pH": 7.4,
        "optimal_temperature": 37
    }
}
```

**SHYpn Use:**
- **Stoichiometry** - Arc weights
- **Reversibility** - Model inhibitor arcs if needed
- **Balanced equations** - Verify model conservation
- **Mechanism** - Advanced modeling (ordered substrates)

---

### 7. **Regulatory Information**

**Activators:**
```python
{
    "activators": [
        {
            "name": "Ca2+",
            "type": "allosteric activator",
            "concentration_range": "0.1-1.0 mM",
            "effect": "increases Vmax by 3-fold",
            "mechanism": "conformational change",
            "literature": "PMID:45678901"
        }
    ]
}
```

**Inhibitors:**
```python
{
    "inhibitors": [
        {
            "name": "U0126",
            "type": "competitive inhibitor",
            "Ki": 0.07,
            "Ki_unit": "μM",
            "target": "ATP binding site",
            "reversibility": "reversible",
            "clinical_use": "research tool",
            "literature": "PMID:56789012"
        },
        {
            "name": "product inhibition",
            "inhibitor": "ADP",
            "type": "competitive",
            "Ki": 150,
            "Ki_unit": "μM"
        }
    ]
}
```

**SHYpn Use:**
- **Inhibitor arcs** - Model negative regulation
- **Drug targets** - Pharmaceutical modeling
- **Feedback loops** - Product inhibition
- **Allosteric regulation** - Advanced kinetics

---

### 8. **pH and Temperature Stability**

**pH Profile:**
```python
{
    "ph_optimum": 7.4,
    "ph_range": {
        "minimum": 6.0,
        "maximum": 8.5
    },
    "ph_stability": [
        {"pH": 5.0, "activity": 10, "unit": "% of maximum"},
        {"pH": 6.0, "activity": 45},
        {"pH": 7.0, "activity": 85},
        {"pH": 7.4, "activity": 100},
        {"pH": 8.0, "activity": 90},
        {"pH": 8.5, "activity": 60},
        {"pH": 9.0, "activity": 20}
    ]
}
```

**Temperature Profile:**
```python
{
    "temperature_optimum": 37,
    "temperature_optimum_unit": "°C",
    "temperature_range": {
        "minimum": 15,
        "maximum": 45,
        "unit": "°C"
    },
    "temperature_stability": [
        {"temp": 25, "activity": 45, "unit": "% of maximum"},
        {"temp": 30, "activity": 75},
        {"temp": 37, "activity": 100},
        {"temp": 42, "activity": 85},
        {"temp": 50, "activity": 10}
    ],
    "thermal_inactivation": {
        "t_half": 15,
        "t_half_unit": "min",
        "temperature": 50,
        "temperature_unit": "°C"
    }
}
```

**SHYpn Use:**
- **Condition modeling** - Adjust rates for pH/temperature
- **Stability analysis** - Long-term simulations
- **Experimental design** - Optimal conditions for validation

---

### 9. **Localization and Expression**

**Subcellular Localization:**
```python
{
    "localization": [
        {
            "compartment": "cytoplasm",
            "abundance": "high",
            "evidence": "immunofluorescence"
        },
        {
            "compartment": "nucleus",
            "abundance": "low",
            "condition": "upon stimulation",
            "evidence": "Western blot"
        }
    ]
}
```

**Tissue Expression:**
```python
{
    "tissue_expression": [
        {"tissue": "brain", "level": "high"},
        {"tissue": "heart", "level": "high"},
        {"tissue": "liver", "level": "medium"},
        {"tissue": "skeletal muscle", "level": "high"},
        {"tissue": "kidney", "level": "low"}
    ]
}
```

**SHYpn Use:**
- **Compartmentalization** - Model cellular locations
- **Tissue-specific models** - Use appropriate expression levels
- **Initial concentrations** - Set based on expression data

---

### 10. **Literature References**

**Citation Data:**
```python
{
    "references": [
        {
            "pmid": "12345678",
            "doi": "10.1016/j.jbc.2020.01.001",
            "authors": "Smith J, Doe J, Johnson A",
            "title": "Kinetic characterization of human MAP kinase kinase kinase",
            "journal": "Journal of Biological Chemistry",
            "year": 2020,
            "volume": 295,
            "issue": 10,
            "pages": "3421-3435",
            "abstract": "...",
            "url": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
        }
    ]
}
```

**SHYpn Use:**
- **Auto-bibliography** - Generate reference list for reports
- **Parameter provenance** - Track data sources
- **Quality assessment** - Prefer well-cited parameters
- **PubMed links** - Direct access to papers

---

## BRENDA API Access

### Authentication

**API Key Required:**
1. Register at https://www.brenda-enzymes.org/
2. Request API key (free for academic use)
3. Include in all API requests

**Storage in SHYpn:**
```python
# Secure credential storage
from shypn.credentials import CredentialsManager

cred_mgr = CredentialsManager()
cred_mgr.store_credential(
    service="brenda",
    credential_type="api_key",
    value="your-api-key-here"
)
```

### API Endpoints

**SOAP API (Recommended):**
```python
from SOAPpy import WSDL

wsdl = "https://www.brenda-enzymes.org/soap/brenda_server.wsdl"
client = SOAPpy.WSDL.Proxy(wsdl)

# Example: Get EC number information
result = client.getEcNumber(
    ecNumber="2.7.11.24",
    email="user@example.com",
    password="api-key-here"
)
```

**REST API (Alternative):**
```python
import requests

url = "https://www.brenda-enzymes.org/rest/ec/2.7.11.24"
headers = {"Authorization": "Bearer your-api-key"}
response = requests.get(url, headers=headers)
data = response.json()
```

---

## Data Organization for SHYpn

### Metadata Schema

```python
class TransitionMetadata:
    """Metadata for Petri net transitions (enzymes/reactions)."""
    
    def __init__(self):
        # Identity
        self.ec_number = ""
        self.systematic_name = ""
        self.recommended_name = ""
        self.synonyms = []
        
        # Reaction
        self.reaction_equation = ""
        self.substrates = []
        self.products = []
        self.cofactors = []
        
        # Kinetics
        self.kinetic_parameters = []  # List of KineticParameter objects
        
        # Context
        self.organism = ""
        self.tissue = ""
        self.localization = []
        
        # Regulation
        self.activators = []
        self.inhibitors = []
        
        # Conditions
        self.ph_optimum = None
        self.temperature_optimum = None
        
        # Provenance
        self.data_source = "BRENDA"
        self.retrieval_date = None
        self.references = []


class KineticParameter:
    """Single kinetic parameter measurement."""
    
    def __init__(self):
        self.type = ""  # "Km", "kcat", "Ki", "Vmax", etc.
        self.value = None
        self.unit = ""
        self.substrate = ""  # or inhibitor
        self.organism = ""
        self.conditions = {}  # pH, temp, buffer, etc.
        self.method = ""
        self.reference_pmid = ""
```

---

## Query Workflow in SHYpn

### User Scenario:

1. **User creates transition** in Petri net
2. **User names transition** "ERK phosphorylation"
3. **User opens property dialog** → "Query BRENDA" button
4. **Search dialog appears:**
   ```
   Search BRENDA
   ─────────────────────────────
   Search by:
   ○ Enzyme name: [ERK kinase________________]
   ○ EC number:   [2.7.11.24________________]
   ○ Reaction:    [ATP phosphorylation______]
   
   Organism filter: [Homo sapiens   ▼]
   
   [Search]  [Cancel]
   ```

5. **Results displayed:**
   ```
   BRENDA Results for "ERK kinase"
   ═══════════════════════════════════════════
   
   ✓ EC 2.7.11.24 - MAP kinase kinase kinase
     Systematic: ATP:protein phosphotransferase
     Organism: Homo sapiens (25 entries)
     
     Kinetic Parameters Available:
     • Km (ATP): 15.0 ± 3.2 μM (n=8 studies)
     • kcat: 15.8 s⁻¹ (n=3 studies)
     • Ki (U0126): 0.07 μM (n=5 studies)
     
     [View Details]  [Import Data]
   ```

6. **User clicks "Import Data"**
7. **Data imported to transition metadata**
8. **Transition property dialog updates:**
   ```
   Transition Properties
   ─────────────────────────────────────────
   Name: ERK phosphorylation
   EC Number: 2.7.11.24 (from BRENDA)
   
   Kinetic Parameters (from BRENDA):
   • Km (ATP): 15.0 μM (H. sapiens, 37°C, pH 7.4)
     Reference: Smith et al. 2020 (PMID:12345678)
   
   [Use in Simulation]  [View Full Dataset]
   ```

9. **User simulates** → Parameters used automatically
10. **User generates report** → BRENDA data cited automatically

---

## Priority Data for SHYpn MVP

### Phase 1 (Essential):
1. ✅ **EC number** → Classification
2. ✅ **Enzyme names** → Identification
3. ✅ **Km values** → Substrate affinity
4. ✅ **kcat values** → Turnover rate
5. ✅ **Organism** → Context
6. ✅ **Literature references** → Citations

### Phase 2 (Important):
7. **Vmax** → Maximum velocity
8. **Ki values** → Inhibition
9. **Substrate/product names** → Stoichiometry
10. **pH/temperature optima** → Conditions

### Phase 3 (Advanced):
11. **Activators/inhibitors** → Regulation
12. **Tissue expression** → Biological context
13. **Localization** → Compartmentalization
14. **Alternative organisms** → Cross-species

---

## Summary

### What BRENDA Provides:

| Category | Data | SHYpn Use |
|----------|------|-----------|
| **Identity** | EC numbers, names, synonyms | Transition labeling |
| **Kinetics** | Km, kcat, Vmax, Ki | Simulation parameters |
| **Reactions** | Substrates, products, stoichiometry | Arc weights, conservation |
| **Context** | Organism, tissue, localization | Model metadata |
| **Regulation** | Activators, inhibitors | Regulatory arcs |
| **Conditions** | pH, temperature | Condition-specific modeling |
| **Provenance** | Literature references | Citations, quality |

### Value Proposition:

**Without BRENDA:** User manually looks up parameters → Time-consuming, error-prone  
**With BRENDA:** One-click parameter import → Fast, accurate, cited

**Metadata Quality:**
- ✅ Scientific rigor (peer-reviewed data)
- ✅ Provenance (literature citations)
- ✅ Technical precision (organism, conditions)
- ✅ Professional reports (auto-bibliography)

---

**Status:** 📊 READY FOR IMPLEMENTATION  
**Next Step:** Design BRENDA connector architecture  
**Estimated Time:** 1 week for basic connector + UI
