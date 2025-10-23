#!/usr/bin/env python3
"""Error 71 Diagnosis Test.

Systematic investigation of potential Error 71 root causes:
1. Malformed UI files (invalid XML, undefined widgets)
2. Dead code (unused widget creation/destruction)
3. Fallback mechanisms (creating widgets when UI load fails)
4. Dynamic widget creation/destruction in panel content
5. Improper widget lifecycle

This test loads each panel UI file and identifies potential issues.

Author: Simão Eugénio
Date: 2025-10-22
"""

import sys
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class UIFileAnalyzer:
    """Analyze UI file for potential Error 71 causes."""
    
    def __init__(self, ui_path):
        """Initialize analyzer.
        
        Args:
            ui_path: Path to UI file
        """
        self.ui_path = ui_path
        self.issues = []
        self.warnings = []
        self.info = []
    
    def analyze(self):
        """Run all analysis checks."""
        print(f"\n{'='*60}")
        print(f"Analyzing: {os.path.basename(self.ui_path)}")
        print(f"{'='*60}\n")
        
        # Check 1: File exists
        if not os.path.exists(self.ui_path):
            self.issues.append(f"❌ File does not exist: {self.ui_path}")
            return
        
        # Check 2: Valid XML
        try:
            tree = ET.parse(self.ui_path)
            root = tree.getroot()
            self.info.append(f"✅ Valid XML structure")
        except ET.ParseError as e:
            self.issues.append(f"❌ MALFORMED XML: {e}")
            return
        
        # Check 3: GTK version
        gtk_version = root.find(".//requires[@lib='gtk+']")
        if gtk_version is not None:
            version = gtk_version.get('version')
            self.info.append(f"📋 GTK version required: {version}")
        else:
            self.warnings.append(f"⚠️ No GTK version requirement specified")
        
        # Check 4: Object definitions
        objects = root.findall(".//object")
        self.info.append(f"📋 Total objects defined: {len(objects)}")
        
        # Check 5: Undefined object references
        self._check_undefined_references(root)
        
        # Check 6: Duplicate IDs
        self._check_duplicate_ids(root)
        
        # Check 7: Missing required properties
        self._check_missing_properties(root)
        
        # Check 8: Deprecated widgets
        self._check_deprecated_widgets(root)
        
        # Check 9: Complex widget hierarchies
        self._check_widget_depth(root)
        
        # Check 10: Load with Gtk.Builder
        self._test_gtk_builder_load()
        
        # Print results
        self._print_results()
    
    def _check_undefined_references(self, root):
        """Check for references to undefined objects."""
        # Get all defined object IDs
        defined_ids = set()
        for obj in root.findall(".//object"):
            obj_id = obj.get('id')
            if obj_id:
                defined_ids.add(obj_id)
        
        # Check all 'object' property references
        undefined_refs = []
        for prop in root.findall(".//property[@name='object']"):
            ref_id = prop.text
            if ref_id and ref_id not in defined_ids:
                undefined_refs.append(ref_id)
        
        if undefined_refs:
            self.issues.append(f"❌ UNDEFINED OBJECT REFERENCES: {', '.join(undefined_refs)}")
        else:
            self.info.append(f"✅ All object references valid")
    
    def _check_duplicate_ids(self, root):
        """Check for duplicate object IDs."""
        ids = []
        for obj in root.findall(".//object"):
            obj_id = obj.get('id')
            if obj_id:
                ids.append(obj_id)
        
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            self.issues.append(f"❌ DUPLICATE IDs: {', '.join(set(duplicates))}")
        else:
            self.info.append(f"✅ No duplicate IDs")
    
    def _check_missing_properties(self, root):
        """Check for missing required properties."""
        # Common required properties by widget type
        required_props = {
            'GtkWindow': ['title'],
            'GtkButton': [],  # No strictly required props
            'GtkLabel': [],
            'GtkEntry': [],
        }
        
        missing_props = []
        for obj in root.findall(".//object"):
            widget_class = obj.get('class')
            obj_id = obj.get('id')
            
            if widget_class in required_props:
                required = required_props[widget_class]
                defined = [prop.get('name') for prop in obj.findall('property')]
                
                for req_prop in required:
                    if req_prop not in defined:
                        missing_props.append(f"{widget_class}#{obj_id} missing '{req_prop}'")
        
        if missing_props:
            self.warnings.append(f"⚠️ Missing properties: {', '.join(missing_props)}")
    
    def _check_deprecated_widgets(self, root):
        """Check for deprecated GTK widgets."""
        deprecated = [
            'GtkHBox', 'GtkVBox',  # Use GtkBox with orientation
            'GtkTable',  # Use GtkGrid
            'GtkAlignment',  # Use GtkWidget alignment properties
            'GtkArrow',  # Deprecated
            'GtkMisc',  # Deprecated
        ]
        
        found_deprecated = []
        for obj in root.findall(".//object"):
            widget_class = obj.get('class')
            if widget_class in deprecated:
                obj_id = obj.get('id', 'unnamed')
                found_deprecated.append(f"{widget_class}#{obj_id}")
        
        if found_deprecated:
            self.warnings.append(f"⚠️ DEPRECATED widgets: {', '.join(found_deprecated)}")
        else:
            self.info.append(f"✅ No deprecated widgets")
    
    def _check_widget_depth(self, root):
        """Check widget hierarchy depth (deep nesting can cause issues)."""
        def get_depth(element, current_depth=0):
            if element.tag == 'object':
                current_depth += 1
            
            max_depth = current_depth
            for child in element:
                child_depth = get_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
            
            return max_depth
        
        max_depth = get_depth(root)
        self.info.append(f"📋 Maximum widget depth: {max_depth}")
        
        if max_depth > 10:
            self.warnings.append(f"⚠️ Deep widget hierarchy ({max_depth} levels) may cause performance issues")
    
    def _test_gtk_builder_load(self):
        """Test loading with Gtk.Builder."""
        try:
            builder = Gtk.Builder()
            builder.add_from_file(self.ui_path)
            self.info.append(f"✅ Gtk.Builder load successful")
            
            # Try to get main object
            objects = builder.get_objects()
            self.info.append(f"📋 Gtk.Builder created {len(objects)} objects")
            
        except Exception as e:
            self.issues.append(f"❌ GTK.BUILDER LOAD FAILED: {e}")
    
    def _print_results(self):
        """Print analysis results."""
        print("\n📊 ANALYSIS RESULTS:\n")
        
        # Issues (critical)
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
            print()
        
        # Warnings
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        # Info
        if self.info:
            print("ℹ️  INFORMATION:")
            for info in self.info:
                print(f"  {info}")
            print()
        
        # Summary
        if self.issues:
            print(f"🔴 RESULT: FAILED - {len(self.issues)} critical issue(s)")
        elif self.warnings:
            print(f"🟡 RESULT: PASSED with {len(self.warnings)} warning(s)")
        else:
            print(f"🟢 RESULT: PASSED - No issues found")


class PanelLoaderAnalyzer:
    """Analyze panel loader Python code for potential issues."""
    
    def __init__(self, loader_path):
        """Initialize analyzer.
        
        Args:
            loader_path: Path to panel loader Python file
        """
        self.loader_path = loader_path
        self.issues = []
        self.warnings = []
        self.info = []
    
    def analyze(self):
        """Run all analysis checks."""
        print(f"\n{'='*60}")
        print(f"Analyzing: {os.path.basename(self.loader_path)}")
        print(f"{'='*60}\n")
        
        # Check 1: File exists
        if not os.path.exists(self.loader_path):
            self.issues.append(f"❌ File does not exist: {self.loader_path}")
            return
        
        # Read file
        with open(self.loader_path, 'r') as f:
            content = f.read()
        
        # Check 2: Dynamic widget creation
        self._check_dynamic_widgets(content)
        
        # Check 3: Fallback mechanisms
        self._check_fallbacks(content)
        
        # Check 4: Widget destruction
        self._check_destructions(content)
        
        # Check 5: Dead code (try-except blocks that catch and ignore)
        self._check_dead_code(content)
        
        # Check 6: Improper widget lifecycle
        self._check_lifecycle(content)
        
        # Print results
        self._print_results()
    
    def _check_dynamic_widgets(self, content):
        """Check for dynamic widget creation."""
        # Look for widget creation outside __init__
        dynamic_patterns = [
            'Gtk.Box(',
            'Gtk.Button(',
            'Gtk.Label(',
            'Gtk.Frame(',
            'Gtk.ScrolledWindow(',
            'Gtk.TextView(',
        ]
        
        lines = content.split('\n')
        dynamic_creations = []
        
        in_init = False
        for i, line in enumerate(lines):
            # Track if we're in __init__
            if 'def __init__' in line:
                in_init = True
            elif line.strip().startswith('def ') and in_init:
                in_init = False
            
            # Check for widget creation outside __init__
            if not in_init:
                for pattern in dynamic_patterns:
                    if pattern in line and 'self.' in line:
                        dynamic_creations.append(f"Line {i+1}: {line.strip()}")
        
        if dynamic_creations:
            self.warnings.append(f"⚠️ Dynamic widget creation found ({len(dynamic_creations)} instances)")
            for creation in dynamic_creations[:5]:  # Show first 5
                self.info.append(f"  {creation}")
        else:
            self.info.append(f"✅ No dynamic widget creation outside __init__")
    
    def _check_fallbacks(self, content):
        """Check for fallback widget creation."""
        fallback_patterns = [
            'except:',
            'except Exception:',
            'if .* is None:.*Gtk\.',
        ]
        
        lines = content.split('\n')
        fallbacks = []
        
        for i, line in enumerate(lines):
            for pattern in fallback_patterns:
                if pattern in line.replace(' ', ''):
                    # Check next few lines for widget creation
                    for j in range(i+1, min(i+5, len(lines))):
                        if 'Gtk.' in lines[j] and '=' in lines[j]:
                            fallbacks.append(f"Line {i+1}-{j+1}: Fallback widget creation")
                            break
        
        if fallbacks:
            self.warnings.append(f"⚠️ Fallback mechanisms found ({len(fallbacks)} instances)")
        else:
            self.info.append(f"✅ No fallback widget creation")
    
    def _check_destructions(self, content):
        """Check for widget destruction."""
        destruction_patterns = [
            '.destroy(',
            '.remove(',
            'del self.',
        ]
        
        lines = content.split('\n')
        destructions = []
        
        for i, line in enumerate(lines):
            for pattern in destruction_patterns:
                if pattern in line:
                    destructions.append(f"Line {i+1}: {line.strip()}")
        
        if destructions:
            self.info.append(f"📋 Widget destruction found ({len(destructions)} instances)")
        else:
            self.info.append(f"✅ No widget destruction")
    
    def _check_dead_code(self, content):
        """Check for dead code (empty except blocks)."""
        lines = content.split('\n')
        dead_code = []
        
        for i, line in enumerate(lines):
            if 'except' in line and ':' in line:
                # Check if next line is just 'pass'
                for j in range(i+1, min(i+3, len(lines))):
                    next_line = lines[j].strip()
                    if next_line == 'pass':
                        dead_code.append(f"Line {i+1}: Empty except block")
                        break
                    elif next_line and not next_line.startswith('#'):
                        break
        
        if dead_code:
            self.warnings.append(f"⚠️ Dead code found ({len(dead_code)} empty except blocks)")
        else:
            self.info.append(f"✅ No obvious dead code")
    
    def _check_lifecycle(self, content):
        """Check for improper widget lifecycle."""
        lifecycle_issues = []
        
        # Check for widget creation in hide/show methods
        if 'def hide(' in content or 'def show(' in content:
            lines = content.split('\n')
            in_hide_show = False
            
            for i, line in enumerate(lines):
                if 'def hide(' in line or 'def show(' in line:
                    in_hide_show = True
                elif line.strip().startswith('def ') and in_hide_show:
                    in_hide_show = False
                
                if in_hide_show and 'Gtk.' in line and '=' in line:
                    lifecycle_issues.append(f"Line {i+1}: Widget creation in hide/show method")
        
        if lifecycle_issues:
            self.warnings.append(f"⚠️ Improper lifecycle: widget creation in hide/show methods")
        else:
            self.info.append(f"✅ No widget creation in hide/show methods")
    
    def _print_results(self):
        """Print analysis results."""
        print("\n📊 ANALYSIS RESULTS:\n")
        
        # Issues (critical)
        if self.issues:
            print("❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
            print()
        
        # Warnings
        if self.warnings:
            print("⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()
        
        # Info
        if self.info:
            print("ℹ️  INFORMATION:")
            for info in self.info:
                print(f"  {info}")
            print()
        
        # Summary
        if self.issues:
            print(f"🔴 RESULT: FAILED - {len(self.issues)} critical issue(s)")
        elif self.warnings:
            print(f"🟡 RESULT: PASSED with {len(self.warnings)} warning(s)")
        else:
            print(f"🟢 RESULT: PASSED - No issues found")


def main():
    """Run Error 71 diagnosis."""
    
    print("\n" + "="*60)
    print("Error 71 Diagnosis Test")
    print("="*60)
    print("\nInvestigating potential Error 71 root causes:")
    print("  1. Malformed UI files")
    print("  2. Dead code")
    print("  3. Fallback mechanisms")
    print("  4. Dynamic widget creation/destruction")
    print("  5. Improper widget lifecycle")
    print("="*60 + "\n")
    
    # Get repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    # Panel UI files to analyze
    ui_files = [
        repo_root / 'ui' / 'panels' / 'left_panel.ui',
        repo_root / 'ui' / 'panels' / 'right_panel.ui',
        repo_root / 'ui' / 'panels' / 'pathway_panel.ui',
        repo_root / 'ui' / 'panels' / 'topology_panel.ui',
    ]
    
    # Panel loader files to analyze
    loader_files = [
        repo_root / 'src' / 'shypn' / 'helpers' / 'left_panel_loader.py',
        repo_root / 'src' / 'shypn' / 'helpers' / 'right_panel_loader.py',
        repo_root / 'src' / 'shypn' / 'helpers' / 'pathway_panel_loader.py',
        repo_root / 'src' / 'shypn' / 'helpers' / 'topology_panel_loader.py',
    ]
    
    # Analyze UI files
    print("\n" + "="*60)
    print("PHASE 1: UI FILE ANALYSIS")
    print("="*60)
    
    ui_results = {}
    for ui_file in ui_files:
        analyzer = UIFileAnalyzer(str(ui_file))
        analyzer.analyze()
        ui_results[ui_file.name] = {
            'issues': len(analyzer.issues),
            'warnings': len(analyzer.warnings),
        }
    
    # Analyze loader files
    print("\n" + "="*60)
    print("PHASE 2: PANEL LOADER ANALYSIS")
    print("="*60)
    
    loader_results = {}
    for loader_file in loader_files:
        analyzer = PanelLoaderAnalyzer(str(loader_file))
        analyzer.analyze()
        loader_results[loader_file.name] = {
            'issues': len(analyzer.issues),
            'warnings': len(analyzer.warnings),
        }
    
    # Final summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60 + "\n")
    
    total_issues = sum(r['issues'] for r in ui_results.values()) + \
                   sum(r['issues'] for r in loader_results.values())
    total_warnings = sum(r['warnings'] for r in ui_results.values()) + \
                     sum(r['warnings'] for r in loader_results.values())
    
    print("📊 UI Files:")
    for name, result in ui_results.items():
        status = "🔴" if result['issues'] > 0 else "🟡" if result['warnings'] > 0 else "🟢"
        print(f"  {status} {name}: {result['issues']} issues, {result['warnings']} warnings")
    
    print("\n📊 Loader Files:")
    for name, result in loader_results.items():
        status = "🔴" if result['issues'] > 0 else "🟡" if result['warnings'] > 0 else "🟢"
        print(f"  {status} {name}: {result['issues']} issues, {result['warnings']} warnings")
    
    print(f"\n📊 OVERALL:")
    print(f"  Total critical issues: {total_issues}")
    print(f"  Total warnings: {total_warnings}")
    
    if total_issues > 0:
        print(f"\n🔴 RECOMMENDATION: REFACTOR REQUIRED")
        print(f"   Critical issues found that may cause Error 71.")
        print(f"   See analysis details above.")
        sys.exit(1)
    elif total_warnings > 0:
        print(f"\n🟡 RECOMMENDATION: REVIEW WARNINGS")
        print(f"   Warnings found that may contribute to Error 71.")
        print(f"   Consider cleaning up code.")
        sys.exit(0)
    else:
        print(f"\n🟢 RECOMMENDATION: PANELS ARE CLEAN")
        print(f"   No issues found. Error 71 likely NOT from panel code.")
        sys.exit(0)


if __name__ == '__main__':
    main()
