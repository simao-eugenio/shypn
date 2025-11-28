# Two-Version Thesis Strategy

## Overview

The thesis will be maintained in **two parallel versions**:

1. **International Version (English)** - ClassicThesis format (current main version)
2. **Portuguese Version (Brazilian Portuguese)** - ABNT format for UFSC submission

## Changes Reverted (November 27, 2025)

The ABNT modifications made to the main thesis have been **reverted** to restore the original ClassicThesis format:

### Files Restored to Original State:
- `doc/thesis/latex/thesis.tex` - Back to 11pt, twoside, roman page numbering
- `doc/thesis/latex/classicthesis-config.tex` - Back to bibtex8, numeric-comp bibliography style, no geometry package
- `doc/thesis/latex/FrontBackmatter/Titlepage.tex` - Back to simple English title page (no logo, no ABNT format)

### Files Kept (Useful for Both Versions):
- `doc/thesis/latex/Bibliography.bib` - **Kept with 41 new entries** added from References.txt (Petri nets, systems biology literature)
- `doc/thesis/latex/gfx/brasao_UFSC.pdf` - **Kept** - UFSC logo for future Portuguese version
- `doc/thesis/latex/gfx/brasao_UFSC.svg` - **Kept** - Original vector logo

### Current Status:
- **International version compiles successfully**: 243 pages, 991KB PDF
- **Bibliography has 51 entries** (10 original + 41 recently added)
- **All LaTeX structure intact** with ClassicThesis formatting

## Rationale: Why Two Versions?

### International Version (Current Main)
- **Purpose**: International academic dissemination, journal publications, conferences
- **Language**: English throughout
- **Format**: ClassicThesis (elegant, publication-ready)
- **Typography**: 11pt Palatino, twoside layout, Roman pre-textual numbering
- **Bibliography**: BibTeX8 with numeric-comp style (IEEE-like)
- **Margins**: Standard ClassicThesis (optimized for readability)
- **Target Audience**: International computer science and systems biology communities

### Portuguese Version (Future ABNT)
- **Purpose**: UFSC institutional repository, Brazilian academic compliance
- **Language**: Brazilian Portuguese (full translation required)
- **Format**: ABNT NBR 14724:2011 (mandatory for Brazilian theses)
- **Typography**: 12pt, oneside, Arabic numbering from Chapter 1
- **Bibliography**: Biblatex-ABNT with author-year style
- **Margins**: ABNT standard (3cm top/left, 2cm bottom/right)
- **Logo**: UFSC brasão on title page
- **Target Audience**: UFSC defense committee, Brazilian institutions

## Recommended Workflow

### Phase 1: Complete International Version First (Priority)
1. **Finalize English content** - All 15 chapters complete
2. **Add missing 27 bibliography entries** (see ABNT_CONVERSION_SUMMARY.md)
3. **Proofread and revise** - Focus on clarity, consistency
4. **Generate final PDF** - For defense and publication
5. **Defend thesis** - Use English version

### Phase 2: Create Portuguese Version After Defense
1. **Copy entire thesis directory** to `doc/thesis_pt/`
2. **Translate all chapters** to Brazilian Portuguese
3. **Apply ABNT formatting** (using documented changes from ABNT_CONVERSION_SUMMARY.md)
4. **Add UFSC logo and institutional pages** (Folha de Aprovação, Ficha Catalográfica)
5. **Submit to UFSC repository** - Portuguese version with ABNT compliance

### Why This Order?
- **English version is more complete** (243 pages, all chapters written)
- **Defense likely uses English version** (international standards)
- **Translation is time-consuming** (15 chapters × ~20 pages = 300 pages to translate)
- **ABNT compliance easier after content finalized** (structural changes without rewriting)

## File Organization Strategy

### Option A: Separate Directories (Recommended)
```
doc/
├── thesis/          # International (English, ClassicThesis)
│   └── latex/
│       ├── thesis.tex
│       ├── classicthesis-config.tex
│       ├── Chapters/
│       └── ...
└── thesis_pt/       # Portuguese (ABNT) - COPY AFTER DEFENSE
    └── latex/
        ├── thesis_pt.tex
        ├── abnt-config.tex
        ├── Capitulos/  # Translated chapters
        └── ...
```

**Advantages:**
- Clean separation, no risk of breaking English version
- Can have different chapter file names (chapter_01.tex vs capitulo_01.tex)
- Different preambles, packages, configurations
- Independent Git branches possible

**Disadvantages:**
- Code/content duplication
- Bibliography must be maintained in both places
- Figures/tables may need duplication if captions change

### Option B: Single Directory with Conditional Compilation
```latex
% thesis.tex
\newif\ifabnt
% \abnttrue  % Uncomment for Portuguese ABNT version

\ifabnt
  \input{config_abnt}
  \selectlanguage{brazilian}
\else
  \input{classicthesis-config}
  \selectlanguage{american}
\fi
```

**Advantages:**
- Single source of truth for content
- Shared bibliography, figures, tables
- Changes automatically propagate

**Disadvantages:**
- More complex LaTeX code (many \ifabnt conditionals)
- Risk of breaking one version while editing the other
- Translation requires in-line language switching (messy)

### **Recommendation: Option A (Separate Directories)**
For full translation, separate directories are cleaner and safer.

## ABNT Conversion Checklist (For Future Portuguese Version)

When ready to create Portuguese version, refer to `doc/thesis/ABNT_CONVERSION_SUMMARY.md` for detailed instructions. Quick summary:

### Required Changes:
1. **thesis.tex**:
   - `\documentclass[oneside,12pt,...]` (not twoside, 11pt)
   - `\pagenumbering{gobble}` for pre-textual
   - `\pagenumbering{arabic}` from Chapter 1

2. **classicthesis-config.tex**:
   - Add `\usepackage[a4paper,top=3cm,bottom=2cm,left=3cm,right=2cm]{geometry}`
   - Change biblatex: `backend=biber, style=abnt, language=brazilian`
   - Add `\usepackage{setspace} \onehalfspacing`
   - Add `\usepackage{indentfirst}`

3. **Titlepage.tex**:
   - Two-page format: (1) Capa, (2) Folha de Rosto
   - UFSC logo: `\includegraphics[width=3.5cm]{gfx/brasao_UFSC.pdf}`
   - Institutional text in Portuguese (UNIVERSIDADE FEDERAL DE SANTA CATARINA, etc.)
   - Natureza do trabalho: "Tese submetida ao Programa de..."

4. **Add missing files**:
   - `FrontBackmatter/Approval.tex` - Folha de Aprovação (after defense)
   - `FrontBackmatter/FichaCatalografica.tex` - Request from UFSC library

5. **Fix known issues** (from ABNT_CONVERSION_SUMMARY.md):
   - Replace `\ce{... -> \emptyset}` with `\ce{... -> []}` (27 instances)
   - Define colors: CTlink, CTtitle, CTurl, Black
   - Define theorem environments: theorem, definition, lemma

6. **Add 27 missing bibliography entries** (see ABNT_CONVERSION_SUMMARY.md Section 8)

### Compilation Sequence (Portuguese Version):
```bash
cd doc/thesis_pt/latex
pdflatex thesis_pt.tex
biber thesis_pt
pdflatex thesis_pt.tex
pdflatex thesis_pt.tex
```

## Timeline Recommendation

### Now → Defense (3-6 months):
- **Focus exclusively on English version**
- Finalize all 15 chapters
- Add missing bibliography entries
- Proofread, revise, polish
- Generate defense version PDF

### After Defense → Repository Submission (1-2 months):
- **Translate to Portuguese** (chapters, abstracts, captions)
- **Apply ABNT formatting** (using ABNT_CONVERSION_SUMMARY.md)
- **Add institutional pages** (approval sheet, cataloging card)
- **Submit to UFSC repository**

### Realistic Translation Effort:
- **243 pages × 5 hours/page = 1,215 hours** (if professional translation)
- **Estimated cost**: R$ 50-100 per page × 243 = R$ 12,150 - 24,300
- **Or**: DIY translation ~3 months part-time work
- **Recommendation**: Use professional translator for quality + speed

## Assets Available for Portuguese Version

From previous ABNT work, the following are ready to use:

### Logo Files:
- `doc/thesis/latex/gfx/brasao_UFSC.pdf` (103KB, vector)
- `doc/thesis/latex/gfx/brasao_UFSC.svg` (343KB, original)

### ABNT Documentation:
- `doc/thesis/ABNT_CONVERSION_SUMMARY.md` - Complete guide (78,500 characters)
  - Detailed structural changes
  - Known compilation issues + solutions
  - Missing bibliography entries list
  - ABNT compliance checklist

### Bibliography:
- `doc/thesis/latex/Bibliography.bib` - 51 entries (ready to copy)
  - Need to add 27 more entries (list in ABNT_CONVERSION_SUMMARY.md)

### Example ABNT Title Page (from previous work):
```latex
% Page 1 (Capa)
\begin{center}
\includegraphics[width=3.5cm]{gfx/brasao_UFSC.pdf}
\vspace{1cm}
{\large\bfseries UNIVERSIDADE FEDERAL DE SANTA CATARINA\par}
{\large\bfseries PROGRAMA DE PÓS-GRADUAÇÃO EM CIÊNCIA DA COMPUTAÇÃO\par}
\vspace{3cm}
{\Large\bfseries SIMÃO EUGÉNIO\par}
\vspace{3cm}
{\Large\bfseries EXTENDED BIOLOGICAL PETRI NETS:\\
UMA ESTRUTURA FORMAL PARA MODELAGEM DE\\
BIOLOGIA DE SISTEMAS EM MÚLTIPLAS ESCALAS\par}
\vfill
{\large Florianópolis\\2025\par}
\end{center}
\newpage

% Page 2 (Folha de Rosto)
% ... (see ABNT_CONVERSION_SUMMARY.md for complete code)
```

## Contact UFSC for Requirements

Before creating Portuguese version, verify institutional requirements:

### UFSC Resources:
- **BU/UFSC Normalização**: https://portal.bu.ufsc.br/normalizacao/
- **PPGCC Secretariat**: [email/phone]
- **Template Availability**: Check if UFSC provides official LaTeX template

### Questions to Ask:
1. Is ABNT format mandatory for theses in English?
2. Can I submit English version with ABNT formatting?
3. Is full Portuguese translation required?
4. What institutional pages are mandatory (approval sheet, cataloging card)?
5. Are there specific guidelines for Computer Science program?

## Conclusion

**Current Status**: ✅ ABNT changes successfully reverted, ClassicThesis format restored

**Recommendation**: Focus on completing English version first, create Portuguese ABNT version later

**Documentation**: All ABNT conversion knowledge preserved in ABNT_CONVERSION_SUMMARY.md

**Next Steps**: 
1. Add 27 missing bibliography entries
2. Finalize English thesis content
3. Defend thesis using English version
4. After defense: Translate and create Portuguese ABNT version for UFSC repository

---

**Last Updated**: November 27, 2025  
**Maintained by**: Simão Eugénio  
**Related Documents**: 
- `doc/thesis/ABNT_CONVERSION_SUMMARY.md` - Complete ABNT formatting guide
- `doc/thesis/latex/thesis.pdf` - Current international version (243 pages, ClassicThesis)
