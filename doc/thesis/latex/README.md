# Extended Biological Petri Nets - PhD Thesis (LaTeX)

This directory contains the LaTeX version of the thesis using the ClassicThesis template.

## 📁 Structure

```
latex/
├── thesis.tex                 # Main thesis file
├── classicthesis-config.tex   # ClassicThesis configuration
├── classicthesis.sty          # ClassicThesis style file
├── Bibliography.bib           # BibTeX references
├── Makefile                   # Build automation
├── FrontBackmatter/           # Front and back matter
│   ├── Titlepage.tex
│   ├── Abstract.tex
│   ├── Acknowledgments.tex
│   ├── Contents.tex
│   └── Bibliography.tex
├── Chapters/                  # All 15 chapters
│   ├── chapter_01.tex
│   ├── chapter_02.tex
│   └── ...
├── gfx/                       # Graphics and figures
└── classicthesis/             # Original ClassicThesis template
```

## 🚀 Quick Start

### Compile the thesis:

```bash
cd latex
make
```

This will:
1. Run pdflatex (first pass)
2. Run biber (bibliography)
3. Run pdflatex (second pass)
4. Run pdflatex (final pass)

Output: `thesis.pdf`

### View the PDF:

```bash
make view
```

### Clean auxiliary files:

```bash
make clean      # Keep PDF
make cleanall   # Remove PDF too
```

### Quick compile (skip bibliography):

```bash
make quick
```

## 📝 Customization

### 1. Edit Title Page

Edit `FrontBackmatter/Titlepage.tex`:
- Change your name
- Add university name
- Update date

### 2. Edit Abstract

Edit `FrontBackmatter/Abstract.tex` (already filled with thesis abstract)

### 3. Add Acknowledgments

Edit `FrontBackmatter/Acknowledgments.tex`:
- Thank your supervisor
- Acknowledge funding
- Thank collaborators

### 4. Configure ClassicThesis

Edit `classicthesis-config.tex`:

```latex
% Change thesis title
\newcommand{\myTitle}{Your Title Here\xspace}

% Change author
\newcommand{\myName}{Your Name\xspace}

% Change colors (optional)
\definecolor{CTsemi}{HTML}{801010}  % Maroon
```

### 5. Add Figures

Place figures in `gfx/` directory:

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.8\textwidth]{gfx/my_figure.pdf}
    \caption{Figure caption}
    \label{fig:my_figure}
\end{figure}
```

Reference: `See~\autoref{fig:my_figure}`

### 6. Add References

Edit `Bibliography.bib`:

```bibtex
@article{AuthorYear,
    author = {Author, A. and Author, B.},
    title = {Title of Paper},
    journal = {Journal Name},
    year = {2024}
}
```

Cite: `\cite{AuthorYear}` or `\textcite{AuthorYear}`

## 🔧 Requirements

Install LaTeX packages:

```bash
# Full installation (recommended, ~4 GB)
sudo apt-get install texlive-full biber

# Or minimal installation
sudo apt-get install texlive-latex-base texlive-latex-extra \
    texlive-fonts-recommended texlive-science \
    texlive-bibtex-extra biber
```

## 📖 ClassicThesis Features

ClassicThesis provides:
- ✅ Beautiful typography (inspired by Robert Bringhurst)
- ✅ Clean margins and spacing
- ✅ Professional chapter headings
- ✅ Elegant page headers/footers
- ✅ Optimized for printing and reading

## 🐛 Troubleshooting

### Problem: "File not found" errors

**Solution:** Run `make clean` then `make`

### Problem: Missing fonts

**Solution:** Install additional fonts:
```bash
sudo apt-get install texlive-fonts-extra
```

### Problem: Bibliography not appearing

**Solution:** Ensure you run full compilation:
```bash
pdflatex thesis
biber thesis
pdflatex thesis
pdflatex thesis
```

Or simply: `make`

### Problem: Overfull/underfull boxes

**Solution:** These are warnings, not errors. The PDF is still created. To fix:
- Reword text
- Add `\linebreak` or `\allowbreak` hints
- Adjust hyphenation in `thesis.tex`

## 📊 Statistics

- **Total chapters:** 15
- **Estimated pages:** ~250-300 pages
- **Word count:** ~195,600 words
- **Compilation time:** ~30-60 seconds (first run)

## 🎨 Alternative Styles

ClassicThesis includes variants:

1. **ArsClassica** (more traditional):
   ```latex
   % In thesis.tex, replace:
   \usepackage{classicthesis}
   % with:
   \usepackage{classicthesis-arsclassica}
   ```

2. **Lined headers** (chapter number lines):
   ```latex
   \usepackage{classicthesis-linedheaders}
   ```

## 📚 Resources

- **ClassicThesis manual:** See `classicthesis/ClassicThesis.pdf`
- **CTAN page:** https://www.ctan.org/pkg/classicthesis
- **Template examples:** Check `classicthesis/Examples/`

## ✅ Next Steps

1. ✅ Chapters converted from Markdown
2. ⏳ Add your university name (Titlepage.tex)
3. ⏳ Fill in Acknowledgments
4. ⏳ Add figures to gfx/
5. ⏳ Add citations to Bibliography.bib
6. ⏳ Compile: `make`
7. ⏳ Review PDF and adjust formatting

## 🎓 Compilation Checklist

Before final submission:

- [ ] All figures included and referenced
- [ ] All citations added to Bibliography.bib
- [ ] Acknowledgments completed
- [ ] University name on title page
- [ ] No compilation errors or warnings
- [ ] PDF page count reasonable (250-350 pages)
- [ ] All chapters have content
- [ ] Table of contents generated
- [ ] List of figures/tables generated
- [ ] Bibliography appears at end

Good luck with your thesis! 🚀
