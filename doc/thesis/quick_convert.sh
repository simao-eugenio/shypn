#!/bin/bash
# Quick conversion script (no installation prompts)

THESIS_DIR="/home/simao/projetos/shypn/doc/thesis"
LATEX_DIR="$THESIS_DIR/latex"
CHAPTERS_DIR="$LATEX_DIR/chapters"

echo "=== Converting Thesis to LaTeX ==="

# Create directories
mkdir -p "$CHAPTERS_DIR" "$LATEX_DIR/figures" "$LATEX_DIR/tables"

# Convert chapters
for i in {01..15}; do
    CHAPTER_FILE="$THESIS_DIR/Chapter_${i}_"*.md
    
    if ls $CHAPTER_FILE 1> /dev/null 2>&1; then
        ACTUAL_FILE=$(ls $CHAPTER_FILE | head -n 1)
        OUTPUT_FILE="$CHAPTERS_DIR/chapter_${i}.tex"
        
        echo "Converting Chapter ${i}..."
        
        pandoc "$ACTUAL_FILE" \
            -f markdown \
            -t latex \
            --top-level-division=chapter \
            --number-sections \
            --listings \
            -o "$OUTPUT_FILE"
        
        echo "  ✓ $OUTPUT_FILE"
    fi
done

echo ""
echo "✓ All chapters converted!"
echo "✓ LaTeX files in: $LATEX_DIR"
echo ""
echo "To compile: cd $LATEX_DIR && make"
