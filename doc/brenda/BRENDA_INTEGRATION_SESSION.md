# BRENDA Integration Planning Session
**Date:** October 24, 2025  
**Status:** Authentication Confirmed, Architecture Designed

---

## Session Summary

This session focused on planning and initial implementation of BRENDA enzyme database integration for the SHYpn reporting system. Key accomplishments include confirming authentication requirements, designing the automated enrichment pipeline, and beginning UI integration.

---

## 1. Authentication Requirements ✅ CONFIRMED

### BRENDA API Access:
- **Registration Required:** YES - Free academic registration at https://www.brenda-enzymes.org/register.php
- **Authentication Method:** Email + Password (SHA256 hashed)
- **API Type:** SOAP API (Zeep library for Python 3)
- **License:** Free under CC BY 4.0 for academic use
- **Registration Process:**
  1. User registers at BRENDA website
  2. Email confirmation (minutes)
  3. **Database refresh by BRENDA admin (1-2 business days)** ⏰
  4. Credentials become active

### Important Notes:
- User experienced: Registration → Confirmation email → Awaiting database refresh
- **UX Implication:** System must work WITHOUT BRENDA initially
- Auto-enrichment is an **optional enhancement**, not a requirement
- Need "Test Connection" button to verify credentials are active

---

## 2. BRENDA Data Categories

### Available Data (10 Categories):

1. **EC Numbers** - Enzyme classification (EC x.y.z.w)
2. **Enzyme Names** - Systematic, recommended, synonyms
3. **Kinetic Parameters** ⭐ MOST VALUABLE
   - Km (substrate affinity)
   - kcat (turnover number)
   - Vmax (maximum velocity)
   - Ki (inhibition constant)
4. **Substrates & Products** - With ChEBI IDs
5. **Organism-Specific Data** - Human, mouse, yeast, etc.
6. **Reaction Information** - Stoichiometry, reversibility
7. **Regulatory Information** - Activators, inhibitors
8. **pH/Temperature Stability** - Optima and ranges
9. **Localization & Expression** - Tissue, subcellular
10. **Literature References** ⭐ - PubMed IDs, DOIs

### MVP Priority (Phase 1):
- ✅ EC numbers → Classification
- ✅ Enzyme names → Identification
- ✅ Km values → Substrate affinity (direct simulation parameter)
- ✅ kcat values → Turnover rate (direct simulation parameter)
- ✅ Organism filter → Context specificity
- ✅ Citations → Auto-bibliography

---

## 3. Automated Enrichment Pipeline Architecture

### Game-Changing Workflow:

```
Import SBML/KEGG Pathway (18 transitions)
  ↓
[SBMLAnalyzer / KEGGAnalyzer]
Extract: EC numbers, enzyme names, identifiers
Identify: Gaps in kinetic parameters
  ↓
[AutoEnrichmentEngine]
Query BRENDA for each enzyme (organism-specific)
Import: Km, kcat, names, citations
Cache: Results locally
  ↓
[GapAnalyzer]
Categorize gaps:
  🔴 Critical: Missing kinetics (blocks simulation)
  🟡 Important: Missing citations (reduces quality)
  🟢 Optional: Missing ChEBI IDs (nice to have)
  ↓
[EnrichmentWizard - Interactive UI]
Guide user through resolution:
  - Show BRENDA search links for manual lookup
  - Offer alternative organisms
  - Suggest reasonable defaults
  ↓
[EnrichedReportGenerator]
Generate report with provenance markers:
  ✅ "Km = 15.0 μM (BRENDA, Smith 2020, PMID:12345678)"
  ⚠️  "Kinetics estimated (no Homo sapiens data)"
  ❌ "Manual entry required [Search Links]"
```

### Impact:
- **Before:** 2-3 DAYS of manual BRENDA searches for 20 enzymes
- **After:** 15 MINUTES automated import with 85% → 98% completion
- **Auto-bibliography:** PubMed citations extracted automatically

---

## 4. Implementation Organization

### Directory Structure:

```
doc/brenda/                           # Documentation
├── BRENDA_DATA_REFERENCE.md          # Comprehensive data catalog
├── AUTO_ENRICHMENT_PIPELINE.md       # Pipeline architecture
├── BRENDA_INTEGRATION_SESSION.md     # This file
└── (future: USER_GUIDE.md, DEVELOPER_GUIDE.md)

src/shypn/data/brenda/                # BRENDA connector code
├── base_connector.py                 # Abstract base class
├── brenda_connector.py               # Main SOAP client
├── soap_client.py                    # Zeep-based SOAP wrapper
├── cache_manager.py                  # Local caching
├── rate_limiter.py                   # API throttling
└── models.py                         # Data models (KineticParameter, etc.)

src/shypn/credentials/                # Credentials management
├── credentials_manager.py            # Encrypt/decrypt storage
├── user_profile.py                   # UserProfile with BRENDA fields
└── authenticators.py                 # SHA256 password hashing

src/shypn/enrichment/                 # Auto-enrichment engine
├── auto_enrichment_engine.py         # Main pipeline coordinator
├── sbml_analyzer.py                  # Extract from SBML
├── kegg_analyzer.py                  # Extract from KEGG
├── gap_analyzer.py                   # Identify missing data
└── enriched_report_generator.py     # Generate reports

src/shypn/ui/                         # UI components
├── preferences/
│   └── credentials_dialog.py         # BRENDA credentials entry
└── enrichment/
    └── enrichment_wizard.py          # Gap resolution wizard
```

### Architecture Principles:
- ✅ OOP with base class + subclasses
- ✅ Separate files for each class
- ✅ Minimize code in loaders (logic in core classes)
- ✅ Clean separation of concerns

---

## 5. SOAP API Example (Python 3)

### Authentication Pattern:

```python
from zeep import Client, Settings
import hashlib

# Setup
wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
password = hashlib.sha256("myPassword".encode("utf-8")).hexdigest()
settings = Settings(strict=False)
client = Client(wsdl, settings=settings)

# Query Km values for enzyme
parameters = (
    "j.doe@example.edu",      # Email
    password,                  # SHA256 hashed password
    "ecNumber*1.1.1.1",       # EC number
    "organism*Homo sapiens",   # Organism filter
    "kmValue*",                # Request Km values
    "substrate*",              # Request substrate info
    "literature*"              # Request citations
)
result = client.service.getKmValue(*parameters)
print(result)
```

### Available Methods (159 total):
- `getKmValue()` - Michaelis constant
- `getTurnoverNumber()` - kcat values
- `getKiValue()` - Inhibition constants
- `getEnzymeNames()` - Names and synonyms
- `getReference()` - Literature citations
- Plus 154 more methods for comprehensive data

---

## 6. User Experience Design

### Phase 1: System Works WITHOUT BRENDA
```
Manual Data Entry
├── User imports KEGG/SBML
├── User enters kinetic parameters manually
├── User adds citations manually
└── Reports generated (without BRENDA enrichment)
```

### Phase 2: BRENDA Registration (1-2 days)
```
User Registers
├── Goes to brenda-enzymes.org/register.php
├── Receives confirmation email
├── Waits for admin approval (1-2 business days)
└── Receives activation notification
```

### Phase 3: Credentials Setup
```
SHYpn Preferences
├── Edit → Preferences → User Profile
├── BRENDA Integration section:
│   ├── Email: [input field]
│   ├── Password: [password field]
│   └── Status: ⏳ Pending / ❌ Invalid / ✅ Active
├── [Test Connection] button
└── Help text: "Registration takes 1-2 days"
```

### Phase 4: Auto-Enrichment Enabled
```
Import Pathway
├── User imports KEGG MAPK pathway (18 transitions)
├── Clicks "Auto-Enrich from BRENDA"
├── Progress bar: "Querying BRENDA... 15/18 enzymes"
├── Results: 85% complete → 98% complete (15 minutes)
└── Report generated with:
    ├── ✅ BRENDA-verified data (green highlights)
    ├── ⚠️  Partial data (yellow highlights)
    ├── ❌ Manual needed (red highlights + search links)
    └── 📚 Auto-generated bibliography
```

---

## 7. Pathway Panel Updates

### Current UI Changes:

The Pathway Operations panel now has **3 tabs**:

1. **KEGG** (renamed from "Import")
   - KEGG pathway import interface
   - Existing KEGGImportPanel controller (working)

2. **SBML** (existing, working)
   - SBML file import interface
   - Existing SBMLImportPanel controller (working)

3. **BRENDA** (new placeholder)
   - Auto-enrichment interface
   - Credentials status indicator
   - "Auto-Enrich" button
   - Gap resolution wizard
   - Phase 4: Wire BRENDAConnector

### Removed:
- ❌ "Browse" tab (unused future placeholder)
- ❌ "History" tab (unused future placeholder)

### Files Modified:
- `ui/panels/pathway_panel.ui` - Renamed tab, added BRENDA placeholder

---

## 8. Implementation Timeline

### Week 1: Foundation (WITHOUT BRENDA)
- Manual kinetic parameter entry
- Model metadata dialogs
- Report generation (PDF/Excel)
- User profile system

### Week 2: BRENDA Integration Prep
- Credentials manager with encryption
- User profile dialog with BRENDA fields
- Connection testing infrastructure
- SOAP client wrapper (Zeep)

### Week 3: BRENDA Connector
- Base connector class
- BRENDA connector implementation
- Local caching
- Rate limiting

### Week 4: Auto-Enrichment Engine
- SBML analyzer
- KEGG analyzer
- Auto-enrichment coordinator
- Gap analyzer

### Week 5: UI & Testing
- Enrichment wizard dialog
- Gap resolution interface
- Full pipeline testing
- User documentation

---

## 9. Testing Strategy

### Test Cases:

1. **Without Credentials**
   - ✅ System works with manual entry
   - ✅ BRENDA features gracefully disabled
   - ✅ Clear messaging about registration

2. **With Pending Credentials**
   - ⏳ "Test Connection" shows pending status
   - ⏳ Help text explains 1-2 day approval
   - ⏳ System continues working manually

3. **With Active Credentials**
   - ✅ "Test Connection" succeeds
   - ✅ Auto-enrichment button enabled
   - ✅ Queries execute successfully

4. **Single Enzyme Query**
   - Query EC 1.1.1.1 (Alcohol dehydrogenase)
   - Filter by Homo sapiens
   - Retrieve Km, kcat, citations
   - Verify data format

5. **Full Pathway Enrichment**
   - Import KEGG MAPK pathway (18 transitions)
   - Run auto-enrichment
   - Verify 85% → 98% completion
   - Check report generation

6. **Error Handling**
   - Invalid credentials → Clear error message
   - Network timeout → Graceful fallback
   - No data found → Show alternative organisms
   - Rate limiting → Automatic retry with delay

7. **Caching**
   - First query → Calls BRENDA API
   - Second query (same enzyme) → Loads from cache
   - Verify cache expiration (24 hours)

---

## 10. Open Questions & Decisions

### Resolved ✅:
- ✅ **Authentication:** Email + SHA256 password required
- ✅ **API Access:** Free academic registration needed
- ✅ **Registration Time:** 1-2 business days for approval
- ✅ **Code Organization:** `src/shypn/data/brenda/`, `doc/brenda/`
- ✅ **Architecture:** OOP with base + subclasses in separate files
- ✅ **UI Integration:** New BRENDA tab in Pathway panel

### Pending ⏳:
- ⏳ **Cache Duration:** How long to cache BRENDA results? (Suggested: 24 hours)
- ⏳ **Rate Limiting:** What's acceptable query rate? (Conservative: 1 query/second)
- ⏳ **Organism Fallback:** If no Homo sapiens data, which organism to suggest? (Mus musculus? Rattus norvegicus?)
- ⏳ **Error Recovery:** Retry strategy for failed queries? (3 retries with exponential backoff?)
- ⏳ **Testing Credentials:** Should we have test BRENDA account for CI/CD? (Probably not - mock instead)

---

## 11. Next Steps

### Immediate (Today):
1. ✅ Save this session documentation
2. ⏳ Wait for user's BRENDA credentials to activate (1-2 days)
3. ⏳ Create `doc/brenda/` directory structure
4. ⏳ Move BRENDA documentation files

### Short Term (This Week):
1. Implement UserProfile class with BRENDA fields
2. Implement CredentialsManager with encryption
3. Create User Profile dialog (Edit → Preferences)
4. Add "Test Connection" functionality

### Medium Term (Next 2 Weeks):
1. Implement BRENDA SOAP client (Zeep)
2. Implement base connector and BRENDA connector
3. Test single enzyme queries
4. Implement local caching

### Long Term (Next 4 Weeks):
1. Implement auto-enrichment engine
2. Implement gap analyzer
3. Create enrichment wizard UI
4. Full pipeline integration testing
5. User documentation and tutorials

---

## 12. References

### BRENDA Resources:
- Website: https://www.brenda-enzymes.org/
- Registration: https://www.brenda-enzymes.org/register.php
- SOAP API: https://www.brenda-enzymes.org/soap.php
- SPARQL Endpoint: https://sparql.dsmz.de/brenda (NEW - Sept 2025)
- License: CC BY 4.0 (https://www.brenda-enzymes.org/license.php)

### Python Libraries:
- **Zeep:** SOAP client for Python 3
  - Docs: https://docs.python-zeep.org/
  - Install: `pip install zeep`
- **Keyring:** Secure credential storage
  - Docs: https://keyring.readthedocs.io/
  - Install: `pip install keyring`

### Related Documentation:
- `doc/brenda/BRENDA_DATA_REFERENCE.md` - Comprehensive data catalog
- `doc/brenda/AUTO_ENRICHMENT_PIPELINE.md` - Pipeline architecture
- `doc/reporting/MASTER_PLAN.md` - Overall reporting system plan
- `doc/reporting/HEADER_BRANDING_SPEC.md` - Report header design

---

## 13. Session Participants

**User:** Simao (simao-eugenio)
- Role: Project lead, domain expert
- Decisions: Architecture organization, implementation priorities
- Status: Awaiting BRENDA credential activation

**AI Assistant:** GitHub Copilot
- Role: Architecture design, documentation, code generation
- Tasks: API research, pipeline design, documentation creation

---

**Session End:** October 24, 2025  
**Next Session:** After BRENDA credentials activation or continued panel architecture work
