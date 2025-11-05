#!/usr/bin/env python3
"""Fix ID Naming Convention Issues in KEGG Model Files.

This script:
1. Scans .shy model files for ID convention violations
2. Fixes incorrect IDs (e.g., '41' → 'T41', '151' → 'P151')
3. Updates all arc references to use corrected IDs
4. Creates backups before modifying files

ID Conventions:
- Places: Must be "P<number>" (e.g., "P101", "P151")
- Transitions: Must be "T<number>" (e.g., "T3", "T41")
- Arcs: Must be "A<number>" (e.g., "A1", "A112")

Usage:
    python fix_id_naming_conventions.py <model_file.shy>
    python fix_id_naming_conventions.py --scan-all  # Scan all .shy files in workspace
"""

import json
import sys
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Set


class IDNamingFixer:
    """Fixes ID naming convention violations in .shy model files."""
    
    def __init__(self, filepath: str):
        """Initialize fixer with model file path.
        
        Args:
            filepath: Path to .shy model file
        """
        self.filepath = filepath
        self.model = None
        self.id_mappings = {}  # old_id -> new_id
        self.violations_found = 0
        self.arcs_updated = 0
        
    def load_model(self):
        """Load model from file."""
        with open(self.filepath, 'r') as f:
            self.model = json.load(f)
        print(f"✓ Loaded model from {self.filepath}")
        
    def analyze_violations(self) -> Dict[str, List[Tuple[str, str]]]:
        """Analyze model for ID naming violations.
        
        Returns:
            Dictionary with violation categories and (old_id, new_id) pairs
        """
        violations = {
            'places': [],
            'transitions': [],
            'arcs': []
        }
        
        # Check places
        for place in self.model.get('places', []):
            pid = place['id']
            if not pid.startswith('P'):
                if pid.isdigit():
                    new_id = f"P{pid}"
                    violations['places'].append((pid, new_id))
                else:
                    print(f"⚠️  Place ID '{pid}' has non-standard format")
        
        # Check transitions
        for transition in self.model.get('transitions', []):
            tid = transition['id']
            if not tid.startswith('T'):
                if tid.isdigit():
                    new_id = f"T{tid}"
                    violations['transitions'].append((tid, new_id))
                else:
                    print(f"⚠️  Transition ID '{tid}' has non-standard format")
        
        # Check arcs
        for arc in self.model.get('arcs', []):
            aid = arc['id']
            if not aid.startswith('A'):
                if aid.isdigit():
                    new_id = f"A{aid}"
                    violations['arcs'].append((aid, new_id))
                else:
                    print(f"⚠️  Arc ID '{aid}' has non-standard format")
        
        return violations
    
    def fix_violations(self, violations: Dict[str, List[Tuple[str, str]]]):
        """Fix ID naming violations in the model.
        
        Args:
            violations: Dictionary with violation categories and (old_id, new_id) pairs
        """
        # Build complete ID mapping
        for category, pairs in violations.items():
            for old_id, new_id in pairs:
                self.id_mappings[old_id] = new_id
        
        if not self.id_mappings:
            print("✓ No violations found - model is clean!")
            return
        
        print(f"\n{'='*70}")
        print(f"FIXING {len(self.id_mappings)} ID VIOLATIONS")
        print(f"{'='*70}")
        
        # Fix place IDs
        for place in self.model.get('places', []):
            old_id = place['id']
            if old_id in self.id_mappings:
                new_id = self.id_mappings[old_id]
                place['id'] = new_id
                # Also update name if it matches the old ID
                if place.get('name') == old_id:
                    place['name'] = new_id
                print(f"  Place: {old_id} → {new_id}")
                self.violations_found += 1
        
        # Fix transition IDs
        for transition in self.model.get('transitions', []):
            old_id = transition['id']
            if old_id in self.id_mappings:
                new_id = self.id_mappings[old_id]
                transition['id'] = new_id
                # Also update name if it matches the old ID
                if transition.get('name') == old_id:
                    transition['name'] = new_id
                print(f"  Transition: {old_id} → {new_id}")
                self.violations_found += 1
        
        # Fix arc IDs
        for arc in self.model.get('arcs', []):
            old_id = arc['id']
            if old_id in self.id_mappings:
                new_id = self.id_mappings[old_id]
                arc['id'] = new_id
                print(f"  Arc: {old_id} → {new_id}")
                self.violations_found += 1
        
        # Fix arc references (source_id and target_id)
        print(f"\nUpdating arc references...")
        for arc in self.model.get('arcs', []):
            source_id = arc.get('source_id')
            target_id = arc.get('target_id')
            
            if source_id in self.id_mappings:
                old_source = source_id
                arc['source_id'] = self.id_mappings[source_id]
                print(f"  Arc {arc['id']}: source {old_source} → {self.id_mappings[source_id]}")
                self.arcs_updated += 1
            
            if target_id in self.id_mappings:
                old_target = target_id
                arc['target_id'] = self.id_mappings[target_id]
                print(f"  Arc {arc['id']}: target {old_target} → {self.id_mappings[target_id]}")
                self.arcs_updated += 1
    
    def save_fixed_model(self, backup=True):
        """Save fixed model to file.
        
        Args:
            backup: If True, create backup of original file
        """
        if backup:
            backup_path = f"{self.filepath}.backup"
            shutil.copy2(self.filepath, backup_path)
            print(f"\n✓ Created backup: {backup_path}")
        
        with open(self.filepath, 'w') as f:
            json.dump(self.model, f, indent=2)
        
        print(f"✓ Saved fixed model to {self.filepath}")
    
    def run(self):
        """Run complete fix workflow."""
        print(f"\n{'='*70}")
        print(f"ANALYZING: {self.filepath}")
        print(f"{'='*70}")
        
        self.load_model()
        violations = self.analyze_violations()
        
        # Report violations
        total_violations = sum(len(v) for v in violations.values())
        if total_violations == 0:
            print("\n✓ No ID naming violations found!")
            return
        
        print(f"\nFound {total_violations} violations:")
        for category, pairs in violations.items():
            if pairs:
                print(f"  {category.capitalize()}: {len(pairs)} violations")
                for old_id, new_id in pairs[:3]:  # Show first 3
                    print(f"    {old_id} → {new_id}")
                if len(pairs) > 3:
                    print(f"    ... and {len(pairs) - 3} more")
        
        # Fix violations
        self.fix_violations(violations)
        
        # Save fixed model
        if self.violations_found > 0:
            self.save_fixed_model(backup=True)
            print(f"\n{'='*70}")
            print(f"SUMMARY")
            print(f"{'='*70}")
            print(f"  Fixed {self.violations_found} ID violations")
            print(f"  Updated {self.arcs_updated} arc references")
            print(f"  ✓ Model is now compliant with ID naming conventions!")
        else:
            print("\n✓ No fixes needed!")


def scan_all_models(workspace_path: str):
    """Scan all .shy files in workspace for violations.
    
    Args:
        workspace_path: Path to workspace directory
    """
    print(f"\n{'='*70}")
    print(f"SCANNING ALL MODELS IN: {workspace_path}")
    print(f"{'='*70}\n")
    
    shy_files = list(Path(workspace_path).rglob("*.shy"))
    print(f"Found {len(shy_files)} .shy files\n")
    
    violations_by_file = {}
    
    for filepath in shy_files:
        try:
            fixer = IDNamingFixer(str(filepath))
            fixer.load_model()
            violations = fixer.analyze_violations()
            
            total = sum(len(v) for v in violations.values())
            if total > 0:
                violations_by_file[str(filepath)] = total
                print(f"❌ {filepath.name}: {total} violations")
            else:
                print(f"✓ {filepath.name}: Clean")
        except Exception as e:
            print(f"⚠️  {filepath.name}: Error - {e}")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SCAN SUMMARY")
    print(f"{'='*70}")
    print(f"Total files scanned: {len(shy_files)}")
    print(f"Files with violations: {len(violations_by_file)}")
    
    if violations_by_file:
        print(f"\nFiles needing fixes:")
        for filepath, count in violations_by_file.items():
            print(f"  {filepath}: {count} violations")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    if sys.argv[1] == "--scan-all":
        workspace = os.path.join(os.path.dirname(__file__), "workspace")
        scan_all_models(workspace)
    else:
        filepath = sys.argv[1]
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            sys.exit(1)
        
        fixer = IDNamingFixer(filepath)
        fixer.run()
