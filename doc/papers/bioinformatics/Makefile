# Makefile for compiling Bioinformatics paper

PAPER = paper
LATEX = pdflatex
BIBTEX = bibtex

.PHONY: all clean

all: $(PAPER).pdf

$(PAPER).pdf: $(PAPER).tex references.bib bioinfo.cls
	$(LATEX) $(PAPER)
	$(BIBTEX) $(PAPER)
	$(LATEX) $(PAPER)
	$(LATEX) $(PAPER)

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out $(PAPER).toc

distclean: clean
	rm -f $(PAPER).pdf

view: $(PAPER).pdf
	xdg-open $(PAPER).pdf 2>/dev/null || open $(PAPER).pdf 2>/dev/null || echo "Please open $(PAPER).pdf manually"

# Quick compile (no bibtex)
quick:
	$(LATEX) $(PAPER)

# Full clean and rebuild
rebuild: distclean all
