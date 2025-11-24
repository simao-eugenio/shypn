# Makefile for Extended Bio-PN Thesis

MAIN = thesis
LATEX = pdflatex
BIBER = biber

.PHONY: all clean cleanall view help

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex Chapters/*.tex FrontBackmatter/*.tex classicthesis-config.tex
	@echo "=== First LaTeX pass ==="
	$(LATEX) -interaction=nonstopmode $(MAIN)
	@echo ""
	@echo "=== Running Biber ==="
	$(BIBER) $(MAIN)
	@echo ""
	@echo "=== Second LaTeX pass ==="
	$(LATEX) -interaction=nonstopmode $(MAIN)
	@echo ""
	@echo "=== Final LaTeX pass ==="
	$(LATEX) -interaction=nonstopmode $(MAIN)
	@echo ""
	@echo "✓ Thesis compiled successfully: $(MAIN).pdf"

quick:
	@echo "=== Quick compile (no biber) ==="
	$(LATEX) -interaction=nonstopmode $(MAIN)

clean:
	@echo "Cleaning auxiliary files..."
	@rm -f *.aux *.log *.out *.toc *.lof *.lot *.bbl *.blg *.bcf *.run.xml *.synctex.gz
	@rm -f Chapters/*.aux FrontBackmatter/*.aux
	@echo "✓ Clean complete"

cleanall: clean
	@echo "Removing PDF..."
	@rm -f $(MAIN).pdf
	@echo "✓ All files removed"

view: $(MAIN).pdf
	@xdg-open $(MAIN).pdf &

help:
	@echo "Available targets:"
	@echo "  all       - Compile thesis (default)"
	@echo "  quick     - Quick compile without bibliography"
	@echo "  clean     - Remove auxiliary files"
	@echo "  cleanall  - Remove all generated files including PDF"
	@echo "  view      - Open PDF with default viewer"
	@echo "  help      - Show this help message"
