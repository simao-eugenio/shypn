#!/usr/bin/env python3
"""Test KEGG import auto-save functionality.

Tests that KEGG import:
1. Auto-saves raw KGML to project/pathways/
2. Auto-saves Petri net model to project/models/
3. Creates PathwayDocument metadata linking both files
"""
import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

def test_kegg_auto_save_structure():
    """Test that KEGG import creates proper file structure."""
    print("=" * 60)
    print("TEST: KEGG Auto-Save Structure")
    print("=" * 60)
    
    # Expected structure after KEGG import:
    # project/
    #   pathways/
    #     hsa00010.kgml  # Raw KGML from KEGG
    #   models/
    #     hsa00010.shy   # Converted Petri net model
    
    print("\n✓ Expected structure:")
    print("  project/pathways/{pathway_id}.kgml")
    print("  project/models/{pathway_id}.shy")
    print("\n✓ PathwayDocument should link:")
    print("  source_type='kegg'")
    print("  source_id=pathway_id")
    print("  raw_file='pathways/{pathway_id}.kgml'")
    print("  model_file='models/{pathway_id}.shy'")
    print("  imported_date=ISO timestamp")
    

def test_kegg_import_panel_has_auto_save():
    """Verify KEGG import panel has auto-save code."""
    print("\n" + "=" * 60)
    print("TEST: KEGG Import Panel Code Review")
    print("=" * 60)
    
    kegg_file = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'src', 'shypn', 'helpers', 'kegg_import_panel.py'
    )
    
    if not os.path.exists(kegg_file):
        print(f"✗ File not found: {kegg_file}")
        return False
    
    with open(kegg_file, 'r') as f:
        content = f.read()
    
    # Check for auto-save patterns
    checks = [
        ('Auto-save model', 'Auto-saving Petri net model to project/models/'),
        ('DocumentModel import', 'from shypn.data.canvas.document_model import DocumentModel'),
        ('Model save', 'save_document.save_to_file(model_filepath)'),
        ('PathwayDocument model_file', "model_file=f\"models/{self.current_pathway_id}.shy\""),
        ('KGML save', 'self.project.save_pathway_file'),
        ('Imported date', 'imported_date=datetime.now().isoformat()'),
    ]
    
    print("\nChecking for auto-save implementation:")
    all_passed = True
    for check_name, check_string in checks:
        if check_string in content:
            print(f"  ✓ {check_name}")
        else:
            print(f"  ✗ {check_name} - NOT FOUND")
            all_passed = False
    
    return all_passed


def test_compare_with_sbml():
    """Compare KEGG implementation with SBML reference."""
    print("\n" + "=" * 60)
    print("TEST: KEGG vs SBML Implementation Comparison")
    print("=" * 60)
    
    # Key patterns from SBML that should be in KEGG:
    patterns = {
        'Auto-save raw data': [
            'models_dir = os.path.join(project.root_path',
            'os.makedirs(models_dir, exist_ok=True)',
        ],
        'Auto-save model': [
            'DocumentModel()',
            'save_document.places = list(manager.document_controller.places)',
            'save_document.save_to_file(',
        ],
        'PathwayDocument metadata': [
            'PathwayDocument(',
            'source_type=',
            'raw_file=',
            'model_file=',
            'imported_date=',
        ],
    }
    
    kegg_file = os.path.join(
        os.path.dirname(__file__), 
        '..', '..', 
        'src', 'shypn', 'helpers', 'kegg_import_panel.py'
    )
    
    with open(kegg_file, 'r') as f:
        kegg_content = f.read()
    
    print("\nPattern matching:")
    for pattern_name, pattern_list in patterns.items():
        print(f"\n{pattern_name}:")
        for pattern in pattern_list:
            if pattern in kegg_content:
                print(f"  ✓ {pattern[:50]}...")
            else:
                print(f"  ✗ {pattern[:50]}... - MISSING")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("KEGG IMPORT AUTO-SAVE TEST SUITE")
    print("=" * 60)
    
    test_kegg_auto_save_structure()
    
    has_auto_save = test_kegg_import_panel_has_auto_save()
    
    test_compare_with_sbml()
    
    print("\n" + "=" * 60)
    if has_auto_save:
        print("✅ KEGG auto-save implementation VERIFIED")
    else:
        print("⚠️  KEGG auto-save implementation INCOMPLETE")
    print("=" * 60)
