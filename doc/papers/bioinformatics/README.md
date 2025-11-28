# Bioinformatics Paper Materials

**Location**: `doc/papers/bioinformatics/`  
**Target Journal**: Bioinformatics (Oxford University Press)  
**Page Limit**: 10 pages maximum (strictly enforced)

---

## Files in This Folder

### 1. `weak_independence_biopn_bioinformatics.tex`
**Current paper** (10 pages, single-column)
- Source LaTeX file
- **Status**: Needs refactoring to two-column format
- **Next**: Follow REFACTORING_PLAN_10PAGE.md

### 2. `weak_independence_biopn_bioinformatics.pdf`
**Compiled current paper** (10 pages)
- Single-column format
- Will be replaced after refactoring

### 3. `BIOINFORMATICS_REFACTORING_PLAN.md`
**Original refactoring plan** (16.5-page target)
- Created before 10-page constraint clarification
- **Status**: Reference only (superseded by 10-page plan)
- Contains detailed Lac Operon example specification (1.5 pages standalone)

### 4. `REFACTORING_PLAN_10PAGE.md` ✅
**Active refactoring plan** (10-page strict limit)
- **Target**: 10 pages two-column (Bioinformatics journal requirement)
- **Strategy**: Compact writing + integrate Lac Operon into Methods (not standalone)
- **Figures**: Reuse from SHYpn GUI and thesis (4 figures total)
- **Implementation**: 8 phases, 8.5 hours estimated
- **Page budget**:
  - Abstract: 0.25 pages
  - Introduction: 1.0 page
  - Background: 0.75 pages
  - Methods: 3.0 pages (includes integrated Lac Operon example)
  - Results: 2.5 pages
  - Discussion: 0.8 pages
  - Future Work: 0.5 pages (bullet points)
  - Conclusion: 0.2 pages
  - References: 1.0 page (35 citations)

---

## Key Changes from Original Plan

| Aspect | Original Plan (16.5p) | New Plan (10p) |
|--------|----------------------|----------------|
| Layout | Two-column | Two-column |
| Introduction | 2.5 pages | 1.0 page |
| Background | 2.0 pages | 0.75 pages |
| Methods | 3.0 pages | 3.0 pages (includes Lac Operon) |
| Lac Operon | 1.5 pages standalone | 0.6 pages integrated |
| Results | 3.0 pages | 2.5 pages |
| Future Work | 1.0 page (prose) | 0.5 pages (bullets) |
| References | 40+ citations | 35 citations |
| **Total** | **16.5 pages** | **10 pages** |

**Compression Strategy**:
- Integrate Lac Operon into Methods (not separate section)
- Compact tables (small fonts, tight spacing)
- Bullet points for future work (not paragraphs)
- Reduce references to essentials (35 vs 40+)

---

## Figure Strategy (All Reused)

### Figure 1: Glucose Homeostasis
- **Source**: Thesis Chapter 3, Figure 3.4 (page 47)
- **Action**: Export PNG from thesis PDF
- **Size**: 2-column width (180mm)

### Figure 2: Lac Operon Model
- **Source**: Generate from SHYpn GUI
- **Action**: Open `examples/03_lac_operon_regulation.py`, export PNG
- **Size**: 2-column width (180mm)

### Figure 3: Speedup Plot
- **Source**: Thesis Chapter 5, Figure 5.8 (page 103)
- **Action**: Export PNG from thesis PDF
- **Size**: Single column (85mm)

### Figure 4: Dependency Distribution
- **Source**: Thesis Chapter 5, Figure 5.6 (page 98)
- **Action**: Export PNG from thesis PDF
- **Size**: Single column (85mm)

**No LaTeX figure drawing needed** - all figures already exist in thesis or can be generated from SHYpn GUI.

---

## Implementation Checklist

- [ ] **Phase 1**: Convert to two-column layout (1h)
- [ ] **Phase 2**: Expand introduction (compact) (1.5h)
- [ ] **Phase 3**: Compress background (table format) (1h)
- [ ] **Phase 4**: Compress formalism (compact notation) (1.5h)
- [ ] **Phase 5**: Integrate Lac Operon into Methods (1h)
- [ ] **Phase 6**: Expand results (add tables/figures) (2h)
- [ ] **Phase 7**: Compress future work (bullets) (0.5h)
- [ ] **Phase 8**: Add references + final polish (0.5h)

**Total**: 8.5 hours

---

## Verification

After each phase:
```bash
cd doc/papers/bioinformatics
pdflatex weak_independence_biopn_bioinformatics.tex
pdfinfo weak_independence_biopn_bioinformatics.pdf | grep Pages
# Must show: Pages: 10 (or fewer)
```

**Critical**: Bioinformatics journal strictly enforces 10-page limit. Exceeding this will result in desk rejection.

---

## Next Steps

1. Start with **Phase 1** (layout conversion)
2. Compile and check page count
3. Proceed through phases iteratively
4. Extract figures from thesis and SHYpn
5. Final compilation and verification

**Note**: Both refactoring plans are preserved for reference, but **REFACTORING_PLAN_10PAGE.md** is the active working document.
