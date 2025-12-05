# Paper: Weak Independence in Biological Petri Nets

## Files

- `weak_independence_biopn.tex` - Main LaTeX paper (LLNCS format for Petri Nets Conference / CMSB)
- `references.bib` - BibTeX bibliography
- `SHYPN_INNOVATIONS.md` - Extended documentation of innovations

## Compilation

### Requirements
```bash
# Install LaTeX distribution
sudo apt-get install texlive-full  # Ubuntu/Debian
# OR
brew install --cask mactex  # macOS

# Install required packages
tlmgr install llncs tikz-petri algorithms booktabs
```

### Build
```bash
cd doc/papers
pdflatex weak_independence_biopn.tex
bibtex weak_independence_biopn
pdflatex weak_independence_biopn.tex
pdflatex weak_independence_biopn.tex  # Run twice for references
```

Or use latexmk (automated):
```bash
latexmk -pdf weak_independence_biopn.tex
```

## Paper Structure

### Sections
1. **Introduction** (2 pages)
   - Motivating example (glucose metabolism)
   - Problem statement (classical independence too restrictive)
   - Contributions (4 key innovations)

2. **Background and Related Work** (2 pages)
   - Classical Petri nets
   - Biological Petri nets (Reddy 1993, Heiner 2008)
   - Existing tools (Snoopy, Cell Illustrator, Charlie)
   - Gap in literature

3. **Extended Bio-PN Definition** (1.5 pages)
   - 10-tuple formalization
   - Novel components (Σ, Θ, Δ)

4. **Weak Independence Theory** (2 pages)
   - Strong vs weak independence
   - Three coupling modes (competitive, convergent, regulatory)
   - Theorem 1: Correctness of parallel execution

5. **Dependency Classification Algorithm** (1 page)
   - Algorithm 1 pseudocode
   - Complexity analysis

6. **Biological Topology Analyzers** (1.5 pages)
   - Mass balance analyzer
   - Flux balance analyzer
   - Regulatory structure analyzer

7. **Evaluation** (3 pages)
   - Dataset: 100 BioModels
   - Table 1: Dependency distribution (65% weakly independent)
   - Figure 1: Speedup plot (2-4× improvement)
   - Table 2: Validation accuracy (72% → 5% false positives)

8. **Implementation: Shypn Tool** (0.5 pages)
   - Architecture overview
   - SBML integration
   - Availability

9. **Discussion** (1.5 pages)
   - Theoretical significance
   - Practical impact
   - Limitations and future work

10. **Related Work Comparison** (1 page)
    - Table 3: Feature comparison with existing tools

11. **Conclusion** (0.5 pages)

**Total**: ~15 pages (conference format)

## TODO Before Submission

### Implementation Tasks
- [ ] Implement dependency classifier (`src/shypn/diagnostic/dependency_classifier.py`)
- [ ] Implement biological analyzers:
  - [ ] Mass balance (`src/shypn/topology/biological/mass_balance.py`)
  - [ ] Flux balance (`src/shypn/topology/biological/flux_balance.py`)
  - [ ] Regulatory structure (`src/shypn/topology/biological/regulation.py`)
- [ ] Add parallel scheduler (`src/shypn/engine/simulation/parallel_scheduler.py`)

### Evaluation Tasks
- [ ] Run dependency classification on 100 BioModels
- [ ] Collect dependency distribution statistics (Table 1)
- [ ] Benchmark parallel simulation speedup (Figure 1)
- [ ] Measure validation false positive rates (Table 2)

### Paper Tasks
- [ ] Create Figure 1 (speedup plot): `figures/speedup_plot.pdf`
- [ ] Create TikZ Petri net examples (inline in LaTeX)
- [ ] Complete proof of Theorem 1 (currently sketch)
- [ ] Add complexity analysis details
- [ ] Write acknowledgments section
- [ ] Add GitHub repository URL
- [ ] Proofread and check citations

### Figures Needed

1. **Figure 1** (`figures/speedup_plot.pdf`): 
   - X-axis: Number of cores (1, 2, 4, 8)
   - Y-axis: Speedup factor
   - Lines: Different BioModels (BIOMD0000000001, BIOMD0000000010, etc.)
   - Ideal speedup line (dashed)

2. **Figure 2** (optional, inline TikZ): Petri net diagrams
   - Glucose metabolism example (already in LaTeX)
   - Competitive vs convergent vs regulatory sharing

## Submission Targets

### Priority 1: Petri Nets Conference (ICATPN)
- **Deadline**: Typically February/March (check current year)
- **Format**: LLNCS (current template)
- **Length**: 15-20 pages
- **URL**: http://www.petrinets.org/

### Priority 2: CMSB (Computational Methods in Systems Biology)
- **Deadline**: Typically May/June
- **Format**: LNCS/LNBI (same as LLNCS)
- **Length**: 15-20 pages
- **URL**: http://www.cmsb-conference.org/

### Priority 3: Bioinformatics Journal
- **Submission**: Rolling
- **Format**: Oxford style (need to convert)
- **Length**: 8-10 pages + supplement
- **URL**: https://academic.oup.com/bioinformatics

## LaTeX Tips

### Compile Errors?
```bash
# Clear auxiliary files
rm *.aux *.bbl *.blg *.log *.out

# Rebuild
pdflatex weak_independence_biopn.tex
bibtex weak_independence_biopn
pdflatex weak_independence_biopn.tex
pdflatex weak_independence_biopn.tex
```

### Add More References
Edit `references.bib`:
```bibtex
@article{YourKey2025,
  author = {Last, First},
  title = {Paper Title},
  journal = {Journal Name},
  year = {2025}
}
```

Cite in text: `\cite{YourKey2025}`

### Add Figures
```latex
\begin{figure}[t]
\centering
\includegraphics[width=0.8\linewidth]{figures/your_figure.pdf}
\caption{Your caption here.}
\label{fig:your_label}
\end{figure}
```

Reference: `Figure~\ref{fig:your_label}`

### Add Algorithms
```latex
\begin{algorithm}[t]
\caption{Algorithm Name}
\label{alg:your_label}
\begin{algorithmic}[1]
\REQUIRE Input
\ENSURE Output
\STATE Step 1
\FOR{each item}
    \STATE Do something
\ENDFOR
\end{algorithmic}
\end{algorithm}
```

## Contact

For questions about the paper structure or content:
- Email: [your email]
- GitHub: [repository URL]

## License

This paper is prepared for academic publication. Copyright will be transferred to the publisher upon acceptance.
