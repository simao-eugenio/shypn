"""HTML document generator for creating styled HTML reports."""

from pathlib import Path
from typing import Dict, Any
import html

from .base_generator import BaseDocumentGenerator, DocumentType


class HTMLGenerator(BaseDocumentGenerator):
    """Generator for HTML documents with embedded CSS styling."""
    
    def get_file_extension(self) -> str:
        """Get the file extension for HTML files."""
        return ".html"
    
    def _generate_impl(self,
                       output_path: Path,
                       document_data: Dict[str, Any],
                       document_type: DocumentType) -> None:
        """Generate an HTML document.
        
        Args:
            output_path: Where to save the HTML file
            document_data: All data for the document
            document_type: Type of document to generate
        """
        # Generate HTML content based on document type
        if document_type == DocumentType.TECHNICAL:
            html_content = self._generate_technical_html(document_data)
        elif document_type == DocumentType.PUBLICATION:
            html_content = self._generate_publication_html(document_data)
        else:  # SUMMARY
            html_content = self._generate_summary_html(document_data)
        
        # Write to file
        output_path.write_text(html_content, encoding='utf-8')
    
    def _generate_technical_html(self, data: Dict[str, Any]) -> str:
        """Generate a comprehensive technical report in HTML.
        
        Args:
            data: Document data dictionary
            
        Returns:
            Complete HTML document as string
        """
        metadata = data["metadata"]
        generation_date = self.format_date(data.get("generation_date"))
        
        # Build HTML
        html_parts = [
            self._get_html_header("Technical Report", include_technical_css=True),
            "<body>",
            '<div class="container">',
        ]
        
        # Title
        model_name = html.escape(metadata.get("basic", {}).get("model_name", "Untitled Model"))
        html_parts.append(f'<h1 class="title">{model_name}</h1>')
        html_parts.append(f'<p class="subtitle">Technical Report</p>')
        html_parts.append(f'<p class="generation-date">Generated: {generation_date}</p>')
        
        # Basic Information
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Basic Information</h2>')
        html_parts.append(self._format_basic_info(metadata.get("basic", {})))
        html_parts.append('</div>')
        
        # Authorship
        if data.get("has_authors"):
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Authorship</h2>')
            html_parts.append(self._format_authorship(metadata.get("authorship", {})))
            html_parts.append('</div>')
        
        # Biological Context
        if data.get("has_biological_context"):
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Biological Context</h2>')
            html_parts.append(self._format_biological_context(metadata.get("biological_context", {})))
            html_parts.append('</div>')
        
        # Provenance
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Provenance</h2>')
        html_parts.append(self._format_provenance(metadata.get("provenance", {})))
        html_parts.append('</div>')
        
        # References
        if data.get("has_references"):
            html_parts.append('<div class="section">')
            html_parts.append('<h2>References</h2>')
            html_parts.append(self._format_references(metadata.get("references", {})))
            html_parts.append('</div>')
        
        # System Information
        html_parts.append('<div class="section">')
        html_parts.append('<h2>System Information</h2>')
        html_parts.append(self._format_system_info(metadata.get("system", {})))
        html_parts.append('</div>')
        
        # Report Panel Data (if available)
        report_data = data.get("additional", {}).get("report_data", {})
        print(f"[HTML_GEN] report_data keys: {list(report_data.keys())}")
        print(f"[HTML_GEN] report_data present: {bool(report_data)}")
        if report_data:
            print(f"[HTML_GEN] Generating report data sections...")
            # Executive Summary (NEW)
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Summary</h2>')
            html_parts.append(self._format_summary_section(report_data))
            html_parts.append('</div>')
            print(f"[HTML_GEN] ✓ Summary section added")
            
            # Model Structure
            if 'model' in report_data and report_data['model'].get('has_data'):
                html_parts.append('<div class="section">')
                html_parts.append('<h2>Model Structure</h2>')
                html_parts.append(self._format_model_structure(report_data['model']))
                html_parts.append('</div>')
                print(f"[HTML_GEN] ✓ Model Structure section added")
            else:
                print(f"[HTML_GEN] ✗ Model Structure section skipped (has_data={report_data.get('model', {}).get('has_data', False)})")
            
            # Dynamic Analyses (includes Species Concentration & Reaction Activity)
            if 'dynamic' in report_data and report_data['dynamic'].get('has_data'):
                html_parts.append('<div class="section">')
                html_parts.append('<h2>Dynamic Analyses</h2>')
                html_parts.append(self._format_dynamic_analyses(report_data['dynamic']))
                html_parts.append('</div>')
                print(f"[HTML_GEN] ✓ Dynamic Analyses section added")
            else:
                print(f"[HTML_GEN] ✗ Dynamic Analyses section skipped (has_data={report_data.get('dynamic', {}).get('has_data', False)})")
            
            # Topology Analyses (includes Key Findings in tabular form)
            if 'topology' in report_data and report_data['topology'].get('has_data'):
                html_parts.append('<div class="section">')
                html_parts.append('<h2>Topology Analyses</h2>')
                html_parts.append(self._format_topology_analyses(report_data['topology']))
                html_parts.append('</div>')
                print(f"[HTML_GEN] ✓ Topology Analyses section added")
            else:
                print(f"[HTML_GEN] ✗ Topology Analyses section skipped (has_data={report_data.get('topology', {}).get('has_data', False)})")
            
            # Provenance Data
            if 'provenance' in report_data and report_data['provenance'].get('has_data'):
                html_parts.append('<div class="section">')
                html_parts.append('<h2>Data Provenance</h2>')
                html_parts.append(self._format_provenance_data(report_data['provenance']))
                html_parts.append('</div>')
                print(f"[HTML_GEN] ✓ Data Provenance section added")
            else:
                print(f"[HTML_GEN] ✗ Data Provenance section skipped (has_data={report_data.get('provenance', {}).get('has_data', False)})")
        else:
            print(f"[HTML_GEN] No report_data available - skipping all report sections")
        
        # Close
        html_parts.extend(['</div>', '</body>', '</html>'])
        
        return "\n".join(html_parts)
    
    def _generate_publication_html(self, data: Dict[str, Any]) -> str:
        """Generate a publication-ready document in HTML.
        
        Args:
            data: Document data dictionary
            
        Returns:
            Complete HTML document as string
        """
        metadata = data["metadata"]
        
        html_parts = [
            self._get_html_header("Publication Document", include_publication_css=True),
            "<body>",
            '<div class="container publication">',
        ]
        
        # Title and authors
        model_name = html.escape(metadata.get("basic", {}).get("model_name", "Untitled Model"))
        html_parts.append(f'<h1 class="title">{model_name}</h1>')
        
        # Format authors from primary_author and contributors
        authorship = metadata.get("authorship", {})
        primary = authorship.get("primary_author")
        contributors = authorship.get("contributors", [])
        
        if primary:
            if contributors:
                author_str = f"{primary} et al."
            else:
                author_str = primary
            html_parts.append(f'<p class="authors">{html.escape(author_str)}</p>')
        
        # Abstract/Description
        description = metadata.get("basic", {}).get("description")
        if description:
            html_parts.append('<div class="abstract">')
            html_parts.append('<h2>Abstract</h2>')
            html_parts.append(f'<p>{html.escape(description)}</p>')
            html_parts.append('</div>')
        
        # Biological Context (if significant)
        if data.get("has_biological_context"):
            html_parts.append('<div class="section">')
            html_parts.append('<h2>Biological System</h2>')
            html_parts.append(self._format_biological_context(metadata.get("biological_context", {})))
            html_parts.append('</div>')
        
        # Model Information
        html_parts.append('<div class="section">')
        html_parts.append('<h2>Model Information</h2>')
        html_parts.append(self._format_basic_info(metadata.get("basic", {}), compact=True))
        html_parts.append('</div>')
        
        # References (essential for publications)
        if data.get("has_references"):
            html_parts.append('<div class="section">')
            html_parts.append('<h2>References</h2>')
            html_parts.append(self._format_references(metadata.get("references", {})))
            html_parts.append('</div>')
        
        html_parts.extend(['</div>', '</body>', '</html>'])
        
        return "\n".join(html_parts)
    
    def _generate_summary_html(self, data: Dict[str, Any]) -> str:
        """Generate a brief summary sheet in HTML.
        
        Args:
            data: Document data dictionary
            
        Returns:
            Complete HTML document as string
        """
        metadata = data["metadata"]
        
        html_parts = [
            self._get_html_header("Model Summary", include_summary_css=True),
            "<body>",
            '<div class="container summary">',
        ]
        
        # Title
        model_name = html.escape(metadata.get("basic", {}).get("model_name", "Untitled Model"))
        html_parts.append(f'<h1>{model_name}</h1>')
        
        # Quick facts table
        html_parts.append('<table class="summary-table">')
        
        # Model type
        model_type = metadata.get("basic", {}).get("version")
        if model_type:
            html_parts.append(f'<tr><th>Version</th><td>{html.escape(model_type)}</td></tr>')
        
        # Organism
        organism = metadata.get("biological_context", {}).get("organism")
        if organism:
            html_parts.append(f'<tr><th>Organism</th><td>{html.escape(organism)}</td></tr>')
        
        # Primary author and contributors
        authorship = metadata.get("authorship", {})
        primary_author = authorship.get("primary_author")
        contributors = authorship.get("contributors", [])
        if primary_author:
            author_str = primary_author
            if contributors:
                author_str += " et al."
            html_parts.append(f'<tr><th>Authors</th><td>{html.escape(author_str)}</td></tr>')
        
        # Date
        creation_date = authorship.get("created_date")
        if creation_date:
            formatted_date = self.format_date(creation_date)
            html_parts.append(f'<tr><th>Created</th><td>{formatted_date}</td></tr>')
        
        html_parts.append('</table>')
        
        # Description
        description = metadata.get("basic", {}).get("description")
        if description:
            html_parts.append(f'<p class="description">{html.escape(description)}</p>')
        
        html_parts.extend(['</div>', '</body>', '</html>'])
        
        return "\n".join(html_parts)
    
    def _get_html_header(self, title: str, 
                        include_technical_css: bool = False,
                        include_publication_css: bool = False,
                        include_summary_css: bool = False) -> str:
        """Generate HTML header with embedded CSS.
        
        Args:
            title: Document title
            include_technical_css: Include technical report styles
            include_publication_css: Include publication styles
            include_summary_css: Include summary styles
            
        Returns:
            HTML header string
        """
        css = self._get_base_css()
        
        if include_technical_css:
            css += self._get_technical_css()
        if include_publication_css:
            css += self._get_publication_css()
        if include_summary_css:
            css += self._get_summary_css()
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
    <style>
{css}
    </style>
</head>"""
    
    def _get_base_css(self) -> str:
        """Get base CSS styles common to all document types."""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 { color: #2c3e50; margin-bottom: 15px; }
        h1 { font-size: 2.5em; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
        h2 { font-size: 1.8em; margin-top: 30px; border-bottom: 2px solid #ecf0f1; padding-bottom: 8px; }
        h3 { font-size: 1.3em; margin-top: 20px; }
        .section { margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin: 15px 0; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ecf0f1; }
        th { background: #f8f9fa; font-weight: 600; width: 200px; }
        table.data-table { font-size: 0.9em; }
        table.data-table th { width: auto; background: #3498db; color: white; }
        table.data-table td { padding: 8px; }
        table.compact-table { font-size: 9pt; border: 1px solid #ddd; table-layout: auto; width: 100%; max-width: 100%; }
        table.compact-table th { padding: 4px 6px; background: #34495e; color: white; font-size: 9pt; line-height: 1.2; word-wrap: break-word; }
        table.compact-table td { padding: 3px 6px; line-height: 1.2; font-size: 9pt; word-wrap: break-word; overflow-wrap: break-word; max-width: 120px; }
        table.compact-table tr:nth-child(even) { background-color: #f9f9f9; }
        table.extra-compact-table { font-size: 7pt; border-collapse: collapse; table-layout: auto; width: 100%; max-width: 100%; border: none; }
        table.extra-compact-table th { padding: 2px 3px; background: #34495e; color: white; font-size: 7pt; line-height: 1.1; word-wrap: break-word; border: none; }
        table.extra-compact-table td { padding: 2px 3px; line-height: 1.1; font-size: 7pt; word-wrap: break-word; overflow-wrap: break-word; max-width: 80px; border: none; }
        table.extra-compact-table tr:nth-child(even) { background-color: #f9f9f9; }
        table.extra-compact-table tr { border: none; }
        .summary-box { background: #e8f4f8; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0; }
        .summary-box h3 { margin-top: 0; color: #2980b9; }
        ul { margin-left: 20px; margin-top: 10px; }
        ul.warnings { color: #e74c3c; }
        li { margin-bottom: 5px; }
        .generation-date { color: #7f8c8d; font-style: italic; margin-bottom: 30px; }
"""
    
    def _get_technical_css(self) -> str:
        """Get CSS specific to technical reports."""
        return """
        .title { color: #2980b9; }
        .subtitle { font-size: 1.3em; color: #7f8c8d; margin-bottom: 5px; }
        .info-grid { display: grid; grid-template-columns: 200px 1fr; gap: 10px; margin: 15px 0; }
        .info-label { font-weight: 600; color: #555; }
"""
    
    def _get_publication_css(self) -> str:
        """Get CSS specific to publication documents."""
        return """
        .publication .title { text-align: center; font-size: 2.2em; margin-bottom: 20px; }
        .authors { text-align: center; font-size: 1.1em; margin-bottom: 30px; color: #555; }
        .abstract { 
            background: #f8f9fa; 
            padding: 20px; 
            border-left: 4px solid #3498db; 
            margin: 30px 0; 
        }
        .abstract h2 { margin-top: 0; font-size: 1.3em; }
"""
    
    def _get_summary_css(self) -> str:
        """Get CSS specific to summary sheets."""
        return """
        .summary h1 { text-align: center; color: #2c3e50; margin-bottom: 30px; }
        .summary-table { margin: 20px 0; }
        .summary-table th { background: #3498db; color: white; }
        .description { 
            margin-top: 30px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 5px; 
        }
"""
    
    def _format_basic_info(self, basic: Dict[str, Any], compact: bool = False) -> str:
        """Format basic information section."""
        html_parts = ['<table class="compact-table">']
        
        fields = [
            ("Name", basic.get("model_name")),
            ("Model ID", basic.get("model_id")),
            ("Version", basic.get("version")),
        ]
        
        if not compact:
            fields.append(("Description", basic.get("description")))
            fields.append(("Keywords", ", ".join(basic.get("keywords", [])) if basic.get("keywords") else None))
        
        for label, value in fields:
            if value:
                html_parts.append(f'<tr><th>{label}</th><td>{html.escape(str(value))}</td></tr>')
        
        html_parts.append('</table>')
        return "\n".join(html_parts)
    
    def _format_authorship(self, authorship: Dict[str, Any]) -> str:
        """Format authorship section."""
        html_parts = ['<table class="compact-table">']
        
        primary = authorship.get("primary_author")
        if primary:
            html_parts.append(f'<tr><th>Primary Author</th><td>{html.escape(primary)}</td></tr>')
        
        contributors = authorship.get("contributors", [])
        if contributors:
            contrib_list = "<ul>"
            for contrib in contributors:
                contrib_list += f"<li>{html.escape(contrib)}</li>"
            contrib_list += "</ul>"
            html_parts.append(f'<tr><th>Contributors</th><td>{contrib_list}</td></tr>')
        
        institution = authorship.get("institution")
        if institution:
            html_parts.append(f'<tr><th>Institution</th><td>{html.escape(institution)}</td></tr>')
        
        department = authorship.get("department")
        if department:
            html_parts.append(f'<tr><th>Department</th><td>{html.escape(department)}</td></tr>')
        
        email = authorship.get("contact_email")
        if email:
            html_parts.append(f'<tr><th>Contact</th><td>{html.escape(email)}</td></tr>')
        
        # Get dates from system section since they moved there
        created_date = authorship.get("created_date")
        if created_date:
            html_parts.append(f'<tr><th>Created</th><td>{self.format_date(created_date)}</td></tr>')
        
        modified_date = authorship.get("last_modified")
        if modified_date:
            html_parts.append(f'<tr><th>Last Modified</th><td>{self.format_date(modified_date)}</td></tr>')
        
        html_parts.append('</table>')
        return "\n".join(html_parts)
    
    def _format_biological_context(self, bio_context: Dict[str, Any]) -> str:
        """Format biological context section."""
        html_parts = ['<table class="compact-table">']
        
        fields = [
            ("Organism", bio_context.get("organism")),
            ("Tissue", bio_context.get("tissue")),
            ("Cell Type", bio_context.get("cell_type")),
            ("Pathway Names", ", ".join(bio_context.get("pathway_names", [])) if bio_context.get("pathway_names") else None),
            ("GO Terms", ", ".join(bio_context.get("go_terms", [])) if bio_context.get("go_terms") else None),
        ]
        
        for label, value in fields:
            if value:
                html_parts.append(f'<tr><th>{label}</th><td>{html.escape(str(value))}</td></tr>')
        
        html_parts.append('</table>')
        return "\n".join(html_parts)
    
    def _format_provenance(self, provenance: Dict[str, Any]) -> str:
        """Format provenance section."""
        html_parts = ['<table class="compact-table">']
        
        fields = [
            ("Source Database", provenance.get("source_database")),
            ("Database ID", provenance.get("database_id")),
            ("Original Format", provenance.get("original_format")),
            ("Import Date", self.format_date(provenance.get("import_date"))),
        ]
        
        for label, value in fields:
            if value:
                html_parts.append(f'<tr><th>{label}</th><td>{html.escape(str(value))}</td></tr>')
        
        html_parts.append('</table>')
        return "\n".join(html_parts)
    
    def _format_references(self, references: Dict[str, Any]) -> str:
        """Format references section."""
        publications = references.get("publications", [])
        if not publications:
            return "<p>No references available.</p>"
        
        html_parts = ['<ol>']
        for pub in publications:
            # Publications are stored as DOI/PubMed ID strings
            if isinstance(pub, str):
                ref_str = html.escape(pub)
                # If it looks like a DOI, make it a link
                if pub.startswith("10."):
                    ref_str = f'<a href="https://doi.org/{html.escape(pub)}">{html.escape(pub)}</a>'
                html_parts.append(f'<li>{ref_str}</li>')
            else:
                # Legacy format: dict with citation/doi/pubmed
                citation = html.escape(pub.get("citation", "Unknown"))
                doi = pub.get("doi", "")
                pubmed = pub.get("pubmed_id", "")
                
                ref_str = citation
                if doi:
                    ref_str += f' DOI: <a href="https://doi.org/{html.escape(doi)}">{html.escape(doi)}</a>'
                if pubmed:
                    ref_str += f' PMID: <a href="https://pubmed.ncbi.nlm.nih.gov/{html.escape(pubmed)}/">{html.escape(pubmed)}</a>'
                
                html_parts.append(f'<li>{ref_str}</li>')
        html_parts.append('</ol>')
        
        return "\n".join(html_parts)
    
    def _format_system_info(self, system: Dict[str, Any]) -> str:
        """Format system information section."""
        html_parts = ['<table class="compact-table">']
        
        fields = [
            ("File Format Version", system.get("file_format_version")),
            ("Software Version", system.get("shypn_version")),
        ]
        
        for label, value in fields:
            if value:
                html_parts.append(f'<tr><th>{label}</th><td>{html.escape(str(value))}</td></tr>')
        
        html_parts.append('</table>')
        return "\n".join(html_parts)
    
    def _format_summary_section(self, report_data: Dict[str, Any]) -> str:
        """Format summary section from report panel data.
        
        Args:
            report_data: Dict containing model, dynamic, topology, provenance data
            
        Returns:
            HTML string with summary information
        """
        html_parts = ['<div class="summary-box">']
        html_parts.append('<h3>📊 Executive Summary</h3>')
        
        # Model structure summary
        model_data = report_data.get('model', {})
        if model_data and model_data.get('has_data'):
            structure = model_data.get('structure', {})
            html_parts.append(f'<p><strong>Model Structure:</strong> ')
            html_parts.append(f'{structure.get("places_count", 0)} species, ')
            html_parts.append(f'{structure.get("transitions_count", 0)} reactions, ')
            html_parts.append(f'{structure.get("arcs_count", 0)} connections</p>')
        
        # Topology summary
        topology_data = report_data.get('topology', {})
        if topology_data and topology_data.get('has_data'):
            stats = topology_data.get('statistics', {})
            html_parts.append(f'<p><strong>Topology Analysis:</strong> ')
            html_parts.append(f'{stats.get("p_invariants", 0)} P-invariants, ')
            html_parts.append(f'{stats.get("t_invariants", 0)} T-invariants, ')
            status = topology_data.get('status', 'analyzed')
            html_parts.append(f'Status: {html.escape(status)}</p>')
        
        # Dynamic summary
        dynamic_data = report_data.get('dynamic', {})
        if dynamic_data and dynamic_data.get('has_data'):
            sim_data = dynamic_data.get('simulation_data', {})
            species_count = len(sim_data.get('species', []))
            reactions_count = len(sim_data.get('reactions', []))
            if species_count > 0 or reactions_count > 0:
                html_parts.append(f'<p><strong>Simulation Data:</strong> ')
                if species_count > 0:
                    html_parts.append(f'{species_count} species tracked')
                if reactions_count > 0:
                    if species_count > 0:
                        html_parts.append(', ')
                    html_parts.append(f'{reactions_count} reactions analyzed')
                html_parts.append('</p>')
        
        # Provenance summary
        provenance_data = report_data.get('provenance', {})
        if provenance_data and provenance_data.get('has_data'):
            summary = provenance_data.get('summary', {})
            total = summary.get('total', 0)
            if total > 0:
                html_parts.append(f'<p><strong>Data Sources:</strong> {total} pathway(s) imported</p>')
        
        html_parts.append('</div>')
        return "\n".join(html_parts)

    def _format_model_structure(self, model_data: Dict[str, Any]) -> str:
        """Format model structure section with species and reactions."""
        html_parts = []
        
        # Overview
        overview = model_data.get('overview', {})
        if overview:
            html_parts.append('<h3>Overview</h3>')
            html_parts.append('<table class="compact-table">')
            if overview.get('name'):
                html_parts.append(f'<tr><th>Model Name</th><td>{html.escape(overview["name"])}</td></tr>')
            if overview.get('description'):
                html_parts.append(f'<tr><th>Description</th><td>{html.escape(overview["description"])}</td></tr>')
            html_parts.append('</table>')
        
        # Structure counts
        structure = model_data.get('structure', {})
        if structure:
            html_parts.append('<h3>Structure</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append(f'<tr><th>Species (Places)</th><td>{structure.get("places_count", 0)}</td></tr>')
            html_parts.append(f'<tr><th>Reactions (Transitions)</th><td>{structure.get("transitions_count", 0)}</td></tr>')
            html_parts.append(f'<tr><th>Connections (Arcs)</th><td>{structure.get("arcs_count", 0)}</td></tr>')
            html_parts.append('</table>')
        
        # Species table (Compact format)
        species = model_data.get('species', [])
        if species:
            html_parts.append('<h3>Species</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>ID</th><th>Name</th><th>Initial Tokens</th><th>Units</th><th>Mass</th><th>Conservation</th></tr>')
            for sp in species:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(sp.get("id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("initial_tokens", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("units", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("mass", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("conservation", "")))}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        # Reactions table (Compact format)
        reactions = model_data.get('reactions', [])
        if reactions:
            html_parts.append('<h3>Reactions</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>ID</th><th>Name</th><th>Type</th><th>EC Number</th><th>Vmax</th><th>Km</th><th>Kcat</th><th>Ki</th><th>Rate Function</th><th>Reversible</th></tr>')
            for rxn in reactions:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("type", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("ec_number", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("vmax", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("km", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("kcat", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("ki", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("rate_function", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("reversible", "")))}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        return "\n".join(html_parts) if html_parts else "<p>No model structure data available.</p>"
    
    def _format_topology_analyses(self, topology_data: Dict[str, Any]) -> str:
        """Format topology analyses section with compact tabular display."""
        html_parts = []
        
        # Status
        status = topology_data.get('status', 'No analysis')
        html_parts.append(f'<p><strong>Status:</strong> {html.escape(status)}</p>')
        
        # Key Findings in Compact Table Format
        findings = topology_data.get('key_findings', [])
        if findings:
            html_parts.append('<h3>Key Findings</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>Finding</th></tr>')
            for finding in findings:
                html_parts.append(f'<tr><td>{html.escape(finding)}</td></tr>')
            html_parts.append('</table>')
        
        # Analysis sections grouped in tabular form
        sections = topology_data.get('sections', {})
        if sections:
            html_parts.append('<h3>Topological Analyses</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>Category</th><th>Metric</th><th>Value</th></tr>')
            
            for section_name, section_data in sections.items():
                if section_data:
                    category_label = section_name.replace('_', ' ').title()
                    first_row = True
                    for key, value in section_data.items():
                        html_parts.append('<tr>')
                        if first_row:
                            html_parts.append(f'<td rowspan="{len(section_data)}"><strong>{html.escape(category_label)}</strong></td>')
                            first_row = False
                        label = key.replace('_', ' ').title()
                        html_parts.append(f'<td>{html.escape(label)}</td>')
                        html_parts.append(f'<td>{html.escape(str(value))}</td>')
                        html_parts.append('</tr>')
            
            html_parts.append('</table>')
        
        # Warnings (if any)
        warnings = topology_data.get('warnings', [])
        if warnings:
            html_parts.append('<h3>Warnings</h3>')
            html_parts.append('<ul class="warnings">')
            for warning in warnings:
                html_parts.append(f'<li>{html.escape(warning)}</li>')
            html_parts.append('</ul>')
        
        return "\n".join(html_parts) if html_parts else "<p>No topology analysis data available.</p>"
    
    def _format_dynamic_analyses(self, dynamic_data: Dict[str, Any]) -> str:
        """Format dynamic analyses section with compact simulation data tables."""
        html_parts = []
        
        # Simulation Parameters Summary (NEW - appears first)
        sim_params = dynamic_data.get('simulation_parameters', {})
        if sim_params:
            html_parts.append('<h3>Simulation Parameters</h3>')
            html_parts.append('<table class="compact-table">')
            
            # Timestamp
            timestamp = sim_params.get('timestamp')
            if timestamp:
                html_parts.append(f'<tr><th>Date/Time</th><td>{html.escape(str(timestamp))}</td></tr>')
            
            # Time parameters
            time_step = sim_params.get('time_step')
            if time_step is not None:
                html_parts.append(f'<tr><th>Time Step (dt)</th><td>{time_step:.4f} s</td></tr>')
            else:
                html_parts.append(f'<tr><th>Time Step (dt)</th><td>Not set</td></tr>')
            
            target_duration = sim_params.get('target_duration')
            if target_duration is not None:
                html_parts.append(f'<tr><th>Target Duration</th><td>{target_duration:.2f} s</td></tr>')
            else:
                html_parts.append(f'<tr><th>Target Duration</th><td>Not set</td></tr>')
            
            actual_duration = sim_params.get('actual_duration', 0)
            html_parts.append(f'<tr><th>Actual Duration</th><td>{actual_duration:.2f} s</td></tr>')
            
            time_scale = sim_params.get('time_scale', 1.0)
            html_parts.append(f'<tr><th>Time Scale</th><td>{time_scale:.1f}x</td></tr>')
            
            total_steps = sim_params.get('total_steps', 0)
            html_parts.append(f'<tr><th>Total Steps</th><td>{total_steps}</td></tr>')
            
            # Activity statistics
            num_time_points = sim_params.get('num_time_points', 0)
            html_parts.append(f'<tr><th>Time Points Recorded</th><td>{num_time_points}</td></tr>')
            
            total_firings = sim_params.get('total_firings', 0)
            html_parts.append(f'<tr><th>Total Transition Firings</th><td>{total_firings}</td></tr>')
            
            avg_rate = sim_params.get('avg_firing_rate', 0)
            html_parts.append(f'<tr><th>Average Firing Rate</th><td>{avg_rate:.2f} firings/s</td></tr>')
            
            html_parts.append('</table>')
        
        # Model info
        model_info = dynamic_data.get('model_info', {})
        if model_info:
            html_parts.append('<h3>Model Information</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append(f'<tr><th>Number of Species</th><td>{model_info.get("num_places", 0)}</td></tr>')
            html_parts.append(f'<tr><th>Number of Reactions</th><td>{model_info.get("num_transitions", 0)}</td></tr>')
            html_parts.append('</table>')
        
        # Organisms
        organisms = dynamic_data.get('organisms', [])
        if organisms:
            html_parts.append('<h3>Organisms</h3>')
            html_parts.append('<ul>')
            for org in organisms:
                html_parts.append(f'<li>{html.escape(org)}</li>')
            html_parts.append('</ul>')
        
        # Enrichments
        enrichments_count = dynamic_data.get('enrichments_count', 0)
        if enrichments_count > 0:
            html_parts.append(f'<p><strong>Enrichments:</strong> {enrichments_count} parameter(s) enriched</p>')
        
        # Simulation data - Species Concentration Table (Compact)
        simulation = dynamic_data.get('simulation_data', {})
        species_sim = simulation.get('species', [])
        
        if species_sim:
            html_parts.append('<h3>Species Concentration</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>Name</th><th>ID</th><th>Initial</th><th>Final</th><th>Min</th><th>Max</th><th>Avg</th></tr>')
            for sp in species_sim:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(sp.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("initial", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("final", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("min", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("max", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(sp.get("avg", "")))}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        # Reaction Activity Table (Compact)
        reactions_sim = simulation.get('reactions', [])
        if reactions_sim:
            html_parts.append('<h3>Reaction Activity</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>Name</th><th>ID</th><th>Avg Rate</th><th>Total Firings</th><th>Status</th></tr>')
            for rxn in reactions_sim:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("avg_rate", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("total_firings", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("status", "")))}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        # Reaction Selected Table (Extra Compact) - Locality simulation data
        reactions_selected = simulation.get('reactions_selected', [])
        if reactions_selected:
            html_parts.append('<h3>Reaction Selected</h3>')
            html_parts.append('<table class="extra-compact-table">')
            html_parts.append('<tr><th>Component</th><th>ID</th><th>Name</th><th>Initial</th><th>Final</th><th>Min</th><th>Max</th><th>Avg</th><th>Info</th></tr>')
            for rxn in reactions_selected:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("component", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("initial", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("final", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("min", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("max", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("average", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(rxn.get("info", "")))}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        return "\n".join(html_parts) if html_parts else "<p>No dynamic analysis data available.</p>"
    
    def _format_provenance_data(self, provenance_data: Dict[str, Any]) -> str:
        """Format provenance data section with pathways information."""
        html_parts = []
        
        # Summary
        summary = provenance_data.get('summary', {})
        if summary:
            html_parts.append('<h3>Summary</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append(f'<tr><th>Total Pathways</th><td>{summary.get("total", 0)}</td></tr>')
            html_parts.append(f'<tr><th>KEGG Pathways</th><td>{summary.get("kegg", 0)}</td></tr>')
            html_parts.append(f'<tr><th>SBML Models</th><td>{summary.get("sbml", 0)}</td></tr>')
            html_parts.append(f'<tr><th>Converted</th><td>{summary.get("converted", 0)}</td></tr>')
            html_parts.append(f'<tr><th>Enriched</th><td>{summary.get("enriched", 0)}</td></tr>')
            html_parts.append('</table>')
        
        # Pathways table (Compact format)
        pathways = provenance_data.get('pathways', [])
        if pathways:
            html_parts.append('<h3>Pathways</h3>')
            html_parts.append('<table class="compact-table">')
            html_parts.append('<tr><th>Name</th><th>Source</th><th>Source ID</th><th>Organism</th><th>Import Date</th><th>Enrichments</th></tr>')
            for pathway in pathways:
                html_parts.append('<tr>')
                html_parts.append(f'<td>{html.escape(str(pathway.get("name", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(pathway.get("source_type", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(pathway.get("source_id", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(pathway.get("organism", "")))}</td>')
                html_parts.append(f'<td>{html.escape(str(pathway.get("import_date", "")))}</td>')
                html_parts.append(f'<td>{pathway.get("enrichments_count", 0)}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
        
        return "\n".join(html_parts) if html_parts else "<p>No provenance data available.</p>"
