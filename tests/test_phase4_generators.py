#!/usr/bin/env python3
"""Test Phase 4 document generation functionality.

Tests the complete document generation pipeline:
1. Creating metadata
2. Generating HTML documents
3. Generating PDF documents (if WeasyPrint available)
4. Generating Excel workbooks (if openpyxl available)

Run this to verify Phase 4 implementation.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from shypn.reporting import ModelMetadata, UserProfile
from shypn.reporting.generators import (
    HTMLGenerator, PDFGenerator, ExcelGenerator, DocumentType
)


def create_test_metadata() -> ModelMetadata:
    """Create sample metadata for testing."""
    metadata = ModelMetadata()
    
    # Basic info
    metadata.model_name = "Glycolysis Test Model"
    metadata.model_id = "TEST_GLY_001"
    metadata.version = "1.0"
    metadata.description = (
        "A simplified model of glycolysis pathway demonstrating "
        "the conversion of glucose to pyruvate through ten enzymatic steps."
    )
    metadata.keywords = ["glycolysis", "metabolism", "glucose", "test"]
    
    # Authorship
    metadata.primary_author = "Test Author"
    metadata.contributors = ["Contributor One", "Contributor Two"]
    metadata.institution = "Test University"
    metadata.department = "Systems Biology Department"
    metadata.contact_email = "test@example.com"
    
    # Biological context
    metadata.organism = "Homo sapiens"
    metadata.biological_system = "Glycolysis pathway"
    metadata.pathway_name = "Glycolysis"
    metadata.cell_type = "Hepatocyte"
    
    # Provenance
    metadata.import_source = "Manual"
    metadata.original_model_id = ""
    
    # References
    metadata.publications = [
        "10.1000/test.001",
        "10.1000/test.002"
    ]
    
    return metadata


def test_html_generation():
    """Test HTML document generation."""
    print("\n=== Testing HTML Generation ===")
    
    metadata = create_test_metadata()
    generator = HTMLGenerator(metadata)
    
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    # Test all three document types
    for doc_type in DocumentType:
        output_path = output_dir / f"test_{doc_type.value}.html"
        success = generator.generate(output_path, doc_type)
        
        if success and output_path.exists():
            size = output_path.stat().st_size
            print(f"✓ {doc_type.value.capitalize()} HTML: {output_path.name} ({size} bytes)")
        else:
            print(f"✗ Failed to generate {doc_type.value} HTML")
            return False
    
    return True


def test_pdf_generation():
    """Test PDF document generation."""
    print("\n=== Testing PDF Generation ===")
    
    try:
        metadata = create_test_metadata()
        generator = PDFGenerator(metadata)
        
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # Test technical report only (most comprehensive)
        output_path = output_dir / "test_technical.pdf"
        success = generator.generate(output_path, DocumentType.TECHNICAL)
        
        if success and output_path.exists():
            size = output_path.stat().st_size
            print(f"✓ Technical PDF: {output_path.name} ({size} bytes)")
            return True
        else:
            print(f"✗ Failed to generate PDF")
            return False
            
    except ImportError as e:
        print(f"⚠ PDF generation skipped: {e}")
        print("  Install with: pip install weasyprint")
        return True  # Not a failure, just missing dependency


def test_excel_generation():
    """Test Excel workbook generation."""
    print("\n=== Testing Excel Generation ===")
    
    try:
        metadata = create_test_metadata()
        generator = ExcelGenerator(metadata)
        
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        # Test all three document types
        for doc_type in DocumentType:
            output_path = output_dir / f"test_{doc_type.value}.xlsx"
            success = generator.generate(output_path, doc_type)
            
            if success and output_path.exists():
                size = output_path.stat().st_size
                print(f"✓ {doc_type.value.capitalize()} Excel: {output_path.name} ({size} bytes)")
            else:
                print(f"✗ Failed to generate {doc_type.value} Excel")
                return False
        
        return True
        
    except ImportError as e:
        print(f"⚠ Excel generation skipped: {e}")
        print("  Install with: pip install openpyxl")
        return True  # Not a failure, just missing dependency


def main():
    """Run all tests."""
    print("=" * 60)
    print("Phase 4 Document Generation Test")
    print("=" * 60)
    
    results = []
    
    # Test HTML (no dependencies)
    results.append(("HTML Generation", test_html_generation()))
    
    # Test PDF (requires WeasyPrint)
    results.append(("PDF Generation", test_pdf_generation()))
    
    # Test Excel (requires openpyxl)
    results.append(("Excel Generation", test_excel_generation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        output_dir = Path(__file__).parent / "test_output"
        print(f"\nGenerated files are in: {output_dir}")
        return 0
    else:
        print("\n✗ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
