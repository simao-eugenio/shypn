# REPORT PANEL - MODELS CATEGORY SPECIFICATION

**Date**: November 2, 2025  
**Category**: MODELS  
**Purpose**: Comprehensive static summary of current model structure and metadata  
**Refresh Policy**: Manual (via 🔄 button) - Report is a resumé, not live data

---

## CATEGORY STRUCTURE

```
MODELS (Collapsible Category)
├── Model Overview (Frame, always visible)
│   ├── Model Name
│   ├── Project Name
│   ├── File Path
│   ├── Created Date
│   ├── Modified Date
│   └── Description
│
├── Petri Net Structure (Frame, always visible)
│   ├── Places Count
│   ├── Transitions Count
│   ├── Arcs Count
│   └── Model Type (Stochastic, Continuous, Timed, Bio-PN)
│
├── Import Provenance (Frame, conditional - only if imported)
│   ├── Source (KEGG, SBML, etc.)
│   ├── Source ID (e.g., hsa00010)
│   ├── Organism (e.g., Homo sapiens)
│   ├── Import Date
│   ├── Original File
│   ├── Imported Species Count
│   └── Imported Reactions Count
│
├── Species/Places List (Expander, collapsed by default)
│   └── Scrolled TextView with full list
│
└── Reactions/Transitions List (Expander, collapsed by default)
    └── Scrolled TextView with full list
```

---

## SECTION 1: MODEL OVERVIEW

**Purpose**: Identify the model and its file metadata  
**Display**: GTK Frame with Label (always visible)  
**Layout**: Vertical text lines, left-aligned, selectable

### Sub-sections:

#### 1.1 Model Name
- **Field**: `model.name` or "Untitled"
- **Format**: `Model Name: {name}`
- **Required**: Yes
- **Example**: `Model Name: Glycolysis Pathway`

#### 1.2 Project Name
- **Field**: `project.name`
- **Format**: `Project: {project_name}`
- **Required**: No (only if project exists)
- **Example**: `Project: Human Metabolism Study`

#### 1.3 File Path
- **Field**: `model.file_path` or `model_canvas.file_path`
- **Format**: `File: {absolute_path}`
- **Required**: No (only if saved)
- **Example**: `File: /home/user/projects/glycolysis.shypn`

#### 1.4 Created Date
- **Field**: `model.created_date`
- **Format**: `Created: YYYY-MM-DD HH:MM:SS`
- **Required**: No (only if metadata available)
- **Parse**: ISO 8601 format, display localized
- **Example**: `Created: 2025-11-01 14:23:15`

#### 1.5 Modified Date
- **Field**: `model.modified_date`
- **Format**: `Modified: YYYY-MM-DD HH:MM:SS`
- **Required**: No (only if metadata available)
- **Parse**: ISO 8601 format, display localized
- **Example**: `Modified: 2025-11-02 09:45:32`

#### 1.6 Description
- **Field**: `model.description`
- **Format**: `\nDescription: {description}`
- **Required**: No (only if exists)
- **Example**: 
  ```
  Description: Glycolysis pathway imported from KEGG.
  Contains 26 metabolites and 34 enzymatic reactions.
  ```

---

## SECTION 2: PETRI NET STRUCTURE

**Purpose**: Quantify model complexity and type  
**Display**: GTK Frame with Label (always visible)  
**Layout**: Vertical text lines, left-aligned, selectable

### Sub-sections:

#### 2.1 Places Count
- **Field**: `len(model.places)`
- **Format**: `Places: {count}`
- **Required**: Yes
- **Data Type**: Integer
- **Example**: `Places: 26`

#### 2.2 Transitions Count
- **Field**: `len(model.transitions)`
- **Format**: `Transitions: {count}`
- **Required**: Yes
- **Data Type**: Integer
- **Example**: `Transitions: 34`

#### 2.3 Arcs Count
- **Field**: `len(model.arcs)`
- **Format**: `Arcs: {count}`
- **Required**: Yes
- **Data Type**: Integer
- **Example**: `Arcs: 73`

#### 2.4 Model Type
- **Field**: Detected from transition types and arc types
- **Format**: `Type: {type1}, {type2}, ...`
- **Required**: No (only if types detected)
- **Detection Logic**:
  - **Stochastic**: Any transition with `transition_type='stochastic'`
  - **Continuous**: Any transition with `transition_type='continuous'`
  - **Timed**: Any transition with `transition_type='timed'`
  - **Bio-PN**: Any arc with `arc_type='test'` (test arcs)
- **Example**: `Type: Stochastic, Continuous, Bio-PN`

---

## SECTION 3: IMPORT PROVENANCE

**Purpose**: Track origin of imported models (KEGG, SBML, etc.)  
**Display**: GTK Frame with Label (conditional - hidden if no import data)  
**Layout**: Vertical text lines, left-aligned, selectable  
**Visibility**: Only shown if `PathwayDocument` linked to model

### Sub-sections:

#### 3.1 Source Type
- **Field**: `pathway_doc.source_type`
- **Format**: `Source: {SOURCE_TYPE}`
- **Required**: Yes (if provenance exists)
- **Values**: KEGG, SBML, BioPAX, CellML, etc.
- **Example**: `Source: KEGG`

#### 3.2 Source ID
- **Field**: `pathway_doc.source_id`
- **Format**: `Source ID: {id}`
- **Required**: No (only if available)
- **Example**: `Source ID: hsa00010`

#### 3.3 Organism
- **Field**: `pathway_doc.source_organism`
- **Format**: `Organism: {organism_name}`
- **Required**: No (only if available)
- **Example**: `Organism: Homo sapiens (human)`

#### 3.4 Import Date
- **Field**: `pathway_doc.imported_date`
- **Format**: `Imported: YYYY-MM-DD HH:MM:SS`
- **Required**: No (only if available)
- **Parse**: ISO 8601 format, display localized
- **Example**: `Imported: 2025-11-01 10:30:00`

#### 3.5 Original File
- **Field**: `pathway_doc.raw_file`
- **Format**: `Original File: {filename}`
- **Required**: No (only if available)
- **Example**: `Original File: hsa00010.xml`

#### 3.6 Imported Species Count
- **Field**: `pathway_doc.metadata['species_count']`
- **Format**: `Imported Species: {count}`
- **Required**: No (only if metadata exists)
- **Example**: `Imported Species: 28`
- **Note**: May differ from current count if user edited model

#### 3.7 Imported Reactions Count
- **Field**: `pathway_doc.metadata['reactions_count']`
- **Format**: `Imported Reactions: {count}`
- **Required**: No (only if metadata exists)
- **Example**: `Imported Reactions: 34`
- **Note**: May differ from current count if user edited model

---

## SECTION 4: SPECIES/PLACES LIST

**Purpose**: Detailed enumeration of all places with metadata  
**Display**: GTK Expander with ScrolledWindow + TextView (collapsed by default)  
**Layout**: Plain text, monospaced-friendly format  
**User Action**: Click "Show Species/Places List" to expand

### Header:
```
Total Species/Places: {count}

Format: [Internal ID] Label | Metadata
------------------------------------------------------------
```

### Item Format:
```
{index}. [{place.id}] {place.label} | {metadata_items}
```

### Metadata Items (if available):
- **KEGG ID**: `KEGG:{metadata['kegg_id']}` or `KEGG:{metadata['compound_id']}`
- **Chemical Formula**: `Formula:{metadata['formula']}`
- **Molecular Mass**: `Mass:{metadata['mass']}`
- **Type**: `Type:{metadata['type']}`

### Example:
```
Total Species/Places: 26

Format: [Internal ID] Label | Metadata
------------------------------------------------------------

1. [P45] C00033 | KEGG:cpd:C00033
2. [P88] C00103 | KEGG:cpd:C00103, Formula:C6H12O6
3. [P89] C00631 | KEGG:cpd:C00631, Mass:180.16
4. [P90] C00267 | KEGG:cpd:C00267, Formula:C3H4O3
```

### Data Source:
- **List**: `model.places` (List[Place])
- **Iteration**: `enumerate(model.places, 1)`
- **ID**: `place.id`
- **Label**: `place.label` or `place.id` or "Unnamed"
- **Metadata**: `place.metadata` (dict)

---

## SECTION 5: REACTIONS/TRANSITIONS LIST

**Purpose**: Detailed enumeration of all transitions with metadata  
**Display**: GTK Expander with ScrolledWindow + TextView (collapsed by default)  
**Layout**: Plain text, monospaced-friendly format  
**User Action**: Click "Show Reactions/Transitions List" to expand

### Header:
```
Total Reactions/Transitions: {count}

Format: [Internal ID] Label | Type | Metadata
------------------------------------------------------------
```

### Item Format:
```
{index}. [{transition.id}] {transition.label} | {transition_type} | {metadata_items}
```

### Metadata Items (if available):
- **KEGG Reaction**: `KEGG:{metadata['kegg_reaction_id']}` or `Reaction:{metadata['reaction_id']}`
- **EC Number**: `EC:{metadata['ec_number']}`
- **Kinetic Law**: `Kinetics:{metadata['kinetic_law']}`
- **Type**: `Type:{metadata['type']}`

### Example:
```
Total Reactions/Transitions: 34

Format: [Internal ID] Label | Type | Metadata
------------------------------------------------------------

1. [T1] R00710 | stochastic | KEGG:42, EC:2.7.1.1
2. [T2] R00711 | stochastic | KEGG:44, EC:5.3.1.9
3. [T9] R00200 | continuous | KEGG:57, Kinetics:mass_action
4. [T15] PFK | timed | Type:enzyme, EC:2.7.1.11
```

### Data Source:
- **List**: `model.transitions` (List[Transition])
- **Iteration**: `enumerate(model.transitions, 1)`
- **ID**: `transition.id`
- **Label**: `transition.label` or `transition.id` or "Unnamed"
- **Type**: `transition.transition_type` or "unknown"
- **Metadata**: `transition.metadata` (dict)

---

## EXPORT FORMAT

### Text Export:
```
================================================================================
MODELS CATEGORY - SCIENTIFIC REPORT
================================================================================

## Model Overview
--------------------------------------------------------------------------------
{overview_label.text}

## Petri Net Structure
--------------------------------------------------------------------------------
{structure_label.text}

## Import Provenance (if visible)
--------------------------------------------------------------------------------
{provenance_label.text}

## Species/Places List (if expanded)
--------------------------------------------------------------------------------
{species_buffer.text}

## Reactions/Transitions List (if expanded)
--------------------------------------------------------------------------------
{reactions_buffer.text}

================================================================================
```

### HTML Export (TODO):
- Structured HTML with CSS styling
- Collapsible sections
- Hyperlinks for KEGG/EC references

### PDF Export (TODO):
- Professional formatting
- Table of contents
- Page numbers and headers

---

## IMPLEMENTATION NOTES

### Data Structure:
- **Model**: `DocumentModel` with `places: List[Place]`, `transitions: List[Transition]`, `arcs: List[Arc]`
- **Places/Transitions**: Direct list iteration (not dict)
- **Metadata**: Dictionary on each element

### Refresh Policy:
- **Manual refresh only** (🔄 button in panel header)
- No auto-refresh on `set_project()` or `set_model_canvas()`
- Philosophy: Report is a **static resumé/snapshot**, not live monitoring

### UI Components:
- **CategoryFrame**: Collapsible header with title "MODELS"
- **GTK Frames**: For overview, structure, provenance sections
- **GTK Expanders**: For species/reactions lists
- **GTK Labels**: Selectable, left-aligned, line-wrapped
- **GTK TextViews**: Monospaced, read-only, scrollable

### Error Handling:
- Graceful fallback for missing attributes (`hasattr()` checks)
- "No model loaded" / "No data" placeholders
- Hidden provenance section if no import data
- "Untitled" / "Unnamed" / "unknown" defaults

---

## FUTURE ENHANCEMENTS

1. **Interactive Links**: Click KEGG IDs to open KEGG website
2. **Filtering**: Search/filter species and reactions lists
3. **Sorting**: Sort by ID, name, type, metadata
4. **Statistics**: Min/max/avg token counts, degree distribution
5. **Comparison**: Compare before/after model edits
6. **Charts**: Visual summary (bar charts of types, distribution plots)
7. **Diff View**: Show what changed since last refresh

---

## TESTING

Test file: `test_report_models_investigation.py`

Verified with KEGG pathway hsa00010 (Glycolysis):
- ✅ 26 places with KEGG metadata
- ✅ 34 transitions with types and metadata
- ✅ Model type detection (Stochastic, Continuous)
- ✅ Export to text
- ✅ All sections populate correctly
