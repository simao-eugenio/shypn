# PLOS Conversion Status - Foundation Manuscript

**Date**: January 18, 2026  
**Priority**: Foundation manuscript → PLOS Computational Biology (before drug discovery)

---

## Files Created

✅ **PLOS_COMPBIOL_GUIDELINES.md** (11 KB)
- Complete submission guidelines
- Generic template for ALL PLOS journals
- LaTeX formatting requirements
- Data/code availability policies

✅ **main_plos.tex** (New file - 408 KB PDF, 21 pages)
- PLOS Computational Biology format
- Preserves original main.tex (two-column Bioinformatics format)
- Single-column, wide margins (PLOS style)
- All content sections included via `\input{}`

✅ **PLOS Template Files Downloaded**
- plos_latex_template.tex (reference template)
- plos2025.bst (BibTeX Vancouver style)
- plos_bibtex_sample.bib (citation examples)
- plos_latex_template.pdf (formatted example)

---

## Current Status

### ✅ Completed

1. **Document Structure** (PLOS-compliant):
   - Title (200 characters)
   - Author/affiliation placeholders
   - Abstract (300 words max, currently ~250 words ✅)
   - **Author Summary** (150-200 words, non-technical) ⭐ **NEW - REQUIRED**
   - Introduction → Background → Theory → Results → Discussion → Conclusion
   - Materials and Methods section
   - Acknowledgments placeholder
   - Supporting Information captions
   - **Data Availability Statement** (REQUIRED) ⭐ **NEW**

2. **LaTeX Setup**:
   - `\documentclass[10pt,letterpaper]{article}` (PLOS standard)
   - Geometry: top=0.85in, left=2.75in (wide margins for line numbers)
   - All required packages: amsmath, cite, hyperref, lineno, microtype
   - Additional packages: algorithm, booktabs, tikz (for Petri nets)
   - Theorem environments preserved

3. **Content Integration**:
   - All 9 section .tex files referenced via `\input{}`
   - References: `\bibliography{references}` + `\bibliographystyle{plos2025}`
   - Maintains original section organization

4. **Compilation**:
   - ✅ Successful: 21 pages, 408 KB PDF
   - No errors, clean compilation
   - Ready for content review

---

## Key PLOS Additions (vs Original)

### 1. Author Summary (UNIQUE TO PLOS)

Currently included 150-200 word non-technical summary:
- First-person voice ("We developed...")
- Explains ATP as metabolite vs. signal
- Highlights 65% weak independence, 2-4× speedup
- Mentions 7% accuracy on sporulation threshold
- Written for general audience (non-experts)

**Status**: ✅ Complete draft (needs author review)

### 2. Data Availability Statement (MANDATORY)

Complete statement included:
- GitHub repository: https://github.com/simao-eugenio/shypn
- Zenodo DOI: [to be assigned upon acceptance]
- BioModels accession numbers (100 systems in S2 Table)
- Case study references: Veening 2008, Huang 1996, Arkin 1998
- Benchmark data location: `benchmarks/` directory
- Statement: "No proprietary or restricted data were used"

**Status**: ✅ Complete (needs Zenodo DOI before submission)

### 3. Materials and Methods

New section added covering:
- Implementation (Python library description)
- Validation dataset (BioModels + 3 case studies)
- Performance benchmarking protocol
- Statistical analysis methods

**Status**: ✅ Complete draft (expand if needed)

### 4. Supporting Information Captions

Four SI items defined:
- **S1 Appendix**: Mathematical proofs (Theorems 1-3)
- **S2 Table**: Extended validation (100 BioModels systems)
- **S3 Fig**: Additional case studies (MAPK, lambda phage)
- **S1 Code**: SHYPN implementation (Zenodo archive)

**Status**: ✅ Captions complete (need to create actual SI files)

---

## Differences: Original vs PLOS

| Element | main.tex (Original) | main_plos.tex (PLOS) |
|---------|---------------------|----------------------|
| **Format** | Two-column (Bioinformatics) | Single-column (PLOS) |
| **Page count** | TBD (compact) | 21 pages (wide margins) |
| **Margins** | 2cm all sides | 0.85in top, 2.75in left |
| **Line numbers** | No | Yes (right margin) |
| **Author Summary** | No | Yes (150-200 words) ⭐ |
| **Data Availability** | No explicit section | Mandatory section ⭐ |
| **Methods** | Implicit | Explicit section |
| **SI Captions** | No | Required at end |
| **References** | natbib style | plos2025.bst (Vancouver) |
| **Abstract** | 250 words | 300 words max (expandable) |

---

## Next Steps (Priority Order)

### HIGH PRIORITY (Before Submission)

1. **Review Author Summary** 
   - Ensure accessible to non-experts
   - Verify 150-200 word limit
   - Confirm first-person voice appropriateness

2. **Expand Abstract to 300 words**
   - Currently ~250 words (good, but can add)
   - Consider adding: broader impact, comparison to alternatives
   - Maintain single paragraph format

3. **Add Author Information**
   - Replace `[Author Name]` placeholder
   - Add affiliations with proper numbering
   - Include ORCID iD (REQUIRED for corresponding author)
   - Add email address

4. **Create Zenodo Archive** ⭐ **CRITICAL**
   - Archive GitHub repo: https://github.com/simao-eugenio/shypn
   - Obtain DOI
   - Update Data Availability Statement with actual DOI
   - Include version tag matching manuscript

5. **Compile References with BibTeX**
   ```bash
   cd /home/simao/projetos/shypn/workspace/projects/My_Project/foundation/manuscript
   pdflatex main_plos.tex
   bibtex main_plos
   pdflatex main_plos.tex
   pdflatex main_plos.tex
   ```
   - Ensure references.bib compatible with plos2025.bst
   - Check Vancouver numbering [1], [2], etc.

### MEDIUM PRIORITY

6. **Expand Materials and Methods**
   - Add hardware specifications for benchmarks
   - Detail statistical methods (if needed)
   - Describe SBML conversion process

7. **Create Supporting Information Files**
   - **S1_Appendix.pdf**: Mathematical proofs
   - **S2_Table.xlsx**: 100 BioModels validation data
   - **S3_Fig.pdf**: Extended case study figures
   - Upload to submission system separately

8. **Prepare Figures** (6 main figures)
   - Extract from main.pdf or regenerate
   - Submit as separate files (NOT in manuscript PDF)
   - Format: TIFF or PDF, 300+ DPI
   - Captions already in text (after first citation)

9. **Write Cover Letter**
   - Why suitable for PLOS Computational Biology?
   - How will it inspire Systems Biology field?
   - Mention: first formal signal hierarchy theory, 100-model validation
   - Recommend Academic Editor (optional)

### LOW PRIORITY

10. **Optimize Section Balance**
    - Check Results section length
    - Consider moving detailed algorithms to SI
    - Ensure Discussion is concise and impactful

11. **Add Striking Image** (Optional)
    - Petri net diagram with signal flow arcs
    - Layer hierarchy visualization
    - 300-600 DPI, single panel
    - May be used for journal promotional materials

12. **Financial Disclosure**
    - Complete in submission system
    - Grant numbers, funder roles
    - If unfunded: "The author(s) received no specific funding for this work."

13. **Competing Interests**
    - Declare any conflicts
    - If none: "The authors have declared that no competing interests exist."

14. **Author Contributions** (CRediT taxonomy)
    - Conceptualization, Methodology, Software, Validation
    - Writing (original draft, review & editing)
    - All authors will receive email notification at submission

---

## Compilation Commands

### Standard Compilation:
```bash
cd /home/simao/projetos/shypn/workspace/projects/My_Project/foundation/manuscript
pdflatex main_plos.tex
```

### Full Compilation (with references):
```bash
pdflatex main_plos.tex
bibtex main_plos
pdflatex main_plos.tex
pdflatex main_plos.tex
```

### Quick Check (last 10 lines):
```bash
pdflatex -interaction=nonstopmode main_plos.tex 2>&1 | tail -10
```

---

## Section Recommendations (Target PLOS Computational Biology)

**Best Section**: **Systems Biology**
- "Integrative modeling and analysis of complex biological systems"
- "Novel multimodal methods applied to biological system data"
- "Network biology and modeling complex feedback and regulatory systems"

**Alternative**: **Cell Biology & Physiology**
- "Molecular regulation of cellular behavior"
- "Multi-system regulation"
- "Modeling across scales"

---

## Submission Checklist

### Required for Initial Submission:
- [ ] main_plos.pdf (compiled manuscript)
- [ ] Separate figure files (6 files: Fig1.tif through Fig6.tif)
- [ ] Cover letter
- [ ] Financial disclosure (in submission system)
- [ ] Author contributions (in submission system)
- [ ] Data availability statement (in manuscript ✅)
- [ ] ORCID iD for corresponding author

### Required if Accepted:
- [ ] main_plos.tex (LaTeX source - single file, combined)
- [ ] references.bib
- [ ] Supporting Information files (S1-S4)
- [ ] High-resolution figures
- [ ] Zenodo DOI for code archive

---

## Key Differences from Drug Discovery Manuscript

| Feature | Foundation (Theory) | Drug Discovery (Application) |
|---------|---------------------|------------------------------|
| **Focus** | Mathematical formalism | Validation + drug design |
| **Key Results** | Theorems, proofs, algorithms | 85% correlation, 28× N-Me |
| **Section** | Systems Biology | Systems Biology or Pharmacology |
| **Figures** | Petri net diagrams, algorithms | Validation plots, predictions |
| **SI** | Proofs, algorithms | Parameter tables, datasets |
| **Priority** | Submit FIRST | Submit SECOND (after foundation) |

---

## Contact for Questions

- LaTeX issues: latex@plos.org
- Submission: ploscompbiol@plos.org
- Data policy: data@plos.org

---

## Timeline Estimate

1. **Author review + revisions**: 1-2 days
2. **Zenodo archive creation**: 1 hour
3. **Figure preparation**: 1-2 days
4. **Supporting Information**: 2-3 days
5. **Cover letter**: 1 hour
6. **Submission**: 30 minutes

**Total**: ~1 week to submission-ready

---

## Status Summary

✅ **PLOS template integrated** (21 pages, compiles successfully)  
✅ **Author Summary written** (150-200 words, accessible)  
✅ **Data Availability Statement complete** (needs Zenodo DOI)  
✅ **Materials and Methods added**  
✅ **Supporting Information captions defined**  
⏳ **Author information** (placeholder - needs completion)  
⏳ **References** (need BibTeX compilation)  
⏳ **Figures** (need extraction/formatting)  
⏳ **Zenodo archive** (CRITICAL - needs DOI)  

**Next immediate action**: Review Author Summary and expand Abstract to 300 words, then create Zenodo archive for DOI.
