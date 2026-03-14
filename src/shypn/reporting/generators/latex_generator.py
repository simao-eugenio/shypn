"""LaTeX document generator for scientific publication-ready reports."""

from pathlib import Path
from typing import Dict, Any

from .base_generator import BaseDocumentGenerator, DocumentType


class LaTeXGenerator(BaseDocumentGenerator):
    """Generator for LaTeX documents with professional typesetting.
    
    Creates publication-ready LaTeX documents that can be compiled
    to PDF using pdflatex, xelatex, or lualatex.
    """
    
    def get_file_extension(self) -> str:
        """Get the file extension for LaTeX files."""
        return ".tex"
    
    def _generate_impl(self,
                       output_path: Path,
                       document_data: Dict[str, Any],
                       document_type: DocumentType) -> None:
        """Generate a LaTeX document.
        
        Args:
            output_path: Where to save the LaTeX file
            document_data: All data for the document
            document_type: Type of document to generate
        """
        metadata = document_data["metadata"]
        
        # Generate LaTeX content
        latex_content = self._generate_technical_latex(document_data)
        
        # Write to file
        output_path.write_text(latex_content, encoding='utf-8')
    
    def _generate_technical_latex(self, data: Dict[str, Any]) -> str:
        """Generate a comprehensive technical report in LaTeX.
        
        Args:
            data: Document data dictionary
            
        Returns:
            Complete LaTeX document as string
        """
        metadata = data["metadata"]
        generation_date = self.format_date(data.get("generation_date"))
        
        # Build LaTeX document
        latex_parts = [
            self._get_latex_preamble(),
            "\\begin{document}\n",
        ]
        
        # Title page
        model_name = self._escape_latex(metadata.get("basic", {}).get("model_name", "Untitled Model"))
        latex_parts.append(f"\\title{{{model_name}}}")
        
        # Authors
        authorship = metadata.get("authorship", {})
        primary_author = authorship.get("primary_author")
        if primary_author:
            latex_parts.append(f"\\author{{{self._escape_latex(primary_author)}}}")
        
        latex_parts.append(f"\\date{{Generated: {generation_date}}}")
        latex_parts.append("\\maketitle\n")
        latex_parts.append("\\tableofcontents\n")
        latex_parts.append("\\clearpage\n")
        
        # Executive Summary
        report_data = data.get("additional", {}).get("report_data", {})
        if report_data:
            latex_parts.append("\\section{Executive Summary}\n")
            latex_parts.append(self._format_summary_section(report_data))
            latex_parts.append("\n")
        
        # Basic Information
        latex_parts.append("\\section{Basic Information}\n")
        latex_parts.append(self._format_basic_info(metadata.get("basic", {})))
        latex_parts.append("\n")
        
        # Authorship
        if data.get("has_authors"):
            latex_parts.append("\\section{Authorship}\n")
            latex_parts.append(self._format_authorship(metadata.get("authorship", {})))
            latex_parts.append("\n")
        
        # Biological Context
        if data.get("has_biological_context"):
            latex_parts.append("\\section{Biological Context}\n")
            latex_parts.append(self._format_biological_context(metadata.get("biological_context", {})))
            latex_parts.append("\n")
        
        # Model Structure
        if report_data and 'model' in report_data and report_data['model'].get('has_data'):
            latex_parts.append("\\section{Model Structure}\n")
            latex_parts.append(self._format_model_structure(report_data['model']))
            latex_parts.append("\n")
        
        # Dynamic Analyses
        if report_data and 'dynamic' in report_data and report_data['dynamic'].get('has_data'):
            latex_parts.append("\\section{Dynamic Analyses}\n")
            latex_parts.append(self._format_dynamic_analyses(report_data['dynamic']))
            latex_parts.append("\n")
        
        # Topology Analyses
        if report_data and 'topology' in report_data and report_data['topology'].get('has_data'):
            latex_parts.append("\\section{Topology Analyses}\n")
            latex_parts.append(self._format_topology_analyses(report_data['topology']))
            latex_parts.append("\n")
        
        # Data Provenance
        if report_data and 'provenance' in report_data and report_data['provenance'].get('has_data'):
            latex_parts.append("\\section{Data Provenance}\n")
            latex_parts.append(self._format_provenance_data(report_data['provenance']))
            latex_parts.append("\n")
        
        # References
        if data.get("has_references"):
            latex_parts.append("\\section{References}\n")
            latex_parts.append(self._format_references(metadata.get("references", {})))
            latex_parts.append("\n")
        
        latex_parts.append("\\end{document}\n")
        
        return "".join(latex_parts)
    
    def _get_latex_preamble(self) -> str:
        """Get LaTeX document preamble with packages and settings."""
        return r"""% Generated by SHYpn - Systems Biology Hybrid Petri Net Tool
\documentclass[11pt,a4paper]{article}

% Packages
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{longtable}
\usepackage{booktabs}
\usepackage{array}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{fancyhdr}

% Hyperref setup
\hypersetup{
    colorlinks=true,
    linkcolor=blue,
    urlcolor=blue,
    citecolor=blue
}

% Page style
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\leftmark}
\fancyfoot[C]{\thepage}

% Custom colors
\definecolor{headerblue}{RGB}{52, 152, 219}
\definecolor{lightgray}{RGB}{248, 249, 250}

"""
    
    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters.
        
        Args:
            text: Text to escape
            
        Returns:
            LaTeX-safe text
        """
        if not text:
            return ""
        
        # Replace special LaTeX characters
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
        }
        
        result = str(text)
        for char, replacement in replacements.items():
            result = result.replace(char, replacement)
        
        return result
    
    def _format_summary_section(self, report_data: Dict[str, Any]) -> str:
        """Format executive summary section."""
        latex_parts = []
        
        # Model structure summary
        model_data = report_data.get('model', {})
        if model_data and model_data.get('has_data'):
            structure = model_data.get('structure', {})
            latex_parts.append("\\textbf{Model Structure:} ")
            latex_parts.append(f"{structure.get('places_count', 0)} species, ")
            latex_parts.append(f"{structure.get('transitions_count', 0)} reactions, ")
            latex_parts.append(f"{structure.get('arcs_count', 0)} connections\n\n")
        
        # Topology summary
        topology_data = report_data.get('topology', {})
        if topology_data and topology_data.get('has_data'):
            stats = topology_data.get('statistics', {})
            latex_parts.append("\\textbf{Topology Analysis:} ")
            latex_parts.append(f"{stats.get('p_invariants', 0)} P-invariants, ")
            latex_parts.append(f"{stats.get('t_invariants', 0)} T-invariants\n\n")
        
        # Dynamic summary
        dynamic_data = report_data.get('dynamic', {})
        if dynamic_data and dynamic_data.get('has_data'):
            sim_data = dynamic_data.get('simulation_data', {})
            species_count = len(sim_data.get('species', []))
            reactions_count = len(sim_data.get('reactions', []))
            if species_count > 0 or reactions_count > 0:
                latex_parts.append("\\textbf{Simulation Data:} ")
                if species_count > 0:
                    latex_parts.append(f"{species_count} species tracked")
                if reactions_count > 0:
                    if species_count > 0:
                        latex_parts.append(", ")
                    latex_parts.append(f"{reactions_count} reactions analyzed")
                latex_parts.append("\n\n")
        
        return "".join(latex_parts)
    
    def _format_basic_info(self, basic: Dict[str, Any]) -> str:
        """Format basic information section."""
        latex_parts = ["\\begin{description}\n"]
        
        fields = [
            ("Name", basic.get("model_name")),
            ("Model ID", basic.get("model_id")),
            ("Version", basic.get("version")),
            ("Description", basic.get("description")),
            ("Keywords", ", ".join(basic.get("keywords", [])) if basic.get("keywords") else None),
        ]
        
        for label, value in fields:
            if value:
                latex_parts.append(f"\\item[{label}:] {self._escape_latex(str(value))}\n")
        
        latex_parts.append("\\end{description}\n")
        return "".join(latex_parts)
    
    def _format_authorship(self, authorship: Dict[str, Any]) -> str:
        """Format authorship section."""
        latex_parts = ["\\begin{description}\n"]
        
        primary = authorship.get("primary_author")
        if primary:
            latex_parts.append(f"\\item[Primary Author:] {self._escape_latex(primary)}\n")
        
        contributors = authorship.get("contributors", [])
        if contributors:
            contrib_str = ", ".join([self._escape_latex(c) for c in contributors])
            latex_parts.append(f"\\item[Contributors:] {contrib_str}\n")
        
        institution = authorship.get("institution")
        if institution:
            latex_parts.append(f"\\item[Institution:] {self._escape_latex(institution)}\n")
        
        email = authorship.get("contact_email")
        if email:
            latex_parts.append(f"\\item[Contact:] \\href{{mailto:{email}}}{{{self._escape_latex(email)}}}\n")
        
        latex_parts.append("\\end{description}\n")
        return "".join(latex_parts)
    
    def _format_biological_context(self, bio_context: Dict[str, Any]) -> str:
        """Format biological context section."""
        latex_parts = ["\\begin{description}\n"]
        
        fields = [
            ("Organism", bio_context.get("organism")),
            ("Tissue", bio_context.get("tissue")),
            ("Cell Type", bio_context.get("cell_type")),
            ("Pathway Names", ", ".join(bio_context.get("pathway_names", [])) if bio_context.get("pathway_names") else None),
        ]
        
        for label, value in fields:
            if value:
                latex_parts.append(f"\\item[{label}:] {self._escape_latex(str(value))}\n")
        
        latex_parts.append("\\end{description}\n")
        return "".join(latex_parts)
    
    def _format_model_structure(self, model_data: Dict[str, Any]) -> str:
        """Format model structure section with species and reactions."""
        latex_parts = []
        
        # Structure counts
        structure = model_data.get('structure', {})
        if structure:
            latex_parts.append("\\subsection{Structure}\n")
            latex_parts.append("\\begin{description}\n")
            latex_parts.append(f"\\item[Species (Places):] {structure.get('places_count', 0)}\n")
            latex_parts.append(f"\\item[Reactions (Transitions):] {structure.get('transitions_count', 0)}\n")
            latex_parts.append(f"\\item[Connections (Arcs):] {structure.get('arcs_count', 0)}\n")
            latex_parts.append("\\end{description}\n\n")
        
        # Species table (compact, first 20 entries)
        species = model_data.get('species', [])
        if species:
            latex_parts.append("\\subsection{Species}\n")
            latex_parts.append("\\begin{longtable}{llrll}\n")
            latex_parts.append("\\toprule\n")
            latex_parts.append("ID & Name & Initial & Units & Conservation \\\\\n")
            latex_parts.append("\\midrule\n")
            latex_parts.append("\\endhead\n")
            
            for sp in species[:20]:  # Limit to first 20 for LaTeX
                latex_parts.append(f"{self._escape_latex(str(sp.get('id', '')))} & ")
                latex_parts.append(f"{self._escape_latex(str(sp.get('name', '')))} & ")
                latex_parts.append(f"{self._escape_latex(str(sp.get('initial_tokens', '')))} & ")
                latex_parts.append(f"{self._escape_latex(str(sp.get('units', '')))} & ")
                latex_parts.append(f"{self._escape_latex(str(sp.get('conservation', '')))} \\\\\n")
            
            if len(species) > 20:
                latex_parts.append(f"\\multicolumn{{5}}{{l}}{{\\textit{{... {len(species) - 20} more species omitted}}}} \\\\\n")
            
            latex_parts.append("\\bottomrule\n")
            latex_parts.append("\\end{longtable}\n\n")
        
        return "".join(latex_parts)
    
    def _format_dynamic_analyses(self, dynamic_data: Dict[str, Any]) -> str:
        """Format dynamic analyses section."""
        latex_parts = []
        
        # Simulation Parameters
        sim_params = dynamic_data.get('simulation_parameters', {})
        if sim_params:
            latex_parts.append("\\subsection{Simulation Parameters}\n")
            latex_parts.append("\\begin{description}\n")
            
            if sim_params.get('time_step') is not None:
                latex_parts.append(f"\\item[Time Step:] {sim_params['time_step']:.4f} s\n")
            if sim_params.get('actual_duration') is not None:
                latex_parts.append(f"\\item[Duration:] {sim_params['actual_duration']:.2f} s\n")
            if sim_params.get('total_firings') is not None:
                latex_parts.append(f"\\item[Total Firings:] {sim_params['total_firings']}\n")
            
            latex_parts.append("\\end{description}\n\n")
        
        return "".join(latex_parts)
    
    def _format_topology_analyses(self, topology_data: Dict[str, Any]) -> str:
        """Format topology analyses section."""
        latex_parts = []
        
        # Status
        status = topology_data.get('status', 'No analysis')
        latex_parts.append(f"\\textbf{{Status:}} {self._escape_latex(status)}\n\n")
        
        # Key findings
        findings = topology_data.get('key_findings', [])
        if findings:
            latex_parts.append("\\subsection{Key Findings}\n")
            latex_parts.append("\\begin{enumerate}\n")
            for finding in findings:
                latex_parts.append(f"\\item {self._escape_latex(finding)}\n")
            latex_parts.append("\\end{enumerate}\n\n")
        
        return "".join(latex_parts)
    
    def _format_provenance_data(self, provenance_data: Dict[str, Any]) -> str:
        """Format provenance data section."""
        latex_parts = []
        
        # Summary
        summary = provenance_data.get('summary', {})
        if summary:
            latex_parts.append("\\subsection{Summary}\n")
            latex_parts.append("\\begin{description}\n")
            latex_parts.append(f"\\item[Total Pathways:] {summary.get('total', 0)}\n")
            latex_parts.append(f"\\item[KEGG Pathways:] {summary.get('kegg', 0)}\n")
            latex_parts.append(f"\\item[SBML Models:] {summary.get('sbml', 0)}\n")
            latex_parts.append("\\end{description}\n\n")
        
        return "".join(latex_parts)
    
    def _format_references(self, references: Dict[str, Any]) -> str:
        """Format references section."""
        publications = references.get("publications", [])
        if not publications:
            return "No references available.\n"
        
        latex_parts = ["\\begin{enumerate}\n"]
        for pub in publications:
            if isinstance(pub, str):
                # Simple string format (DOI or PubMed ID)
                if pub.startswith("10."):
                    latex_parts.append(f"\\item \\href{{https://doi.org/{pub}}}{{{self._escape_latex(pub)}}}\n")
                else:
                    latex_parts.append(f"\\item {self._escape_latex(pub)}\n")
            else:
                # Legacy dict format
                citation = self._escape_latex(pub.get("citation", "Unknown"))
                latex_parts.append(f"\\item {citation}\n")
        
        latex_parts.append("\\end{enumerate}\n")
        return "".join(latex_parts)
