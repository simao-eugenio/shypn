# BRENDA Integration Plan

**Date**: October 28, 2025  
**Status**: Planning Phase  
**Related**: SBML_KINETIC_INTEGRATION_PLAN.md, KEGG implementation

---

## Executive Summary

BRENDA (BRaunschweig ENzyme DAtabase) will be integrated as **Universal Kinetic Enrichment Layer**:

1. **Primary Purpose**: Provide high-quality kinetic parameters (Km, Vmax, kcat, Ki) for ALL models
2. **Secondary Purpose**: Cross-reference enzymes to external pathway databases (KEGG, MetaCyc, Reactome)

**Key Principle**: BRENDA enrichment supports models from any source (KEGG, BioModels, manual drawing).

**Critical Insight**: BRENDA pathways are **metadata pointers** to external databases, NOT native pathway models. BRENDA provides enzyme-centric data that connects to real pathways maintained by KEGG, MetaCyc, and Reactome.

---

## Architecture Overview

### Current State (Before BRENDA)
```
Pathway Sources:
  ├─ KEGG Pathways
  ├─ BioModels (SBML)
  └─ Manual Drawing
       ↓
  [Enrichment: Local DB + Heuristics]
```

### **NEW Architecture (With BRENDA)**
```
┌─────────────────────────────────────────────────────┐
│          PRIMARY PATHWAY SOURCES                     │
├─────────────────────────────────────────────────────┤
│  1. KEGG Pathways          (REST API)               │
│  2. BioModels              (SBML files)             │
│  3. Manual Drawing         (User-created)           │
└─────────────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│     UNIVERSAL ENRICHMENT LAYER (All Models)         │
├─────────────────────────────────────────────────────┤
│  Tier 1: SBML Explicit     (Definitive, 1.0)       │
│  Tier 2: ⭐ BRENDA API     (High, 0.8-0.9) [NEW]   │
│            • Km, Vmax, kcat, Ki from experiments    │
│            • Organism-specific parameters           │
│            • Literature references (PMID)           │
│  Tier 3: Database Lookup   (Medium-High, 0.7-0.8)  │
│  Tier 4: Heuristic         (Medium, 0.5-0.6)       │
│  Tier 5: Default           (Low, 0.3)               │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│          PATHWAY CROSS-REFERENCES (Optional)         │
├─────────────────────────────────────────────────────┤
│  ⭐ BRENDA Pathway Metadata:                        │
│     - Links enzymes → external pathway databases    │
│     - Sources: KEGG, MetaCyc, Reactome, BioCyc     │
│     - Enzyme-centric pathway associations           │
└─────────────────────────────────────────────────────┘
```

---

## Dual-Module Design

### Module 1: BRENDA Kinetics Database (PRIMARY)
**Purpose**: Universal kinetic parameter enrichment for ALL models  
**Location**: `src/shypn/data/brenda_kinetics_api.py` (rename from enzyme_kinetics_api.py)  
**Used by**: All pathway sources (KEGG, SBML, manual)

#### Three-Tier Database (Enhanced):
```
┌────────────────────────────────────────┐
│ Tier 1: Local SQLite Cache            │
│ - Fast repeated lookups (<10ms)       │
│ - 30-day TTL                           │
│ - Location: ~/.shypn/cache/           │
└────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────┐
│ Tier 2: ⭐ BRENDA SOAP API [NEW]      │
│ - 83,000+ enzymes                      │
│ - Organism-specific data               │
│ - Literature references (PMID)         │
│ - Requires authentication              │
└────────────────────────────────────────┘
              ↓
┌────────────────────────────────────────┐
│ Tier 3: Fallback Database              │
│ - 10 glycolysis enzymes                │
│ - Offline capability                   │
│ - Bundled with app                     │
└────────────────────────────────────────┘
```

#### Key Features:
- Query by EC number and organism
- Fetch kinetic parameters (Km, Vmax, kcat, Ki)
- Extract literature references (PMID)
- Organism-specific filtering
- Automatic kinetic metadata creation
- Cache results for performance

#### API Methods (from BRENDA SOAP):
- `getKmValue()` - Fetch Km values
- `getKcatValue()` - Fetch kcat values  
- `getVmaxValue()` - Fetch Vmax values
- `getKiValue()` - Fetch inhibition constants
- `getTurnoverNumber()` - Fetch turnover numbers
- `getOrganism()` - Get organism info

### Module 2: BRENDA Pathway Cross-Reference (SECONDARY)
**Purpose**: Link enzymes to external pathway databases  
**Location**: `src/shypn/data/brenda_pathway_xref.py` (NEW)  
**Used by**: Optional pathway discovery and cross-referencing

#### Data Structure:
```python
@dataclass
class BRENDAPathwayReference:
    """Metadata pointer to external pathway database."""
    ec_number: str              # EC 2.7.1.1
    pathway_name: str           # "Glycolysis"
    external_link: str          # URL to KEGG/MetaCyc/Reactome
    source_database: str        # "KEGG", "MetaCyc", "Reactome"
    organism: Optional[str]     # Organism context
```

#### Key Features:
- Discover which pathways contain an enzyme
- Get links to external pathway databases
- Cross-reference with existing KEGG/SBML models
- No native pathway models imported

#### API Methods:
- `getPathway()` - Get pathway associations for EC number
- Returns: pathway name, external link, source database

**Important**: BRENDA pathways are **metadata only**, not executable models. Use KEGG or BioModels for actual pathway imports.

---

## Implementation Phases

### Phase 1: BRENDA API Client (2 weeks)

**Goal**: Establish BRENDA SOAP connection and credential management

#### Tasks:

1. **Credential Storage** (2 days)
   - Create credential config system
   - Store credentials securely (encrypted or OS keyring)
   - Fallback to environment variables
   - Add to user preferences dialog

2. **SOAP Client Wrapper** (3 days)
   - Create `BRENDAAPIClient` class
   - Implement authentication (SHA256 hashing)
   - Handle SOAP faults gracefully
   - Add connection pooling for performance
   - Implement retry logic with exponential backoff

3. **Basic Query Methods** (3 days)
   - `query_ec_number(ec: str, organism: str = None)`
   - `query_km_values(ec: str, organism: str = None)`
   - `query_vmax_values(ec: str, organism: str = None)`
   - `query_kcat_values(ec: str, organism: str = None)`
   - Parse BRENDA response format

4. **Response Parsing** (2 days)
   - Parse BRENDA XML/text format
   - Extract kinetic parameters
   - Extract organism information
   - Extract literature references (PMID)
   - Handle missing/incomplete data

**Files to Create**:
- `src/shypn/data/brenda_soap_client.py`
- `src/shypn/config/credentials_manager.py`

**Success Criteria**:
- ✓ Successfully authenticate with BRENDA
- ✓ Fetch Km values for EC 2.7.1.1 (Hexokinase)
- ✓ Parse and return structured data
- ✓ Handle network errors gracefully

---

### Phase 2: BRENDA Kinetics Integration (2 weeks)

**Goal**: Integrate BRENDA as Tier 2 in enrichment system

#### Tasks:

1. **Rename and Refactor** (2 days)
   - Rename `enzyme_kinetics_api.py` → `brenda_kinetics_api.py`
   - Update imports across codebase
   - Add BRENDA-specific methods
   - Maintain backward compatibility

2. **Implement `_fetch_from_api()`** (3 days)
   - Complete TODO in `brenda_kinetics_api.py`
   - Call BRENDA SOAP client
   - Parse kinetic parameters
   - Handle organism filtering
   - Cache results to SQLite

3. **Organism Priority System** (2 days)
   - Define organism preference order:
     * Homo sapiens (human) - highest priority
     * Mus musculus (mouse)
     * Rattus norvegicus (rat)
     * Generic/multiple organisms
   - Weighted confidence based on organism match
   - Allow user configuration

4. **Update DatabaseKineticMetadata** (2 days)
   - Add BRENDA-specific fields
   - Track organism source
   - Store literature references (PMID)
   - Add confidence adjustments based on organism

5. **Testing** (3 days)
   - Test with multiple EC numbers
   - Test organism filtering
   - Test cache hit/miss scenarios
   - Test offline fallback

**Files to Modify**:
- `src/shypn/data/enzyme_kinetics_api.py` → `brenda_kinetics_api.py`
- `src/shypn/data/kinetics/kinetic_metadata.py`
- `src/shypn/heuristic/kinetics_assigner.py`

**Success Criteria**:
- ✓ BRENDA queries integrated into enrichment flow
- ✓ Parameters cached correctly
- ✓ Organism filtering works
- ✓ Confidence scores reflect data quality

---

### Phase 3: Pathway Cross-Reference Service (1 week)

**Goal**: Optional enzyme-to-pathway cross-referencing using BRENDA metadata

#### Tasks:

1. **Data Models** (2 days)
   - Create `BRENDAPathwayReference` dataclass
   - Store pathway name, external link, source database
   - No native pathway model parsing needed

2. **Cross-Reference API** (2 days)
   - Implement `query_pathway_references(ec: str)`
   - Parse BRENDA pathway metadata response
   - Extract external database links
   - Handle multiple pathway associations

3. **UI Integration** (2 days)
   - Add "Pathway Info" button to transition properties
   - Show associated pathways for enzyme
   - Display external links (KEGG, MetaCyc, Reactome)
   - Open external pathway in browser

4. **Documentation** (1 day)
   - Document pathway cross-reference feature
   - Explain metadata-only nature
   - Provide examples of usage

**Files to Create**:
- `src/shypn/data/brenda_pathway_xref.py`
- `src/shypn/data/models.py` (add BRENDAPathwayReference)

**Success Criteria**:
- ✓ Query pathway associations by EC number
- ✓ Display external pathway links
- ✓ Users can navigate to source databases
- ✓ Clear that BRENDA provides metadata, not models

---

### Phase 4: Universal Enrichment Service (2 weeks)

**Goal**: Unified enrichment service that works for ALL model types

#### Tasks:

1. **Universal Enrichment Service** (4 days)
   - Create `UniversalKineticEnrichmentService`
   - Works on any DocumentModel (regardless of source)
   - Prioritizes enrichment tiers:
     * SBML explicit (never overwrite)
     * BRENDA kinetics (high confidence)
     * Database lookup (medium-high)
     * Heuristic (medium)

2. **Batch Enrichment** (3 days)
   - Enrich multiple transitions at once
   - Show progress dialog
   - Allow selective enrichment
   - Preview before applying

3. **Enrichment Dialog UI** (4 days)
   - Menu: `Tools → Enrich Kinetics...`
   - Show all transitions with current status
   - Display available BRENDA data
   - Confidence indicators
   - Apply/Cancel buttons

4. **Integration with All Importers** (3 days)
   - Update KEGG importer to use universal service
   - Update SBML importer (already done in Phase 1)
   - Update BRENDA importer
   - Manual models can be enriched post-hoc

**Files to Create**:
- `src/shypn/services/universal_enrichment_service.py`
- `ui/dialogs/enrich_kinetics_dialog.ui`
- `src/shypn/helpers/enrich_kinetics_dialog.py`

**Success Criteria**:
- ✓ Any model can be enriched
- ✓ BRENDA data preferred over heuristics
- ✓ User has full control
- ✓ Enrichment history tracked

---

### Phase 5: Project Metadata & Reporting (1.5 weeks)

**Goal**: Track BRENDA enrichment in project metadata and reports

#### Tasks:

1. **Extend Project Metadata** (2 days)
   - Add `brenda_enrichments` section
   - Track which transitions enriched from BRENDA
   - Track organism sources
   - Track literature references

2. **Enrichment Report** (3 days)
   - Generate report of BRENDA-enriched transitions
   - Include organism information
   - Include confidence scores
   - Include PMID citations

3. **Export for Publications** (2 days)
   - Export enrichment data to CSV
   - Export citations in BibTeX format
   - Include in project documentation

**Files to Modify**:
- `src/shypn/data/project_models.py`
- `src/shypn/analysis/kinetic_report_generator.py`

**Success Criteria**:
- ✓ BRENDA enrichments tracked in project
- ✓ Reports include BRENDA citations
- ✓ Exportable for publications

---

## Credential Management

### Security Considerations:

1. **Never commit credentials to git**
   - Add `brenda_credentials.txt` to `.gitignore`
   - Add `*.credentials` to `.gitignore`

2. **Storage Options** (Priority order):
   - **Option 1**: OS Keyring (most secure)
     * Linux: SecretStorage/Keyring
     * macOS: Keychain
     * Windows: Credential Manager
   - **Option 2**: Encrypted config file
     * AES-256 encryption
     * Key derived from user password
   - **Option 3**: Environment variables
     * `BRENDA_EMAIL`, `BRENDA_PASSWORD`
   - **Option 4**: Plain text config (development only)

3. **User Preferences UI**:
   - Settings → BRENDA Credentials
   - Test connection button
   - Clear cached credentials

### Credential Flow:

```python
# Priority order
credentials = (
    load_from_keyring() or
    load_from_encrypted_config() or
    load_from_env_vars() or
    load_from_config_file() or
    prompt_user()
)
```

---

## Data Model Updates

### DatabaseKineticMetadata (Enhanced)

```python
@dataclass
class DatabaseKineticMetadata(KineticMetadata):
    """Enhanced for BRENDA integration."""
    
    # Existing fields
    ec_number: Optional[str] = None
    organism: Optional[str] = None
    database: Optional[str] = None  # "brenda", "kegg", "sabio-rk"
    database_id: Optional[str] = None
    
    # NEW: BRENDA-specific fields
    brenda_organism_id: Optional[str] = None  # BRENDA organism ID
    organism_match_score: float = 1.0  # How well organism matches (0-1)
    literature_refs: List[str] = field(default_factory=list)  # PMID list
    experimental_conditions: Optional[Dict] = None  # pH, temp, etc.
    data_quality_flag: Optional[str] = None  # From BRENDA
    
    def __post_init__(self):
        """Set confidence based on organism match."""
        self.source = KineticSource.DATABASE
        
        # Adjust confidence based on organism match
        if self.organism_match_score >= 0.9:
            self.confidence = ConfidenceLevel.MEDIUM_HIGH
            self.confidence_score = 0.85
        elif self.organism_match_score >= 0.7:
            self.confidence_score = 0.75
        else:
            self.confidence_score = 0.65
```

---

## API Integration Details

### BRENDA SOAP Methods (Key Ones)

**Authentication**:
```python
email = "user@example.com"
password_hash = hashlib.sha256(password.encode()).hexdigest()
```

**Query Km Values**:
```python
result = client.service.getKmValue(
    email,                        # User email
    password_hash,                # SHA256 hash
    "ecNumber*2.7.1.1",          # EC filter
    "organism*Homo sapiens",      # Organism filter
    "kmValue*",                   # All Km values
    "kmValueMaximum*",            # Maximum values
    "substrate*",                 # All substrates
    "commentary*",                # Comments
    "ligandStructureId*",         # Ligand IDs
    "literature*"                 # Literature refs
)
```

**Query Vmax Values**:
```python
result = client.service.getVmaxValue(
    email, password_hash,
    "ecNumber*2.7.1.1",
    "organism*Homo sapiens",
    "vmaxValue*",
    "substrate*",
    "commentary*",
    "literature*"
)
```

### Response Format (Example):
```
#ecNumber*2.7.1.1#
#organism*Homo sapiens#
#kmValue*0.15#
#kmValueMaximum*0.2#
#substrate*glucose#
#literature*12345678#
```

---

## Testing Strategy

### Unit Tests:

1. **BRENDA Client Tests** (`tests/test_brenda_client.py`)
   - Test authentication
   - Test query methods
   - Test response parsing
   - Mock SOAP responses

2. **Enrichment Tests** (`tests/test_brenda_enrichment.py`)
   - Test parameter extraction
   - Test organism filtering
   - Test confidence scoring
   - Test metadata creation

3. **Integration Tests** (`tests/test_brenda_integration.py`)
   - Test end-to-end enrichment
   - Test with real BRENDA account
   - Test cache behavior
   - Test offline fallback

### Manual Tests:

1. **Connectivity Test**:
   ```bash
   python3 tests/test_brenda_soap_config.py
   ```

2. **Enrichment Test**:
   - Import KEGG pathway
   - Apply BRENDA enrichment
   - Verify parameters added
   - Check confidence scores

3. **Cross-Source Test**:
   - Import SBML (BioModels)
   - Enrich with BRENDA
   - Verify SBML data preserved
   - BRENDA fills gaps only

---

## Timeline Summary

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1: API Client | 2 weeks | SOAP connection, credentials |
| Phase 2: Kinetics Integration | 2 weeks | Tier 2 enrichment |
| Phase 3: Pathway Cross-Reference | 1 week | Metadata links (optional) |
| Phase 4: Universal Service | 2 weeks | Unified enrichment |
| Phase 5: Metadata & Reports | 1.5 weeks | Project tracking |
| **Total** | **8.5 weeks** | **Complete BRENDA integration** |

---

## Success Metrics

### Technical Metrics:
- ✅ BRENDA authentication successful
- ✅ Kinetic parameters fetched and cached
- ✅ Pathways imported from BRENDA
- ✅ Enrichment works for all model types
- ✅ Organism filtering functional
- ✅ Cache hit rate > 70%

### User Experience Metrics:
- ✅ BRENDA tab accessible and intuitive
- ✅ Enrichment dialog clear and helpful
- ✅ Progress indicators for API calls
- ✅ Error messages actionable
- ✅ Citations properly attributed

### Quality Metrics:
- ✅ Average confidence score > 0.8 for BRENDA data
- ✅ Organism match > 80% for human models
- ✅ < 5% failed enrichments
- ✅ API response time < 2 seconds

---

## Migration & Compatibility

### Backward Compatibility:

1. **Existing Projects**:
   - Old projects load without BRENDA data
   - Can be enriched retroactively
   - No data loss

2. **Existing Enrichments**:
   - Legacy enrichments preserved
   - Can be upgraded to BRENDA data
   - User prompted for upgrade

3. **API Naming**:
   - `enzyme_kinetics_api.py` → `brenda_kinetics_api.py`
   - Keep alias for compatibility:
     ```python
     # src/shypn/data/enzyme_kinetics_api.py
     from .brenda_kinetics_api import BRENDAKineticsAPI as EnzymeKineticsAPI
     ```

---

## Future Enhancements (Post-Release)

1. **Multi-Database Support**:
   - Add SABIO-RK as Tier 2B
   - Add MetaCyc as Tier 2C
   - Merge results from multiple sources

2. **Machine Learning Confidence**:
   - Train on validated BRENDA data
   - Predict confidence for new enzymes
   - Active learning from user corrections

3. **Collaborative Curation**:
   - Users submit corrections
   - Peer review system
   - Community parameter database

4. **Real-Time Updates**:
   - Subscribe to BRENDA updates
   - Auto-refresh stale cache entries
   - Notify users of new data

---

## Dependencies

### Python Packages (Add to requirements.txt):
```
zeep>=4.2.1          # BRENDA SOAP client
cryptography>=41.0   # Credential encryption
keyring>=24.0        # OS keyring access
```

### Optional:
```
lxml>=4.9.0          # XML parsing (zeep dependency)
requests>=2.31.0     # HTTP fallback
```

---

## Risk Assessment

### High Risk:
- **BRENDA API availability**: Mitigation → Cache + fallback DB
- **Rate limiting**: Mitigation → Intelligent caching, batch requests
- **Authentication changes**: Mitigation → Modular auth system

### Medium Risk:
- **Response format changes**: Mitigation → Robust parsing, version detection
- **Network latency**: Mitigation → Async requests, timeout handling
- **Organism name variations**: Mitigation → Fuzzy matching, synonym database

### Low Risk:
- **Cache corruption**: Mitigation → Auto-rebuild, checksum validation
- **UI complexity**: Mitigation → Phased rollout, user testing

---

## Conclusion

BRENDA integration as **universal enrichment layer** provides:

1. **High-Quality Kinetic Data**: Km, Vmax, kcat, Ki from 83,000+ enzymes
2. **Experimental Validation**: Data extracted from peer-reviewed literature
3. **Universal Support**: Works for ALL model types (KEGG, SBML, manual)
4. **Organism Specificity**: Human/mouse/rat preference for biomedical research
5. **Literature Integration**: PMID references for publications
6. **Pathway Discovery**: Cross-reference enzymes to KEGG/MetaCyc/Reactome

**Architectural Clarity**:
- ✅ **PRIMARY**: Kinetic parameter enrichment (Tier 2 in enrichment hierarchy)
- ✅ **SECONDARY**: Pathway metadata cross-referencing (optional feature)
- ❌ **NOT**: Native pathway model importer (use KEGG/BioModels instead)

**Why This Architecture**:
BRENDA is fundamentally an **enzyme database**, not a pathway modeling tool. While it provides valuable pathway associations, these are metadata pointers to external databases (KEGG, MetaCyc, Reactome) rather than complete, executable pathway models. Using BRENDA for what it does best—providing high-quality experimental kinetic parameters—ensures the most reliable and maintainable integration.

**Next Steps**:
1. Set up BRENDA credentials
2. Test connection (`test_brenda_soap_config.py`)
3. Begin Phase 1 implementation

---

**Status**: Ready for implementation after credential activation confirmation.
