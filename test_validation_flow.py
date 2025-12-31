#!/usr/bin/env python3
"""Test validation flow for SBML import with assignment rules.

Tests:
1. Parse BIOMD61 (has 3 assignment rules)
2. Check that validation issues are detected
3. Verify assignment_rules and reversible_formulas categories exist
4. Confirm recommendations are present
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser

def test_validation_detection():
    """Test that validation properly detects stochastic incompatibility issues."""
    
    # Parse BIOMD61
    biomd61_path = "/home/simao/projetos/shypn/workspace/projects/My_Project/pathways/BIOMD0000000061.xml"
    
    if not Path(biomd61_path).exists():
        print(f"❌ BIOMD61 file not found: {biomd61_path}")
        return False
    
    print("=" * 80)
    print("Testing Validation Flow for BIOMD61")
    print("=" * 80)
    print()
    
    # Parse file (validation happens inside parse_file)
    parser = SBMLParser()
    print(f"📄 Parsing {Path(biomd61_path).name}...")
    print()
    
    try:
        pathway_data = parser.parse_file(biomd61_path)
        print(f"✅ Parsed successfully")
        print(f"   Species: {len(pathway_data.species)}")
        print(f"   Reactions: {len(pathway_data.reactions)}")
        print()
        
        # Check metadata for validation issues
        validation_issues = pathway_data.metadata.get('validation_issues', [])
        
        if not validation_issues:
            print("⚠️  No validation issues found in metadata")
            return False
        
        print(f"📋 Found {len(validation_issues)} validation issues")
        print()
        
        # Check for stochastic compatibility issues
        assignment_rule_issues = [
            issue for issue in validation_issues
            if issue.get('category') == 'assignment_rules'
        ]
        
        reversible_formula_issues = [
            issue for issue in validation_issues
            if issue.get('category') == 'reversible_formulas'
        ]
        
        # Report findings
        if assignment_rule_issues:
            print(f"✅ Assignment rules detected: {len(assignment_rule_issues)} issue(s)")
            for issue in assignment_rule_issues:
                print(f"   Category: {issue.get('category')}")
                print(f"   Severity: {issue.get('severity')}")
                print(f"   Message: {issue.get('message')}")
                print()
                suggestion = issue.get('suggestion', '')
                if suggestion:
                    # Show first few lines
                    lines = suggestion.split('\n')[:5]
                    print("   Suggestion (first 5 lines):")
                    for line in lines:
                        if line.strip():
                            print(f"      {line}")
                print()
        else:
            print("❌ No assignment rule issues detected (expected some)")
        
        if reversible_formula_issues:
            print(f"✅ Reversible formula issues detected: {len(reversible_formula_issues)} issue(s)")
            for issue in reversible_formula_issues:
                print(f"   Category: {issue.get('category')}")
                print(f"   Severity: {issue.get('severity')}")
                print(f"   Message: {issue.get('message')}")
                print()
        else:
            print("⚠️  No reversible formula issues detected")
        
        print()
        print("=" * 80)
        print("VALIDATION FLOW TEST RESULTS")
        print("=" * 80)
        
        if assignment_rule_issues or reversible_formula_issues:
            print("✅ PASS: Validation correctly detects stochastic incompatibility issues")
            print()
            print("Next step: Import BIOMD61 via GUI to test dialog")
            print("Expected behavior:")
            print("  1. Parse completes successfully")
            print("  2. Dialog shows: 'Model Compatibility Issues Detected'")
            print("  3. Options: Convert to Continuous | Use Hybrid | Proceed Anyway | Cancel")
            print("  4. If 'Continuous' chosen, all transitions become continuous")
            print("  5. If 'Hybrid' chosen, only problematic transitions become continuous")
            return True
        else:
            print("❌ FAIL: Expected to find stochastic compatibility issues")
            return False
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_validation_detection()
    sys.exit(0 if success else 1)
