# PLOS Computational Biology Submission Guidelines

**Retrieved: January 18, 2026**

## Key Finding: PLOS Guidelines ARE Generic Across All PLOS Journals

The formatting, structure, and LaTeX template are **shared across ALL PLOS journals** (PLOS ONE, PLOS Computational Biology, PLOS Medicine, etc.). This means:
- ✅ Same LaTeX template works for BOTH manuscripts
- ✅ Foundation manuscript can be reformatted once
- ✅ Drug discovery manuscript uses identical format
- ✅ No need to learn multiple journal systems

---

## LaTeX Template

**Official Template**: https://journals.plos.org/ploscompbiol/s/file?id=b7a0/Author_Template%20(2).zip

**Key Features**:
- Single unified template for ALL PLOS journals
- Includes BibTeX style sheet (Vancouver reference format)
- Compatible with Overleaf
- Document class: `plos2015.cls` (generic PLOS class)

**Submission Format**:
- **Initial submission**: Single PDF (text + figure legends + tables + references)
- **Figures**: Separate files, NOT in PDF
- **Accepted manuscripts**: Upload .tex source files (combine multiple .tex into single file)
- **LaTeX support**: latex@plos.org

**Important**: Do NOT track changes in .tex file. Use `latexdiff` for tracking during review.

---

## Manuscript Structure

### Required Sections (in order):

1. **Title Page**
   - Full title (≤200 characters, sentence case)
   - Short title (≤70 characters)
   - Authors + affiliations
   - Corresponding author email(s)
   - ORCID required for corresponding author

2. **Abstract** (≤300 words)
   - Conceptually divided: Background, Methods/Findings, Conclusions
   - **NO section headings** in abstract text
   - No citations, avoid abbreviations
   - Single paragraph format

3. **Author Summary** (150-200 words) ⭐ **UNIQUE TO PLOS**
   - Non-technical summary for general audience
   - First-person voice
   - Follows abstract immediately
   - Accessible to scientists and non-scientists

4. **Introduction**
   - Brief literature review
   - Broader context for non-experts
   - Mention controversies/disagreements
   - Conclude with study aim + achievement

5. **Results**
   - Past tense
   - Subdivisions with concise subheadings OK
   - No specific word limit
   - Peripheral details → Supporting Information

6. **Discussion**
   - Major conclusions + speculation
   - Significance to field
   - Future research directions
   - Concise and tightly argued
   - **Can combine Results+Discussion**

7. **Materials and Methods** (or Models)
   - Can be placed: before Results, before Discussion, or after Discussion
   - Enough detail to reproduce
   - Ethics statement if human/animal research
   - protocols.io encouraged (DOI-assigned protocols)

8. **Acknowledgments**
   - Contributors not meeting authorship criteria
   - **NO funding sources** (separate disclosure)
   - **NO editors/reviewers** mentioned

9. **References**
   - Vancouver style (numbered citation-sequence)
   - First 6 authors, et al.
   - Square brackets in text: [19]
   - DOIs required where available
   - Journal abbreviations from NCBI databases
   - BibTeX style file provided in template

10. **Supporting Information Captions**
    - List at end of manuscript
    - File number + name required
    - One-line title strongly recommended

---

## Style and Format

| Element | Requirement |
|---------|------------|
| **Length** | **NO LIMIT** (word count, figures, SI files) |
| **Font** | Any standard font (except "Symbol") |
| **Spacing** | Double-spaced |
| **Layout** | Single column (NOT multiple columns) |
| **Page/Line numbers** | Include both; continuous line numbers |
| **Headings** | Limit to 3 levels; clearly indicated |
| **Tables** | Insert after first citation paragraph |
| **Footnotes** | **NOT PERMITTED** (move to text or references) |
| **Abbreviations** | Define at first use; minimize usage |
| **Equations** | Use MathType or Equation Editor for full equations |
| | Insert single symbols as Unicode text |

---

## Data and Code Availability (CRITICAL)

### Data Policy:
- **All data** underlying findings must be **fully available without restriction**
- Large datasets → public repository (see recommended list)
- Small datasets → Supporting Information files
- Formats: Spreadsheets or flat files (NOT PDFs for tabular data)
- "Data not shown" **NOT ACCEPTED**

### Code Policy (Mandatory for PLOS Computational Biology):
- **All author-generated code** must be **publicly available**
- Repository with DOI (Zenodo, GitHub, CodeOcean, Software Heritage)
- Clear license (Open Source Definition compliant)
- Documentation included
- Version specified

### Data Availability Statement:
- Separate section in submission
- List repositories + DOIs/accession numbers
- Example: "All data and code available at GitHub [URL]. Archived on Zenodo DOI: 10.5281/zenodo.XXXXXX"

---

## Figures and Tables

### Figures:
- Submit separately (NOT in manuscript PDF initially)
- Cite in ascending numeric order
- Caption format: "Fig 1. Title. Legend."
- Caption placed in manuscript text after first citation
- Label matches filename (Fig 1 → Fig1.tif)

### Tables:
- Insert directly in manuscript after first citation
- Label (Table 1) + title above table
- Legends/footnotes below table
- Cite in ascending numeric order

---

## Supporting Information

- Any file type, <20 MB per file
- Naming: S1 Appendix, S2 Table, S3 Fig, etc.
- Published exactly as provided (no copyediting)
- Captions listed at end of manuscript
- Recommended citation in text (not required)

---

## Additional Required Information

### Financial Disclosure Statement:
- Grant numbers, author initials, funder URLs
- Funders' role in study design/analysis/publication
- If unfunded: "The author(s) received no specific funding for this work."

### Competing Interests:
- Declare financial/personal/professional conflicts
- Available to reviewers, stated in published article

### Author Contributions:
- CRediT taxonomy (Conceptualization, Data curation, Writing, etc.)
- Minimum one contribution per author
- All authors notified at submission by email

### Cover Letter:
- Why suitable for PLOS Computational Biology?
- How will it inspire field and drive research forward?
- May recommend Academic Editor (not binding)

---

## Section Selection (Choose One)

For **drug discovery SHYPN manuscript**:
- **Systems Biology** (best fit)
  - "Integrative modeling and analysis of complex biological systems"
  - "Novel multimodal methods"
  - "Systems pharmacology"

For **foundation SHYPN theoretical manuscript**:
- **Systems Biology** or **Cell Biology & Physiology**
  - "Modeling and analysis integrating across scales"
  - "Molecular regulation of cellular behavior"

---

## Advantages vs JMedChem

| Feature | PLOS Computational Biology | JMedChem |
|---------|---------------------------|----------|
| **Format** | Simpler (plos2015.cls) | Complex (achemso.cls) |
| **TOC Graphic** | NOT required | REQUIRED (3.25"×1.75") |
| **Page 2** | No blank page issue | Blank placeholder page |
| **Abstract** | 300 words | 150-200 words |
| **Length** | No limit | Shorter preferred |
| **Structure** | Flexible (Methods movable) | Rigid section order |
| **Audience** | Computational + biology | Medicinal chemistry |
| **Impact Factor** | 4.3 | 7.3 |
| **APC** | ~$2,500 | ~$2,000 |
| **Review time** | 4-6 weeks | 6-8 weeks |
| **Open access** | Yes (mandatory) | Optional |
| **Author Summary** | Required (150-200 words) | Not required |

---

## Template Download Commands

```bash
# Download PLOS LaTeX template
cd /home/simao/projetos/shypn/workspace/projects/My_Project/drug_discovery/manuscript
wget https://journals.plos.org/ploscompbiol/s/file?id=b7a0/Author_Template%20(2).zip -O plos_template.zip
unzip plos_template.zip
```

Template contents:
- `plos2015.cls` - Document class
- `plos2015.bst` - BibTeX style (Vancouver)
- `plos_template.tex` - Example manuscript
- `plos_template.pdf` - Formatted example

---

## Conversion Strategy

### For Drug Discovery Manuscript:
1. Keep current content structure (already excellent narrative)
2. Replace `\documentclass{achemso}` with `\documentclass[10pt]{plos2015}`
3. Remove achemso-specific commands (\tocentry, \abbreviations)
4. Add **Author Summary** section (150-200 words, non-technical)
5. Expand abstract to 300 words (currently 194)
6. Keep all sections (Introduction, Theoretical Framework, Results, Discussion)
7. Add Data Availability Statement (Zenodo DOI for code/data)
8. Convert references to Vancouver numbered style (BibTeX handles this)

### For Foundation Manuscript:
1. Convert from current format to PLOS template
2. Same structure: Title → Abstract → Author Summary → Body → References
3. Emphasize theoretical innovation (SHYPN formalism)
4. Include mathematical derivations in main text or SI
5. Add code availability (GitHub + Zenodo for SHYPN implementation)

---

## Next Steps

1. **Download PLOS template** (wget command above)
2. **Create Author Summary** for drug discovery manuscript (150-200 words)
   - Explain to non-experts: Why macrocyclic peptides? Why ATP matters?
3. **Expand abstract** to 300 words (add more context on implications)
4. **Prepare Data Availability Statement**:
   - Zenodo: Cyclosporin validation data (CSV)
   - GitHub: SHYPN model code
   - GitHub: Validation analysis scripts
5. **Convert references** to Vancouver format (use plos2015.bst)
6. **Test compilation** with plos2015.cls
7. **Prepare figures** (separate PDF/TIFF files)
8. **Create Supporting Information**:
   - S1 Appendix: Complete SHYPN 13-tuple specification
   - S2 Table: Full parameter table with confidence intervals
   - S3 Fig: Residual analysis plots

---

## Contact

- LaTeX issues: latex@plos.org
- General submission: ploscompbiol@plos.org
- Data policy: data@plos.org

---

## Key Takeaway

✅ **PLOS template is UNIVERSAL** across all PLOS journals
✅ **Simpler than achemso** (no TOC graphic, flexible structure)
✅ **Better fit for computational work** (Systems Biology section)
✅ **Open access** = higher visibility and citations
✅ **Code + data mandatory** = aligns with reproducible science
✅ **Both manuscripts** can use identical format

**Recommendation**: Convert both manuscripts to PLOS format. Target PLOS Computational Biology for both (foundation and drug discovery) as companion papers in the same journal.
