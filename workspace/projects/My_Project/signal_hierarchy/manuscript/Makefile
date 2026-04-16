# Makefile for Signal Hierarchy paper
# Bioinformatics two-column format

MAIN = main
TEX = pdflatex
BIB = bibtex

# Default target: compile PDF
all: pdf

# Compile PDF (run multiple times for references)
pdf:
	$(TEX) $(MAIN).tex
	$(BIB) $(MAIN)
	$(TEX) $(MAIN).tex
	$(TEX) $(MAIN).tex

# Quick compile (single pass, for draft checking)
draft:
	$(TEX) $(MAIN).tex

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.bbl *.blg *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz

# Clean everything including PDF
distclean: clean
	rm -f $(MAIN).pdf

# View PDF
view: pdf
	xdg-open $(MAIN).pdf 2>/dev/null || open $(MAIN).pdf || evince $(MAIN).pdf &

# Help
help:
	@echo "Signal Hierarchy Paper - Makefile"
	@echo "=================================="
	@echo "Targets:"
	@echo "  all (default) - Compile PDF with references"
	@echo "  draft         - Quick compile (single pass)"
	@echo "  clean         - Remove auxiliary files"
	@echo "  distclean     - Remove all generated files"
	@echo "  view          - Compile and open PDF"
	@echo "  help          - Show this message"
	@echo ""
	@echo "Usage: make [target]"

.PHONY: all pdf draft clean distclean view help
