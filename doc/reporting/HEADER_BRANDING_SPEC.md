# Report Header & Branding - Design Specification

## Purpose

Create a professional, informative header for all generated reports that:
- Establishes **credibility** and **provenance**
- Provides **proper attribution**
- Ensures **reliable source** identification
- Maintains **consistent branding**

---

## Header Components

### 1. Visual Identity

#### SHYpn Logo
- **Position:** Top-left corner
- **Size:** 60x60 pixels (or proportional)
- **Format:** SVG preferred (scalable), PNG fallback
- **File:** `ui/icons/shypn_logo.svg` or `ui/icons/shypn_logo.png`

**Logo Design Considerations:**
- Should represent: Systems Biology + Petri Nets
- Colors: Professional academic palette
- Must work in: Color, grayscale, black & white

#### Tagline/Description (ADOPTED)
```
SHYpn - Systems Biology Pathway Modeling Platform
Hybrid Petri Net Platform for Biological Pathway and Regulatory Network
Modeling, Simulation, and Analysis
```

**Rationale:**
- ✅ Systems Biology comes first (primary discipline)
- ✅ Pathway prominent (central object of study)
- ✅ "Modeling" emphasizes core capability (not just analysis)
- ✅ Platform not just editor (comprehensive ecosystem)
- ✅ Complete scope: Modeling + Simulation + Analysis
- ✅ Regulatory Networks included (future extensibility)
- ✅ Technical foundation clear (Hybrid Petri Nets)

**Alternative shorter version (for compact headers):**
```
SHYpn - Systems Biology Pathway Modeling Platform
Hybrid Petri Net Modeling and Simulation
```

---

### 2. Institutional Information

#### Primary Institution
```
Institution: [User's Institution/University]
Department: [Department/Faculty]
Research Group: [Lab/Group Name]
```

**Source:** User Profile (configured in Preferences)

#### Contact Information
```
Principal Investigator: [Prof. Name]
Contact: [email@institution.edu]
Website: [https://lab.institution.edu]
```

---

### 3. Document Metadata

#### Report Information
```
Report Type: Scientific Report / Executive Summary / Technical Report
Model Name: [Model filename or title]
Generated: October 24, 2025 14:30:00 UTC
Version: 1.0
```

#### Author Information
```
Prepared by: [User Name]
ORCID: [0000-0000-0000-0000] (optional)
Email: [user@institution.edu]
```

---

### 4. Provenance & Licensing

#### Software Information
```
Generated with: SHYpn v1.0.0
Platform: Linux/Windows/macOS
Python: 3.11.x
```

#### Citation
```
If you use this report, please cite:
[Author et al. (Year). SHYpn: Systems Biology Pathway Editor.
Journal/Conference. DOI: xx.xxxx/xxxxx]
```

#### License
```
Software License: MIT / GPL-3.0 / BSD (as applicable)
Report License: CC-BY-4.0 / CC-BY-SA-4.0 (user configurable)
```

---

## Header Layouts

### Layout A: Scientific Report (Formal)

```
┌────────────────────────────────────────────────────────────┐
│  [LOGO]     SHYpn - Systems Biology Pathway Modeling      │
│             Platform                                       │
│             Hybrid Petri Net Platform for Biological       │
│             Pathway and Regulatory Network Modeling        │
├────────────────────────────────────────────────────────────┤
│  Institution:  University of Example                       │
│  Department:   Computational Biology                       │
│  Lab:          Systems Biology Research Group              │
│  PI:           Prof. Jane Doe (jane.doe@example.edu)       │
├────────────────────────────────────────────────────────────┤
│  SCIENTIFIC REPORT                                         │
│                                                            │
│  Model: MAPK Signaling Pathway                            │
│  Author: John Smith (ORCID: 0000-0001-2345-6789)          │
│  Date: October 24, 2025                                   │
│  Version: 1.0                                              │
├────────────────────────────────────────────────────────────┤
│  Generated with SHYpn v1.0.0                               │
│  Citation: [Full citation here]                            │
│  License: CC-BY-4.0                                        │
└────────────────────────────────────────────────────────────┘
```

---

### Layout B: Executive Summary (Compact)

```
┌─────────────────────────────────────────────┐
│  [LOGO]  SHYpn - Systems Biology Pathway   │
│          Modeling Platform                  │
│          University of Example              │
├─────────────────────────────────────────────┤
│  EXECUTIVE SUMMARY: MAPK Signaling Analysis│
│  Prepared by: J. Smith | Oct 24, 2025      │
└─────────────────────────────────────────────┘
```

---

### Layout C: Technical Report (Detailed)

```
┌────────────────────────────────────────────────────────────┐
│  ┌──────┐                                                  │
│  │LOGO  │  SHYpn v1.0.0                                    │
│  │      │  Systems Biology Pathway Modeling Platform      │
│  └──────┘  Hybrid Petri Net Platform for Biological       │
│            Pathway and Regulatory Network Modeling         │
│                                                            │
│  TECHNICAL REPORT                                          │
│  ════════════════                                          │
│                                                            │
│  Institution Information                                   │
│  ───────────────────────                                   │
│  University of Example                                     │
│  Department of Computational Biology                       │
│  Systems Biology Research Group                            │
│  Principal Investigator: Prof. Jane Doe                    │
│  Contact: jane.doe@example.edu                             │
│  Website: https://sysbio.example.edu                       │
│                                                            │
│  Document Information                                      │
│  ────────────────────                                      │
│  Model: MAPK Signaling Pathway (mapk_model.shypn)         │
│  Author: John Smith (john.smith@example.edu)               │
│  ORCID: 0000-0001-2345-6789                                │
│  Generated: October 24, 2025 14:30:00 UTC                 │
│  Report Version: 1.0                                       │
│  Model Version: 2.3                                        │
│                                                            │
│  Provenance & Citation                                     │
│  ─────────────────────                                     │
│  Generated with SHYpn v1.0.0 on Linux                      │
│  Python 3.11.5 | GTK 3.24.38                               │
│                                                            │
│  Please cite:                                              │
│  Doe, J., Smith, J., et al. (2025). SHYpn: A Systems      │
│  Biology Pathway Modeling Platform for Hybrid Petri Net   │
│  Modeling. Bioinformatics, 41(10), 1234-1245.             │
│  DOI: 10.1093/bioinformatics/btXXXXXX                     │
│                                                            │
│  License: Software (MIT) | Report (CC-BY-4.0)             │
└────────────────────────────────────────────────────────────┘
```

---

## Data Sources

### User Profile (Preferences → User Profile)

```python
class UserProfile:
    """Store user and institutional information."""
    
    def __init__(self):
        # Personal Information
        self.name = ""                    # Full name
        self.email = ""                   # Contact email
        self.orcid = ""                   # ORCID ID (optional)
        
        # Institutional Information
        self.institution = ""             # University/Company name
        self.department = ""              # Department/Faculty
        self.research_group = ""          # Lab/Group name
        self.pi_name = ""                 # Principal Investigator
        self.pi_email = ""                # PI contact
        self.lab_website = ""             # Lab URL
        
        # Preferences
        self.default_license = "CC-BY-4.0"
        self.include_orcid = True
        self.include_contact = True
```

**Storage:** `~/.config/shypn/user_profile.json` (encrypted sensitive data)

---

### Model Metadata

```python
class ModelMetadata:
    """Store model-specific information."""
    
    def __init__(self):
        # Model Identity
        self.model_name = ""              # Display name
        self.model_version = "1.0"        # Version number
        self.filename = ""                # .shypn filename
        
        # Authorship
        self.authors = []                 # List of authors
        self.creation_date = None         # datetime
        self.last_modified = None         # datetime
        
        # Description
        self.description = ""             # Brief description
        self.biological_system = ""       # e.g., "MAPK signaling"
        self.organism = ""                # e.g., "Homo sapiens"
        
        # Provenance
        self.import_source = ""           # "SBML", "KEGG", "Manual"
        self.original_id = ""             # BioModels ID, KEGG pathway ID
        self.references = []              # List of DOIs/PMIDs
        
        # Validation
        self.validation_status = ""       # "Validated", "In Progress", etc.
        self.validation_notes = ""
```

**Storage:** Embedded in `.shypn` file

---

### Software Information (Auto-generated)

```python
class SoftwareInfo:
    """Automatically collected system information."""
    
    @staticmethod
    def get_info():
        return {
            'shypn_version': get_shypn_version(),    # From __version__
            'python_version': sys.version,
            'gtk_version': f"{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}",
            'platform': platform.system(),
            'architecture': platform.machine(),
            'generated_timestamp': datetime.now(timezone.utc)
        }
```

---

## Header Generation Code

### PDF Header (ReportLab)

```python
def generate_pdf_header(canvas, doc, report_type, user_profile, model_metadata):
    """Generate PDF report header."""
    
    # Logo
    if os.path.exists(LOGO_PATH):
        canvas.drawImage(LOGO_PATH, 50, 750, width=60, height=60)
    
    # Title
    canvas.setFont('Helvetica-Bold', 16)
    canvas.drawString(120, 790, 'SHYpn - Systems Biology Pathway Modeling Platform')
    
    canvas.setFont('Helvetica', 10)
    canvas.drawString(120, 775, 'Hybrid Petri Net Platform for Biological Pathway')
    canvas.drawString(120, 763, 'and Regulatory Network Modeling, Simulation, and Analysis')
    
    # Institution
    canvas.line(50, 760, 550, 760)  # Separator line
    
    y = 745
    canvas.setFont('Helvetica', 9)
    if user_profile.institution:
        canvas.drawString(50, y, f"Institution: {user_profile.institution}")
        y -= 12
    if user_profile.department:
        canvas.drawString(50, y, f"Department: {user_profile.department}")
        y -= 12
    if user_profile.research_group:
        canvas.drawString(50, y, f"Lab: {user_profile.research_group}")
        y -= 12
    
    # Report type
    canvas.line(50, y-5, 550, y-5)
    y -= 20
    canvas.setFont('Helvetica-Bold', 14)
    canvas.drawString(50, y, report_type.upper())
    
    # Model info
    y -= 20
    canvas.setFont('Helvetica', 9)
    canvas.drawString(50, y, f"Model: {model_metadata.model_name}")
    y -= 12
    canvas.drawString(50, y, f"Author: {user_profile.name}")
    if user_profile.orcid and user_profile.include_orcid:
        canvas.drawString(200, y, f"(ORCID: {user_profile.orcid})")
    
    # Date
    y -= 12
    canvas.drawString(50, y, f"Date: {datetime.now().strftime('%B %d, %Y')}")
    
    return y  # Return Y position for content start
```

---

### Excel Header (openpyxl)

```python
def generate_excel_header(worksheet, user_profile, model_metadata):
    """Generate Excel header in first rows."""
    
    # Merge cells for title
    worksheet.merge_cells('A1:F1')
    title_cell = worksheet['A1']
    title_cell.value = 'SHYpn - Systems Biology Pathway Modeling Platform'
    title_cell.font = Font(size=16, bold=True)
    title_cell.alignment = Alignment(horizontal='center')
    
    # Subtitle
    worksheet.merge_cells('A2:F2')
    worksheet['A2'].value = 'Hybrid Petri Net Platform for Biological Pathway and Regulatory Network Modeling'
    worksheet['A2'].alignment = Alignment(horizontal='center')
    
    # Institution info
    row = 4
    if user_profile.institution:
        worksheet[f'A{row}'] = 'Institution:'
        worksheet[f'B{row}'] = user_profile.institution
        row += 1
    
    # Model info
    row += 1
    worksheet[f'A{row}'] = 'Model:'
    worksheet[f'B{row}'] = model_metadata.model_name
    worksheet[f'A{row}'].font = Font(bold=True)
    
    row += 1
    worksheet[f'A{row}'] = 'Generated:'
    worksheet[f'B{row}'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    return row + 2  # Return row number for data start
```

---

## UI Components

### User Profile Dialog

**Location:** Edit → Preferences → User Profile

```
┌─────────────────────────────────────────────┐
│  User Profile & Institutional Information   │
├─────────────────────────────────────────────┤
│  Personal Information                       │
│  ────────────────────                       │
│  Full Name:       [________________________]│
│  Email:           [________________________]│
│  ORCID iD:        [________________________]│
│                   Get ORCID: https://orcid.org
│                                             │
│  Institutional Information                  │
│  ─────────────────────────                  │
│  Institution:     [________________________]│
│  Department:      [________________________]│
│  Research Group:  [________________________]│
│                                             │
│  Lab/PI Information                         │
│  ──────────────────                         │
│  PI Name:         [________________________]│
│  PI Email:        [________________________]│
│  Lab Website:     [________________________]│
│                                             │
│  Report Preferences                         │
│  ──────────────────                         │
│  Default License: [CC-BY-4.0       ▼]       │
│  ☑ Include ORCID in reports                │
│  ☑ Include contact information             │
│  ☑ Include institutional affiliation       │
│                                             │
│         [Cancel]              [Save]        │
└─────────────────────────────────────────────┘
```

---

### Model Metadata Dialog

**Location:** Report Panel → Edit Model Metadata

```
┌─────────────────────────────────────────────┐
│  Model Metadata                             │
├─────────────────────────────────────────────┤
│  Basic Information                          │
│  ─────────────────                          │
│  Model Name:      [________________________]│
│  Version:         [1.0____]                 │
│  Description:                               │
│  ┌────────────────────────────────────────┐ │
│  │                                        │ │
│  │                                        │ │
│  └────────────────────────────────────────┘ │
│                                             │
│  Biological Context                         │
│  ──────────────────                         │
│  System:          [________________________]│
│                   (e.g., "MAPK Signaling")  │
│  Organism:        [________________________]│
│                   (e.g., "Homo sapiens")    │
│                                             │
│  Authors                                    │
│  ───────                                    │
│  [Author 1                               ] │
│  [Author 2                               ] │
│  [+ Add Author]                             │
│                                             │
│  Provenance                                 │
│  ──────────                                 │
│  Import Source:   [Manual       ▼]         │
│  Original ID:     [________________________]│
│                   (BioModels/KEGG ID)       │
│                                             │
│  References (DOI/PMID)                      │
│  ─────────────────────                      │
│  [10.1093/bioinformatics/...            ] │
│  [+ Add Reference]                          │
│                                             │
│         [Cancel]              [Save]        │
└─────────────────────────────────────────────┘
```

---

## Logo Design Suggestions

### Concept A: Petri Net + Biology
```
    ●───●           P = Place (biological component)
    │   │           T = Transition (reaction/process)
    ●─T─●           Focus on network structure
```

### Concept B: SHY Letters + Network
```
  S H Y
  ● ● ●
  │\│/│           Letters connected by network edges
  ●─●─●           Represents hybrid systems
```

### Concept C: Pathway Flow
```
  ━━━━━►          Arrow showing pathway flow
  │ SHY           Combined with software name
  ━━━━━►          Dual pathways (hybrid concept)
```

**Recommendation:** Hire a designer or use open-source biology/network icons

---

## Citation Format

### Recommended Citation Block

```
If you use SHYpn in your research, please cite:

[Authors]. (Year). SHYpn: A Systems Biology Pathway Modeling Platform
for Hybrid Petri Net Analysis and Simulation. 
[Journal/Conference], Volume(Issue), Pages. 
DOI: xx.xxxx/xxxxx

BibTeX:
@article{shypn2025,
  title={SHYpn: A Systems Biology Pathway Modeling Platform for 
         Hybrid Petri Net Analysis and Simulation},
  author={[Authors]},
  journal={[Journal]},
  year={2025},
  volume={XX},
  pages={XX--XX},
  doi={xx.xxxx/xxxxx}
}
```

---

## License Options

### Software License
- **MIT** - Most permissive
- **GPL-3.0** - Copyleft, derivatives must be open source
- **Apache-2.0** - Patent grant included

### Report Content License
- **CC-BY-4.0** - Attribution required
- **CC-BY-SA-4.0** - Attribution + Share-Alike
- **CC-BY-NC-4.0** - Non-commercial use only
- **All Rights Reserved** - Copyright retained

**User configurable in preferences**

---

## Implementation Checklist

### Phase 1: Infrastructure
- [ ] Create UserProfile class
- [ ] Create ModelMetadata class
- [ ] Create SoftwareInfo utility
- [ ] Add user profile dialog
- [ ] Add model metadata dialog
- [ ] Store profiles in config

### Phase 2: Header Generation
- [ ] PDF header template
- [ ] Excel header template
- [ ] HTML header template
- [ ] Logo integration
- [ ] Citation formatter

### Phase 3: Integration
- [ ] Add header to all report types
- [ ] Test with missing data (graceful fallback)
- [ ] Validate ORCID format
- [ ] Test on all platforms
- [ ] Update documentation

---

## Mockup: Complete Scientific Report Header

```pdf
╔═══════════════════════════════════════════════════════════════════╗
║  ┌────┐                                                           ║
║  │    │  SHYpn - Systems Biology Pathway Modeling Platform       ║
║  │LOGO│  Hybrid Petri Net Platform for Biological Pathway and    ║
║  │    │  Regulatory Network Modeling, Simulation, and Analysis   ║
║  └────┘                                                           ║
║  ─────────────────────────────────────────────────────────────── ║
║                                                                   ║
║  University of Example                                            ║
║  Department of Computational Biology and Bioinformatics           ║
║  Systems Biology Research Group                                   ║
║  Principal Investigator: Prof. Jane Doe (jane.doe@example.edu)   ║
║  Lab Website: https://sysbio.example.edu                          ║
║                                                                   ║
║  ─────────────────────────────────────────────────────────────── ║
║                                                                   ║
║                        SCIENTIFIC REPORT                          ║
║                                                                   ║
║               Analysis of MAPK Signaling Pathway                  ║
║                                                                   ║
║  ─────────────────────────────────────────────────────────────── ║
║                                                                   ║
║  Model Information                                                ║
║  ──────────────────                                               ║
║  Model Name:     MAPK Signaling Pathway                           ║
║  Model Version:  2.3                                              ║
║  File:           mapk_pathway_v2.3.shypn                          ║
║  Description:    Computational model of the MAPK cascade including║
║                  RAF, MEK, and ERK kinases with feedback loops    ║
║                                                                   ║
║  Author:         Dr. John Smith                                   ║
║  ORCID:          0000-0001-2345-6789                              ║
║  Email:          john.smith@example.edu                           ║
║                                                                   ║
║  Generated:      October 24, 2025 at 14:30:00 UTC                ║
║  Report Version: 1.0                                              ║
║                                                                   ║
║  ─────────────────────────────────────────────────────────────── ║
║                                                                   ║
║  Provenance & Citation                                            ║
║  ────────────────────────                                         ║
║  Generated with: SHYpn v1.0.0                                     ║
║  Platform:       Linux x86_64                                     ║
║  Python:         3.11.5                                           ║
║  GTK:            3.24.38                                          ║
║                                                                   ║
║  If you use this report in your research, please cite:            ║
║                                                                   ║
║    Doe, J., Smith, J., et al. (2025). SHYpn: A Systems Biology   ║
║    Pathway Modeling Platform for Hybrid Petri Net Analysis.      ║
║    Bioinformatics, 41(10), 1234-1245.                            ║
║    DOI: 10.1093/bioinformatics/btXXXXXX                           ║
║                                                                   ║
║  Software License: MIT License                                    ║
║  Report License:   Creative Commons Attribution 4.0 (CC-BY-4.0)  ║
║                                                                   ║
║  © 2025 Systems Biology Research Group, University of Example    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝

[Report content begins here...]
```

---

## Summary

### Key Design Principles

1. **Credibility** - Clear institutional affiliation and authorship
2. **Provenance** - Full software version and generation details
3. **Reproducibility** - Model version, parameters, timestamps
4. **Citation** - Easy to cite both software and report
5. **Licensing** - Clear terms for software and content reuse
6. **Professionalism** - Polished appearance suitable for publication

### Implementation Priority

1. **High Priority:**
   - User profile system
   - Model metadata
   - Basic header with name/institution/date

2. **Medium Priority:**
   - ORCID integration
   - Citation formatting
   - License selection

3. **Future Enhancements:**
   - Logo design
   - Template customization
   - Multi-author support
   - Institutional logo support

---

**Status:** 📋 Design Complete - Ready for Implementation  
**Next Step:** Create UserProfile and ModelMetadata classes
