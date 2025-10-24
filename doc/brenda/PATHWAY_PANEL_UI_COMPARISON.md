# Pathway Panel UI Comparison

## Before Normalization

### KEGG Tab (Old)
```
┌─────────────────────────────────┐
│ Pathway ID:  [hsa00010____]     │
│ Organism:    [Human Sapiens ▼]  │
│                                  │
│ ▼ Options                        │
│   ☑ Filter cofactors             │
│   ☑ Scale coordinates            │
│                                  │
│           [Fetch] [Import]       │
└─────────────────────────────────┘
```
**Issues:**
- Two-step workflow (Fetch, then Import)
- No option for local files
- Import button disabled until fetch completes

### SBML Tab (Old)
```
┌─────────────────────────────────┐
│ ● External  ○ Local              │
│                                  │
│ BioModels ID: [BIOMD000001____]  │
│ OR                               │
│ File: [______________] [Browse]  │
│                                  │
│ ▼ Options                        │
│   ☑ Layout strategy              │
│                                  │
│      [Fetch] [Parse and Load]    │
└─────────────────────────────────┘
```
**Issues:**
- Better than KEGG (has source selection)
- Still two buttons (Fetch + Parse)
- Inconsistent with KEGG workflow

### BRENDA Tab (Old)
```
┌─────────────────────────────────┐
│                                  │
│   BRENDA Data Enrichment         │
│                                  │
│   (Placeholder - Phase 4)        │
│                                  │
│                                  │
└─────────────────────────────────┘
```
**Issues:**
- Not implemented
- No UI structure

---

## After Normalization

### KEGG Tab (New) ✅
```
┌──────────────────────────────────────┐
│ Source:                              │
│   ● External (KEGG API)              │
│   ○ Local KGML File                  │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ EXTERNAL SOURCE VISIBLE        │   │
│ │                                │   │
│ │ Pathway ID:  [hsa00010____]    │   │
│ │ Organism:    [Human Sapiens ▼] │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ LOCAL SOURCE HIDDEN            │   │
│ │                                │   │
│ │ File: [________] [Browse...]   │   │
│ └────────────────────────────────┘   │
│                                      │
│ ▼ Options                            │
│   ☑ Filter cofactors                 │
│   ☑ Scale coordinates                │
│                                      │
│            [Import to Canvas]        │
└──────────────────────────────────────┘
```
**Improvements:**
- ✅ Clear source selection (External default)
- ✅ Single unified action button
- ✅ Local file option available
- ✅ Consistent with other tabs

### SBML Tab (New) ✅
```
┌──────────────────────────────────────┐
│ Source:                              │
│   ● External (BioModels)             │
│   ○ Local File                       │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ EXTERNAL SOURCE VISIBLE        │   │
│ │                                │   │
│ │ BioModels ID: [BIOMD000001___] │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ LOCAL SOURCE HIDDEN            │   │
│ │                                │   │
│ │ File: [________] [Browse...]   │   │
│ └────────────────────────────────┘   │
│                                      │
│ ▼ Options                            │
│   ☑ Layout strategy                  │
│   ☑ Node appearance                  │
│                                      │
│            [Import to Canvas]        │
└──────────────────────────────────────┘
```
**Improvements:**
- ✅ Standardized source selection labels
- ✅ Single unified action button
- ✅ Matches KEGG structure exactly
- ✅ Same button label

### BRENDA Tab (New) ✅
```
┌──────────────────────────────────────┐
│ Source:                              │
│   ● External (BRENDA API)            │
│   ○ Local File                       │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ EXTERNAL SOURCE VISIBLE        │   │
│ │                                │   │
│ │ ❌ Not configured [Configure…] │   │
│ │                                │   │
│ │ EC Number: [1.1.1.1________]   │   │
│ │ Organism:  [All organisms   ▼] │   │
│ │                                │   │
│ │ ⓘ Registration takes 1-2 days  │   │
│ └────────────────────────────────┘   │
│                                      │
│ ┌────────────────────────────────┐   │
│ │ LOCAL SOURCE HIDDEN            │   │
│ │                                │   │
│ │ File: [________] [Browse...]   │   │
│ │ Formats: CSV, JSON             │   │
│ └────────────────────────────────┘   │
│                                      │
│ ▼ Import Options                     │
│   ☑ Include Km values                │
│   ☑ Include kcat values              │
│   ☑ Include Ki values                │
│   ☑ Include literature citations     │
│   ☑ Update existing parameters       │
│                                      │
│            [Import to Canvas]        │
└──────────────────────────────────────┘
```
**Improvements:**
- ✅ Full implementation (no placeholder)
- ✅ Matches KEGG/SBML structure
- ✅ Credentials status indicator
- ✅ Same unified action button
- ✅ Options expander for data selection

---

## Pattern Template

**Universal Tab Structure:**
```
┌──────────────────────────────────────┐
│ 1. SOURCE SELECTION                  │
│    ● External (Accession ID)         │
│    ○ Local File                      │
├──────────────────────────────────────┤
│ 2a. EXTERNAL INPUT (visible=True)    │
│     [Accession ID entry]             │
│     [Additional parameters]          │
├──────────────────────────────────────┤
│ 2b. LOCAL INPUT (visible=False)      │
│     [File path entry] [Browse...]    │
├──────────────────────────────────────┤
│ 3. OPTIONS (Expander - optional)     │
│    ▼ Import Options                  │
│      [checkboxes, settings]          │
├──────────────────────────────────────┤
│ 4. PREVIEW/STATUS (optional)         │
│    [feedback, warnings]              │
├──────────────────────────────────────┤
│ 5. ACTION BUTTON                     │
│    [    Import to Canvas    ]        │
└──────────────────────────────────────┘
```

---

## User Workflow Comparison

### Before Normalization

**KEGG Import:**
1. Enter pathway ID
2. Select organism
3. Click "Fetch Pathway" (wait...)
4. Click "Import" (enabled after fetch)
5. Pathway appears on canvas

**SBML Import:**
1. Choose source (External/Local)
2. Enter BioModels ID OR select file
3. Click "Fetch from BioModels" OR click "Parse and Load"
4. SBML appears on canvas

**BRENDA Import:**
- Not available (placeholder)

**Problems:**
- ❌ Different workflow per tab
- ❌ Two-step vs one-step inconsistency
- ❌ Button labels vary
- ❌ User confusion: "Do I Fetch or Import first?"

### After Normalization

**ALL Tabs (KEGG, SBML, BRENDA):**
1. Choose source: ● External OR ○ Local
2. Enter accession ID OR browse for file
3. (Optional) Expand options, configure settings
4. Click "Import to Canvas"
5. Data appears on canvas

**Benefits:**
- ✅ Same workflow for all tabs
- ✅ Single clear action
- ✅ No confusion
- ✅ Consistent button labels
- ✅ User learns once, applies everywhere

---

## Visual Design Consistency

### Color Coding (Planned)

```
External Source Box:  [Light Blue Background]
Local Source Box:     [Light Gray Background]
Active Radio Button:  ● (Filled)
Inactive Radio:       ○ (Empty)
Action Button:        [Blue "suggested-action"]
```

### Typography

```
Section Headers:  **Bold** (Source, Options)
Input Labels:     **Bold** (Pathway ID, EC Number, etc.)
Help Text:        Dim/Gray (Registration info, format hints)
Status Text:      Colored (❌ Red, ⏳ Orange, ✅ Green)
```

### Spacing

```
Outer margin:     12px
Section spacing:  12px
Widget spacing:   6px
Button alignment: Right (halign=end)
```

---

## Interaction Flow

### Radio Button Toggle

```
User clicks "Local File" radio button
  ↓
Signal: radio_button.toggled
  ↓
Handler: on_radio_toggled()
  ↓
Hide External Box (visible=False)
Show Local Box (visible=True)
  ↓
UI updates smoothly
```

### Browse Button

```
User clicks "Browse..." button
  ↓
Signal: button.clicked
  ↓
Handler: on_browse_clicked()
  ↓
Open GtkFileChooserDialog
  ↓
User selects file
  ↓
Update file_entry widget with path
  ↓
Enable Import button
```

### Import Button

```
User clicks "Import to Canvas"
  ↓
Signal: button.clicked
  ↓
Handler: on_import_clicked()
  ↓
Check which source is active:
  If External:
    - Fetch data from API
    - Parse response
    - Convert to canvas format
    - Add to canvas
  If Local:
    - Read file from disk
    - Parse file
    - Convert to canvas format
    - Add to canvas
  ↓
Show success notification
  ↓
Clear/reset input fields (optional)
```

---

## Implementation Checklist

### Phase 1: UI Structure ✅
- [x] KEGG tab: Add radio buttons
- [x] KEGG tab: Create External/Local boxes
- [x] KEGG tab: Change to single Import button
- [x] SBML tab: Standardize button label
- [x] SBML tab: Verify source selection structure
- [x] BRENDA tab: Create full structure
- [x] BRENDA tab: Add credentials status
- [x] BRENDA tab: Add options expander
- [x] All tabs: Consistent widget IDs
- [x] XML validation (no errors)

### Phase 2: Signal Wiring ⏳
- [ ] KEGG: Wire radio button toggling
- [ ] KEGG: Wire Browse button
- [ ] KEGG: Wire Import button
- [ ] SBML: Wire radio button toggling
- [ ] SBML: Wire Browse button
- [ ] SBML: Wire Import button
- [ ] BRENDA: Wire radio button toggling
- [ ] BRENDA: Wire Configure button
- [ ] BRENDA: Wire Browse button
- [ ] BRENDA: Wire Import button

### Phase 3: Controller Integration ⏳
- [ ] Wire KEGGImportPanel to KEGG tab
- [ ] Wire SBMLImportPanel to SBML tab
- [ ] Create BRENDAConnector
- [ ] Wire BRENDAConnector to BRENDA tab
- [ ] Test External source workflows
- [ ] Test Local source workflows

### Phase 4: Polish ⏳
- [ ] Add loading indicators
- [ ] Add error handling
- [ ] Add success notifications
- [ ] Add preview areas
- [ ] Add tooltips
- [ ] User testing
- [ ] Bug fixes

---

## Testing Scenarios

### KEGG Tab
1. **External Source:**
   - Enter valid pathway ID → should fetch and import
   - Enter invalid ID → should show error
   - Select different organism → should update results

2. **Local Source:**
   - Browse and select .xml file → should import
   - Select invalid file → should show error
   - Cancel file selection → should not crash

### SBML Tab
1. **External Source:**
   - Enter valid BioModels ID → should fetch and import
   - Enter invalid ID → should show error
   - Network offline → should show error

2. **Local Source:**
   - Browse and select .sbml file → should import
   - Select invalid file → should show error
   - Select .xml file → should import

### BRENDA Tab
1. **External Source:**
   - No credentials → should show warning
   - Valid credentials → should query API
   - Invalid EC number → should show error
   - Filter by organism → should return filtered results

2. **Local Source:**
   - Browse and select CSV → should import
   - Browse and select JSON → should import
   - Invalid format → should show error

---

## User Documentation Template

### Quick Start Guide

**Importing Pathways (All Sources)**

1. **Open Pathway Panel** (View → Panels → Pathways)

2. **Choose Your Tab:**
   - KEGG: For metabolic pathways
   - SBML: For BioModels
   - BRENDA: For enzyme data

3. **Select Source:**
   - ● External: Use accession ID (recommended)
   - ○ Local: Use file on your computer

4. **Enter Details:**
   - External: Type ID (e.g., hsa00010, BIOMD0000001, 1.1.1.1)
   - Local: Click "Browse..." to select file

5. **Import:**
   - Click "Import to Canvas"
   - Wait for processing
   - Pathway/data appears on canvas

**That's it!** Same workflow for all sources.

---

**Document Status:** ✅ Complete  
**Last Updated:** 2025-01-XX  
**Related Docs:** PATHWAY_PANEL_NORMALIZATION.md
