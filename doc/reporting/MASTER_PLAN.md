# Scientific/Executive Reporting System - Master Plan

## Project Overview

**Date Started:** October 24, 2025  
**Status:** 🎯 PLANNING PHASE  
**Scope:** Comprehensive reporting, metadata management, external database integration, and document generation

---

## Vision Statement

Create a complete scientific reporting ecosystem within shypn that allows users to:
- Generate professional scientific and executive reports
- Manage model metadata and provenance
- Access external biological databases (BRENDA, etc.)
- Authenticate with external services
- Export reports to multiple formats (PDF, Excel, etc.)

---

## Architecture Components

### 1. Scientific/Executive Reporting System
**Purpose:** Generate comprehensive reports from Petri net models and simulation results

**Features:**
- Report templates (Scientific, Executive, Technical)
- Automatic data collection from simulations
- Visualization integration (plots, graphs, network diagrams)
- Statistical analysis summaries
- Model validation metrics

**User Stories:**
- "As a researcher, I want to generate a scientific report with methods, results, and figures"
- "As a manager, I want an executive summary with key findings and recommendations"
- "As a reviewer, I want a technical report with all model details and parameters"

---

### 2. Project Architecture Integration
**Purpose:** Connect reporting to existing project structure

**Integration Points:**
- Multi-canvas document system
- Dynamic Analyses Panel (existing)
- Simulation data collectors (existing)
- File operations panel
- Workspace settings

**Architecture Considerations:**
- Report generation tied to specific canvas/model
- Access to all simulation history
- Integration with existing UI panels
- Non-blocking background generation for large reports

---

### 3. Model Metadata Management
**Purpose:** Track comprehensive metadata for models and simulations

**Metadata Categories:**

**Model-Level Metadata:**
- Model name, version, creation date
- Author(s), institution, contact
- Description, purpose, assumptions
- Biological system modeled
- Key findings, validation status

**Simulation-Level Metadata:**
- Parameters used
- Timestamp, duration
- Initial conditions
- Results summary
- Validation metrics

**Provenance Tracking:**
- Import source (SBML, KEGG, manual)
- Original model ID (BioModels, KEGG pathway)
- Modification history
- Citations/references

**Storage:**
- Embedded in .shypn file format
- Separate metadata.json sidecar option
- Export to RDF/Ontology formats

---

### 4. External Database Integration
**Purpose:** Access biological data from external sources

**Databases to Integrate:**

**BRENDA (Priority 1):**
- Enzyme kinetic parameters (Km, Vmax, kcat)
- Organism-specific data
- Temperature/pH dependencies
- Literature references
- API: https://www.brenda-enzymes.org/

**BioModels (Already Partial):**
- Enhance existing SBML import
- Access model annotations
- Retrieve publications
- Download simulation results

**KEGG (Already Partial):**
- Enhance existing pathway import
- Compound structures
- Reaction stoichiometry
- Pathway maps

**UniProt (Future):**
- Protein information
- Gene names
- Functional annotations

**ChEBI (Future):**
- Chemical compound data
- Molecular structures
- Chemical ontology

**Architecture:**
```
External Database Layer
├── DatabaseConnector (base class)
│   ├── BrendaConnector
│   ├── BioModelsConnector (extend existing)
│   ├── KEGGConnector (extend existing)
│   ├── UniProtConnector
│   └── ChEBIConnector
├── CacheManager (local caching)
├── RateLimiter (API throttling)
└── AuthenticationManager (credentials)
```

---

### 5. User Credentials Management
**Purpose:** Secure storage and management of external service credentials

**Requirements:**
- Secure credential storage (encrypted)
- Per-service authentication
- OAuth support where available
- API key management
- User profile (name, email, institution)

**Services Requiring Auth:**
- BRENDA (API key required)
- BioModels (optional, for private models)
- KEGG (API key for higher rate limits)
- Future services (UniProt, etc.)

**Architecture:**
```
Credentials System
├── CredentialsManager
│   ├── encrypt_credentials()
│   ├── decrypt_credentials()
│   ├── store_credential()
│   └── retrieve_credential()
├── UserProfile
│   ├── name, email, institution
│   ├── orcid_id (optional)
│   └── preferences
└── ServiceAuthenticators
    ├── APIKeyAuth
    ├── OAuth2Auth
    └── BasicAuth
```

**Storage:**
- Platform-specific secure storage
  - Linux: Secret Service API / keyring
  - macOS: Keychain
  - Windows: Credential Manager
- Fallback: Encrypted file in user config dir
- Never store in plain text

---

### 6. Local Document Generation
**Purpose:** Export reports to professional document formats

**Supported Formats:**

**PDF (Priority 1):**
- Library: ReportLab or WeasyPrint
- Full scientific report with figures
- Executive summary format
- Technical specification format

**Excel/LibreOffice (Priority 2):**
- Library: openpyxl or XlsxWriter
- Tabular simulation results
- Multi-sheet workbooks
- Charts and graphs

**HTML (Priority 3):**
- Interactive reports
- Embedded plots (Plotly)
- Web-ready format

**LaTeX (Future):**
- Academic paper format
- Integration with bibliography
- High-quality typesetting

**Markdown (Future):**
- Plain text with formatting
- GitHub-compatible
- Easy version control

**Document Components:**
- Title page with metadata
- Table of contents
- Executive summary
- Model description (diagram, equations)
- Methods section
- Results (tables, plots)
- Discussion/conclusions
- References/citations
- Appendices (parameters, raw data)

**Header/Branding System:**
> **📋 See:** `doc/reporting/HEADER_BRANDING_SPEC.md` for complete specification

**Key Components:**
- SHYpn logo placement (top-left, 60x60px)
- Institutional information (University, Department, Research Group, PI)
- Author information (Name, ORCID, Email)
- Provenance tracking (Software version, platform, timestamp)
- Citation block (Proper attribution format)
- License information (Software + Report licenses)

**Three Header Layouts:**
1. **Scientific Report** - Formal, comprehensive header with all details
2. **Executive Summary** - Compact header with essential info only
3. **Technical Report** - Detailed header with full provenance chain

**Data Sources for Header:**
- `UserProfile` - Name, email, ORCID, institution, department, lab, PI info
- `ModelMetadata` - Model name, version, authors, description, organism
- `SoftwareInfo` - Auto-generated version, platform, Python/GTK versions

**UI Components:**
- User Profile dialog (Edit → Preferences → User Profile)
- Model Metadata dialog (Report Panel → Edit Model Metadata)
- License selection (per-report or default in preferences)

**Implementation Note:** Header generation will be implemented as reusable components for PDF, Excel, and HTML formats. All reports will maintain consistent branding and provenance information to establish credibility and ensure reproducibility.

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal:** Basic infrastructure

- [ ] Create reporting module structure
- [ ] Design metadata schema
- [ ] Implement metadata storage in .shypn format
- [ ] Create user profile system
- [ ] Design credentials management architecture

**Deliverables:**
- `src/shypn/reporting/` module
- `src/shypn/metadata/` module
- `src/shypn/credentials/` module
- Metadata schema documentation
- Architecture diagrams

---

### Phase 2: Metadata & UI (Week 2-3)
**Goal:** User can manage metadata and configure profile

- [ ] Model metadata editor dialog
- [ ] Simulation metadata auto-capture
- [ ] **User profile settings dialog (name, email, ORCID, institution)**
- [ ] **User profile storage (encrypted credentials)**
- [ ] Metadata display in UI
- [ ] Save/load metadata with models
- [ ] **Header component system (reusable across formats)**

**Deliverables:**
- Metadata editor UI
- **User profile dialog with institutional info**
- **UserProfile class implementation**
- **Header generation utilities**
- Integration with existing file operations
- User documentation

**Related Documentation:**
- `doc/reporting/HEADER_BRANDING_SPEC.md` - Complete header design

---

### Phase 3: External Database - BRENDA (Week 3-4)
**Goal:** BRENDA integration working

- [ ] BRENDA API connector
- [ ] Credentials dialog for API key
- [ ] Parameter lookup dialog
- [ ] Cache management
- [ ] Rate limiting

**Deliverables:**
- BRENDA connector functional
- UI for parameter lookup
- Test suite for API calls
- Documentation

---

### Phase 4: Document Generation - PDF (Week 4-5)
**Goal:** Generate professional PDF reports with proper headers

- [ ] Report template system
- [ ] PDF generation engine (ReportLab/WeasyPrint)
- [ ] **Header generation system (logo, institution, author, provenance)**
- [ ] **Citation block formatting**
- [ ] **License information display**
- [ ] Plot/figure embedding
- [ ] Table generation from data
- [ ] Report preview dialog

**Deliverables:**
- PDF report generator
- 3 report templates (Scientific, Executive, Technical)
- **Professional headers with institutional branding**
- **Citation and license blocks**
- Report generation UI
- Example reports

**Related Documentation:**
- `doc/reporting/HEADER_BRANDING_SPEC.md` - Header implementation guide

---

### Phase 5: Excel Export (Week 5-6)
**Goal:** Export to Excel format with headers

- [ ] Excel generation engine (openpyxl)
- [ ] **Excel header formatting (institutional info, metadata)**
- [ ] Simulation data to spreadsheet
- [ ] Chart generation in Excel
- [ ] Multi-sheet workbooks
- [ ] Format selection dialog

**Deliverables:**
- Excel export functionality
- **Professional Excel headers**
- Multiple export formats
- Chart integration
- Documentation

**Related Documentation:**
- `doc/reporting/HEADER_BRANDING_SPEC.md` - Excel header examples

---

### Phase 6: Enhancement & Integration (Week 6+)
**Goal:** Complete the ecosystem

- [ ] Enhance BioModels/KEGG connectors
- [ ] Add UniProt/ChEBI connectors
- [ ] HTML report generation
- [ ] Report comparison tools
- [ ] Batch report generation
- [ ] Report scheduling/automation

**Deliverables:**
- Complete external database integration
- Multiple export formats
- Automated reporting tools
- Comprehensive documentation

---

## Technical Architecture

### Module Structure
```
src/shypn/
├── reporting/
│   ├── __init__.py
│   ├── report_generator.py
│   ├── report_templates.py
│   ├── pdf_generator.py
│   ├── excel_generator.py
│   ├── html_generator.py
│   ├── header_generator.py        # NEW: Reusable header components
│   ├── citation_formatter.py      # NEW: Citation block formatting
│   └── report_ui.py
├── metadata/
│   ├── __init__.py
│   ├── model_metadata.py
│   ├── simulation_metadata.py
│   ├── provenance.py
│   ├── metadata_editor.py
│   └── metadata_storage.py
├── external_data/
│   ├── __init__.py
│   ├── database_connector.py (base)
│   ├── brenda_connector.py
│   ├── biomodels_connector.py (enhance existing)
│   ├── kegg_connector.py (enhance existing)
│   ├── cache_manager.py
│   └── rate_limiter.py
├── credentials/
│   ├── __init__.py
│   ├── credentials_manager.py
│   ├── user_profile.py            # NEW: UserProfile class
│   ├── authenticators.py
│   └── secure_storage.py
└── ui/
    ├── reporting_panel.py
    ├── metadata_dialog.py
    ├── credentials_dialog.py
    ├── user_profile_dialog.py     # NEW: Edit → Preferences → User Profile
    └── database_query_dialog.py
```

### Data Flow
```
User Action
    ↓
UI Panel/Dialog
    ↓
Reporting System
    ↓
├─→ Metadata Manager → Model/Simulation Data
├─→ External Data → BRENDA/BioModels/etc.
├─→ Credentials → Authentication
└─→ Document Generator → PDF/Excel/HTML
    ↓
Output File
```

---

## Dependencies to Add

### Python Libraries
```python
# PDF Generation
reportlab>=4.0.0          # PDF creation
weasyprint>=60.0          # Alternative HTML-to-PDF

# Excel Generation
openpyxl>=3.1.0           # Excel read/write
xlsxwriter>=3.1.0         # Alternative Excel write

# External APIs
requests>=2.31.0          # HTTP (already in project)
requests-cache>=1.1.0     # API response caching

# Security
cryptography>=41.0.0      # Credential encryption
keyring>=24.0.0           # OS keyring access

# Data Processing
pandas>=2.1.0             # Data manipulation (if not already)
numpy>=1.24.0             # Numerical ops (already in project)

# Optional
markdown>=3.5.0           # Markdown generation
jinja2>=3.1.0             # Template engine
```

---

## UI Integration Points

### Main Menu Extensions
```
File
├── ...
├── Export Report...
│   ├── Scientific Report (PDF)
│   ├── Executive Summary (PDF)
│   ├── Technical Report (PDF)
│   ├── Simulation Data (Excel)
│   └── Interactive Report (HTML)
└── Model Properties...

Edit
└── Preferences...
    └── External Databases...
    └── User Profile...

Tools
├── ...
├── Query External Database...
│   ├── BRENDA - Enzyme Parameters
│   ├── BioModels - Model Repository
│   ├── KEGG - Pathway Data
│   └── UniProt - Protein Info
└── Batch Export Reports...

Help
└── External Database Help...
```

### New Panels
- **Report Generation Panel** (left dock, new tab)
- **Model Metadata Panel** (right dock, new tab)
- **External Database Query Panel** (dialog or dock)

---

## Security Considerations

### Credentials
- ✅ Encrypt at rest
- ✅ Never log credentials
- ✅ Use OS secure storage
- ✅ Optional: 2FA support
- ✅ Credential expiry handling

### External APIs
- ✅ Rate limiting
- ✅ Request caching
- ✅ Error handling
- ✅ Timeout handling
- ✅ SSL/TLS verification

### Data Privacy
- ✅ User consent for external queries
- ✅ Local data remains local
- ✅ Optional: Anonymize exports
- ✅ GDPR compliance considerations

---

## Testing Strategy

### Unit Tests
- Metadata serialization/deserialization
- Credential encryption/decryption
- Report template rendering
- PDF/Excel generation

### Integration Tests
- Full report generation pipeline
- External API mocking
- File format validation
- Cross-platform credential storage

### Manual Tests
- UI workflows
- Report quality review
- External database queries
- Multi-format export

---

## Documentation Plan

### User Documentation
- `doc/reporting/USER_GUIDE.md` - End-user guide
- `doc/reporting/REPORT_TEMPLATES.md` - Available templates
- **`doc/reporting/HEADER_BRANDING_SPEC.md` - Header design specification ✅**
- `doc/external_data/DATABASE_INTEGRATION.md` - How to use external databases
- `doc/external_data/BRENDA_GUIDE.md` - BRENDA-specific guide

### Developer Documentation
- `doc/reporting/ARCHITECTURE.md` - System architecture
- `doc/reporting/API_REFERENCE.md` - API documentation
- `doc/external_data/ADDING_DATABASES.md` - How to add new databases
- `doc/credentials/SECURITY.md` - Security implementation

### Quick References
- `doc/reporting/QUICK_START.md` - Get started in 5 minutes
- `doc/reporting/EXAMPLES.md` - Example reports
- `doc/external_data/API_KEYS.md` - How to get API keys

---

## Success Metrics

### Phase 1-2 (Foundation)
- [ ] Metadata can be attached to models
- [ ] User profile is saved and loaded
- [ ] Credentials are securely stored

### Phase 3-4 (Core Features)
- [ ] BRENDA queries return valid data
- [ ] PDF reports are generated successfully
- [ ] Reports contain all required sections

### Phase 5-6 (Complete)
- [ ] All planned databases integrated
- [ ] All planned formats supported
- [ ] Users can generate professional reports in < 1 minute
- [ ] 90%+ test coverage

---

## Risks & Mitigations

### Risk 1: External API Changes
**Mitigation:** Version API calls, implement fallbacks, cache responses

### Risk 2: Security Vulnerabilities
**Mitigation:** Use proven libraries (cryptography), code review, penetration testing

### Risk 3: Performance (Large Reports)
**Mitigation:** Background generation, progress indicators, pagination

### Risk 4: Format Compatibility
**Mitigation:** Test on multiple platforms, use standard libraries, provide multiple formats

### Risk 5: API Rate Limits
**Mitigation:** Aggressive caching, rate limiting, batch requests, user messaging

---

## Next Steps (Immediate)

1. **Review & Approval** - Get feedback on this plan
2. **Create Initial Structure** - Set up module directories
3. **Design Metadata Schema** - Define JSON/dict structure for metadata
4. **Prototype Metadata Editor** - Simple dialog to edit model metadata
5. **Research BRENDA API** - Study documentation, get test API key

---

## Questions to Answer

1. **Report Priority:** Which report type is most important? (Scientific, Executive, Technical)
2. **Database Priority:** Start with BRENDA or enhance BioModels/KEGG first?
3. **Format Priority:** PDF first, or Excel first?
4. **UI Design:** New panel vs. dialogs vs. menu items?
5. **Metadata Scope:** Minimal fields or comprehensive from start?
6. **Header/Branding:**
   - Which tagline? "Systems Biology Pathway Editor" vs. "Hybrid Petri Net Modeling Platform"
   - Logo design approach? (Designer, open-source icons, or custom)
   - Default license for reports? (CC-BY-4.0, CC-BY-SA-4.0, or other)
7. **User Profile:** Required fields vs. optional fields?

---

## Recent Updates

### October 24, 2025 - Header & Branding System
**Added comprehensive header/branding specification:**
- Professional report headers with logo, institution, author info
- Provenance tracking (software version, platform, timestamp)
- Citation blocks for proper attribution
- License information display
- Three header layouts (Scientific, Executive, Technical)
- UserProfile and ModelMetadata data sources
- Implementation examples for PDF and Excel

**New Components:**
- `UserProfile` class - Store user/institutional information
- `header_generator.py` - Reusable header components
- `citation_formatter.py` - Citation block formatting
- User Profile dialog - Edit → Preferences → User Profile

**Documentation:**
- Created `doc/reporting/HEADER_BRANDING_SPEC.md` (comprehensive spec)
- Updated MASTER_PLAN.md with header integration

**Rationale:** Professional headers establish credibility, ensure proper provenance, and make reports publication-ready. Essential for establishing SHYpn as a serious research tool.

---

**Status:** 📋 READY FOR REVIEW (Updated with Header/Branding)  
**Next Action:** Get user feedback on priorities and header design  
**Estimated Total Time:** 6-8 weeks for full implementation
