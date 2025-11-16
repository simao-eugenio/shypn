"""PDF document generator using WeasyPrint for HTML-to-PDF conversion."""

from pathlib import Path
from typing import Dict, Any

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

from .base_generator import BaseDocumentGenerator, DocumentType
from .html_generator import HTMLGenerator


class PDFGenerator(BaseDocumentGenerator):
    """Generator for PDF documents using WeasyPrint.
    
    This generator leverages the HTMLGenerator to create HTML content
    and then converts it to PDF format using WeasyPrint.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the PDF generator.
        
        Raises:
            ImportError: If WeasyPrint is not installed
        """
        if not WEASYPRINT_AVAILABLE:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Install it with: pip install weasyprint"
            )
        super().__init__(*args, **kwargs)
        self.html_generator = HTMLGenerator(self.metadata, self.user_profile)
    
    def get_file_extension(self) -> str:
        """Get the file extension for PDF files."""
        return ".pdf"
    
    def _generate_impl(self,
                       output_path: Path,
                       document_data: Dict[str, Any],
                       document_type: DocumentType) -> None:
        """Generate a PDF document from HTML.
        
        Args:
            output_path: Where to save the PDF file
            document_data: All data for the document
            document_type: Type of document to generate
        """
        # Generate HTML content using HTMLGenerator
        if document_type == DocumentType.TECHNICAL:
            html_content = self.html_generator._generate_technical_html(document_data)
        elif document_type == DocumentType.PUBLICATION:
            html_content = self.html_generator._generate_publication_html(document_data)
        else:  # SUMMARY
            html_content = self.html_generator._generate_summary_html(document_data)
        
        # Convert HTML to PDF
        html_doc = HTML(string=html_content)
        
        # Add PDF-specific CSS for better print layout
        pdf_css = CSS(string=self._get_pdf_css())
        
        # Render to PDF
        html_doc.write_pdf(
            str(output_path),
            stylesheets=[pdf_css]
        )
    
    def _get_pdf_css(self) -> str:
        """Get PDF-specific CSS for optimal print layout.
        
        Returns:
            CSS string for PDF rendering
        """
        return """
        @page {
            size: A4;
            margin: 1.5cm;
        }
        
        body {
            background: white;
            padding: 0;
        }
        
        .container {
            max-width: 100%;
            box-shadow: none;
            padding: 0;
        }
        
        h1 {
            page-break-after: avoid;
            page-break-before: auto;
        }
        
        h2 {
            page-break-after: avoid;
            page-break-before: auto;
            orphans: 3;
            widows: 3;
        }
        
        h3 {
            page-break-after: avoid;
            orphans: 2;
            widows: 2;
        }
        
        .section {
            page-break-inside: auto;
        }
        
        table {
            page-break-inside: auto;
        }
        
        table.compact-table, table.extra-compact-table {
            page-break-inside: auto;
        }
        
        tr {
            page-break-inside: avoid;
        }
        
        /* Ensure links are visible in print */
        a {
            color: #2980b9;
            text-decoration: underline;
        }
        
        /* Better printing for lists */
        ul, ol {
            page-break-inside: auto;
        }
        
        li {
            orphans: 2;
            widows: 2;
        }
        
        /* Keep related content together */
        .summary-box {
            page-break-inside: avoid;
        }
        """
