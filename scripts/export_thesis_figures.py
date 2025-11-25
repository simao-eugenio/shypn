#!/usr/bin/env python3
"""Export Petri Net models as high-quality figures for thesis.

This script loads SHYpn models and exports them as:
- PNG (for quick previews)
- PDF (vector format for LaTeX)
- SVG (editable vector format)
- TikZ (LaTeX-native format)

Usage:
    python scripts/export_thesis_figures.py --model examples/01_atp_synthesis.shy --output doc/thesis/latex/gfx/
    python scripts/export_thesis_figures.py --all --output doc/thesis/latex/gfx/
"""

import argparse
import json
import math
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

try:
    import cairo
except ImportError:
    print("ERROR: pycairo not installed. Install with: pip install pycairo")
    sys.exit(1)

from shypn.data.canvas.document_model import DocumentModel


class ThesisFigureExporter:
    """Export SHYpn models as publication-quality figures."""
    
    def __init__(self, dpi: int = 300, margin: float = 50.0):
        """Initialize exporter.
        
        Args:
            dpi: Dots per inch for raster outputs (PNG)
            margin: Margin around model in pixels
        """
        self.dpi = dpi
        self.margin = margin
    
    def load_model(self, filepath: str) -> DocumentModel:
        """Load SHYpn model from .shy file.
        
        Args:
            filepath: Path to .shy JSON file
            
        Returns:
            DocumentModel instance
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model = DocumentModel()
        model.from_dict(data)
        return model
    
    def calculate_bounds(self, model: DocumentModel) -> Tuple[float, float, float, float]:
        """Calculate bounding box of model.
        
        Args:
            model: DocumentModel instance
            
        Returns:
            (min_x, min_y, max_x, max_y) tuple
        """
        if not model.places and not model.transitions:
            return (0, 0, 100, 100)
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        # Check places
        for place in model.places:
            min_x = min(min_x, place.x - place.radius)
            max_x = max(max_x, place.x + place.radius)
            min_y = min(min_y, place.y - place.radius)
            max_y = max(max_y, place.y + place.radius)
        
        # Check transitions
        for transition in model.transitions:
            half_width = transition.width / 2
            half_height = transition.height / 2
            min_x = min(min_x, transition.x - half_width)
            max_x = max(max_x, transition.x + half_width)
            min_y = min(min_y, transition.y - half_height)
            max_y = max(max_y, transition.y + half_height)
        
        return (min_x, min_y, max_x, max_y)
    
    def export_png(self, model: DocumentModel, output_path: str, 
                   width: Optional[int] = None, height: Optional[int] = None):
        """Export model as PNG image.
        
        Args:
            model: DocumentModel instance
            output_path: Output PNG file path
            width: Optional fixed width (auto-calculated if None)
            height: Optional fixed height (auto-calculated if None)
        """
        # Calculate bounds
        min_x, min_y, max_x, max_y = self.calculate_bounds(model)
        model_width = max_x - min_x
        model_height = max_y - min_y
        
        # Calculate canvas size with margins
        if width is None:
            width = int(model_width + 2 * self.margin)
        if height is None:
            height = int(model_height + 2 * self.margin)
        
        # Create surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
        cr = cairo.Context(surface)
        
        # White background
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        
        # Transform: translate to center model with margin
        cr.translate(self.margin - min_x, self.margin - min_y)
        
        # Render model
        self._render_model(cr, model, zoom=1.0)
        
        # Save
        surface.write_to_png(output_path)
        surface.finish()
        print(f"✅ Exported PNG: {output_path} ({width}×{height})")
    
    def export_pdf(self, model: DocumentModel, output_path: str,
                   width: Optional[float] = None, height: Optional[float] = None):
        """Export model as PDF (vector format).
        
        Args:
            model: DocumentModel instance
            output_path: Output PDF file path
            width: Optional fixed width in points (auto-calculated if None)
            height: Optional fixed height in points (auto-calculated if None)
        """
        # Calculate bounds
        min_x, min_y, max_x, max_y = self.calculate_bounds(model)
        model_width = max_x - min_x
        model_height = max_y - min_y
        
        # Calculate canvas size with margins (in points, 1 point = 1/72 inch)
        if width is None:
            width = model_width + 2 * self.margin
        if height is None:
            height = model_height + 2 * self.margin
        
        # Create surface
        surface = cairo.PDFSurface(output_path, width, height)
        cr = cairo.Context(surface)
        
        # White background
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        
        # Transform: translate to center model with margin
        cr.translate(self.margin - min_x, self.margin - min_y)
        
        # Render model
        self._render_model(cr, model, zoom=1.0)
        
        # Finish
        cr.show_page()
        surface.finish()
        print(f"✅ Exported PDF: {output_path} ({width:.1f}×{height:.1f} points)")
    
    def export_svg(self, model: DocumentModel, output_path: str,
                   width: Optional[float] = None, height: Optional[float] = None):
        """Export model as SVG (editable vector format).
        
        Args:
            model: DocumentModel instance
            output_path: Output SVG file path
            width: Optional fixed width in points (auto-calculated if None)
            height: Optional fixed height in points (auto-calculated if None)
        """
        # Calculate bounds
        min_x, min_y, max_x, max_y = self.calculate_bounds(model)
        model_width = max_x - min_x
        model_height = max_y - min_y
        
        # Calculate canvas size with margins
        if width is None:
            width = model_width + 2 * self.margin
        if height is None:
            height = model_height + 2 * self.margin
        
        # Create surface
        surface = cairo.SVGSurface(output_path, width, height)
        cr = cairo.Context(surface)
        
        # White background
        cr.set_source_rgb(1, 1, 1)
        cr.paint()
        
        # Transform: translate to center model with margin
        cr.translate(self.margin - min_x, self.margin - min_y)
        
        # Render model
        self._render_model(cr, model, zoom=1.0)
        
        # Finish
        surface.finish()
        print(f"✅ Exported SVG: {output_path} ({width:.1f}×{height:.1f} points)")
    
    def export_tikz(self, model: DocumentModel, output_path: str):
        """Export model as TikZ/LaTeX code.
        
        Args:
            model: DocumentModel instance
            output_path: Output .tex file path
        """
        # Calculate bounds for proper scaling
        min_x, min_y, max_x, max_y = self.calculate_bounds(model)
        
        # Generate TikZ code
        lines = []
        lines.append("% Generated by SHYpn Thesis Figure Exporter")
        lines.append("% Compile with: pdflatex")
        lines.append("\\begin{tikzpicture}[")
        lines.append("  place/.style={circle, draw=black, thick, minimum size=60pt},")
        lines.append("  transition/.style={rectangle, draw=black, thick, fill=black, minimum width=10pt, minimum height=40pt},")
        lines.append("  arc/.style={->, thick},")
        lines.append("  test/.style={->, thick, dashed},")
        lines.append("  inhibitor/.style={-o, thick}")
        lines.append("]")
        lines.append("")
        
        # Draw places
        lines.append("  % Places")
        for place in model.places:
            # Scale coordinates (TikZ uses cm by default)
            x_cm = place.x / 72  # 72 points per inch, ~2.54cm per inch
            y_cm = -place.y / 72  # Flip Y axis (TikZ origin is bottom-left)
            
            label = place.label or place.name
            tokens_str = f", label=center:{place.tokens}" if place.tokens > 0 else ""
            lines.append(f"  \\node[place] ({place.name}) at ({x_cm:.2f}cm, {y_cm:.2f}cm) {{{label}{tokens_str}}};")
        
        lines.append("")
        
        # Draw transitions
        lines.append("  % Transitions")
        for transition in model.transitions:
            x_cm = transition.x / 72
            y_cm = -transition.y / 72
            
            label = transition.label or transition.name
            lines.append(f"  \\node[transition] ({transition.name}) at ({x_cm:.2f}cm, {y_cm:.2f}cm) {{}};")
            lines.append(f"  \\node[above=2pt of {transition.name}] {{{label}}};")
        
        lines.append("")
        
        # Draw arcs
        lines.append("  % Arcs")
        for arc in model.arcs:
            # Determine arc style
            if hasattr(arc, 'arc_type'):
                if arc.arc_type == 'test':
                    style = "test"
                elif arc.arc_type == 'inhibitor':
                    style = "inhibitor"
                else:
                    style = "arc"
            else:
                style = "arc"
            
            source_name = arc.source_id.replace('place_', 'P').replace('transition_', 'T')
            target_name = arc.target_id.replace('place_', 'P').replace('transition_', 'T')
            
            weight_str = f", edge label={{{arc.weight}}}" if arc.weight != 1 else ""
            lines.append(f"  \\draw[{style}] ({source_name}) -- ({target_name}){weight_str};")
        
        lines.append("")
        lines.append("\\end{tikzpicture}")
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print(f"✅ Exported TikZ: {output_path}")
    
    def _render_model(self, cr: cairo.Context, model: DocumentModel, zoom: float = 1.0):
        """Render complete model to Cairo context.
        
        Args:
            cr: Cairo context
            model: DocumentModel instance
            zoom: Zoom level (1.0 = 100%)
        """
        # Render arcs first (background layer)
        for arc in model.arcs:
            arc.render(cr, zoom=zoom)
        
        # Render places
        for place in model.places:
            place.render(cr, zoom=zoom)
        
        # Render transitions
        for transition in model.transitions:
            transition.render(cr, zoom=zoom)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Export SHYpn models as thesis figures",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export single model to all formats
  python scripts/export_thesis_figures.py --model examples/01_atp_synthesis.shy --output doc/thesis/latex/gfx/

  # Export all example models
  python scripts/export_thesis_figures.py --all --output doc/thesis/latex/gfx/

  # Export specific model as PDF only
  python scripts/export_thesis_figures.py --model examples/09_glycolysis.shy --format pdf --output doc/thesis/latex/gfx/
"""
    )
    
    parser.add_argument('--model', type=str, help='Path to .shy model file')
    parser.add_argument('--all', action='store_true', help='Export all example models')
    parser.add_argument('--output', type=str, default='doc/thesis/latex/gfx/', help='Output directory')
    parser.add_argument('--format', type=str, choices=['png', 'pdf', 'svg', 'tikz', 'all'], 
                        default='all', help='Output format')
    parser.add_argument('--dpi', type=int, default=300, help='DPI for PNG export (default: 300)')
    parser.add_argument('--width', type=int, help='Fixed width in pixels/points')
    parser.add_argument('--height', type=int, help='Fixed height in pixels/points')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.model and not args.all:
        parser.error("Must specify either --model or --all")
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize exporter
    exporter = ThesisFigureExporter(dpi=args.dpi)
    
    # Get model files to export
    if args.all:
        examples_dir = Path(__file__).parent.parent / 'examples'
        model_files = sorted(examples_dir.glob('*.shy'))
        if not model_files:
            print(f"❌ No .shy files found in {examples_dir}")
            return 1
    else:
        model_files = [Path(args.model)]
        if not model_files[0].exists():
            print(f"❌ Model file not found: {args.model}")
            return 1
    
    print(f"📦 Exporting {len(model_files)} model(s) to {output_dir}")
    print(f"📐 Format(s): {args.format}")
    print()
    
    # Export each model
    for model_path in model_files:
        print(f"🔄 Processing: {model_path.name}")
        
        try:
            # Load model
            model = exporter.load_model(str(model_path))
            
            # Generate base output filename
            base_name = model_path.stem
            
            # Export requested formats
            formats = ['png', 'pdf', 'svg', 'tikz'] if args.format == 'all' else [args.format]
            
            for fmt in formats:
                output_file = output_dir / f"{base_name}.{fmt}"
                
                if fmt == 'png':
                    exporter.export_png(model, str(output_file), width=args.width, height=args.height)
                elif fmt == 'pdf':
                    exporter.export_pdf(model, str(output_file), width=args.width, height=args.height)
                elif fmt == 'svg':
                    exporter.export_svg(model, str(output_file), width=args.width, height=args.height)
                elif fmt == 'tikz':
                    output_file = output_dir / f"{base_name}.tex"
                    exporter.export_tikz(model, str(output_file))
            
            print()
        
        except Exception as e:
            print(f"❌ Error exporting {model_path.name}: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    print("✅ Export complete!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
