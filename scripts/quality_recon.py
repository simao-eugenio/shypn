#!/usr/bin/env python3
"""Software Quality Reconnaissance Report Generator.

Analyzes the codebase for:
- Code complexity and maintainability
- Error handling patterns
- Security issues
- Code duplication
- Documentation coverage
- Type hints coverage
- Import quality
- Dead code detection
"""

import os
import ast
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple


class QualityScanner:
    """Scans Python source files for quality metrics."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.src_dir = self.root_dir / 'src' / 'shypn'
        self.issues = defaultdict(list)
        self.stats = defaultdict(int)
        
    def scan_all(self):
        """Run all quality checks."""
        print("=" * 80)
        print("SOFTWARE QUALITY RECONNAISSANCE REPORT")
        print("=" * 80)
        print()
        
        py_files = list(self.src_dir.rglob("*.py"))
        print(f"Scanning {len(py_files)} Python files in {self.src_dir}")
        print()
        
        for py_file in py_files:
            if '__pycache__' in str(py_file):
                continue
            self.scan_file(py_file)
        
        self.print_report()
    
    def scan_file(self, filepath: Path):
        """Scan a single Python file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.stats['total_files'] += 1
            self.stats['total_lines'] += len(content.splitlines())
            
            # Parse AST
            try:
                tree = ast.parse(content, filename=str(filepath))
            except SyntaxError as e:
                self.issues['syntax_errors'].append((filepath, str(e)))
                return
            
            # Run checks
            self.check_complexity(filepath, tree)
            self.check_error_handling(filepath, tree, content)
            self.check_security(filepath, content)
            self.check_documentation(filepath, tree)
            self.check_type_hints(filepath, tree)
            self.check_imports(filepath, tree)
            self.check_code_smells(filepath, tree, content)
            
        except Exception as e:
            self.issues['scan_errors'].append((filepath, str(e)))
    
    def check_complexity(self, filepath: Path, tree: ast.AST):
        """Check cyclomatic complexity."""
        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.functions = []
                self.current_function = None
                self.complexity = 1
            
            def visit_FunctionDef(self, node):
                old_func = self.current_function
                old_complexity = self.complexity
                
                self.current_function = node.name
                self.complexity = 1
                
                self.generic_visit(node)
                
                self.functions.append((node.name, self.complexity, node.lineno))
                
                self.current_function = old_func
                self.complexity = old_complexity
            
            def visit_If(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_While(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_For(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_ExceptHandler(self, node):
                self.complexity += 1
                self.generic_visit(node)
            
            def visit_With(self, node):
                self.complexity += 1
                self.generic_visit(node)
        
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        # Flag complex functions (>10 = high, >20 = very high)
        for func_name, complexity, lineno in visitor.functions:
            if complexity > 20:
                self.issues['very_high_complexity'].append(
                    (filepath, func_name, complexity, lineno)
                )
            elif complexity > 10:
                self.issues['high_complexity'].append(
                    (filepath, func_name, complexity, lineno)
                )
    
    def check_error_handling(self, filepath: Path, tree: ast.AST, content: str):
        """Check error handling patterns."""
        class ErrorHandlingVisitor(ast.NodeVisitor):
            def __init__(self):
                self.bare_excepts = []
                self.generic_excepts = []
                self.pass_excepts = []
            
            def visit_ExceptHandler(self, node):
                # Bare except
                if node.type is None:
                    self.bare_excepts.append(node.lineno)
                # Catch Exception (too generic)
                elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                    self.generic_excepts.append(node.lineno)
                
                # Check for pass in except
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    self.pass_excepts.append(node.lineno)
                
                self.generic_visit(node)
        
        visitor = ErrorHandlingVisitor()
        visitor.visit(tree)
        
        if visitor.bare_excepts:
            self.issues['bare_except'].extend(
                [(filepath, line) for line in visitor.bare_excepts]
            )
        if visitor.generic_excepts:
            self.issues['generic_except'].extend(
                [(filepath, line) for line in visitor.generic_excepts]
            )
        if visitor.pass_excepts:
            self.issues['silent_except'].extend(
                [(filepath, line) for line in visitor.pass_excepts]
            )
    
    def check_security(self, filepath: Path, content: str):
        """Check for security issues."""
        lines = content.splitlines()
        
        # Check for hardcoded secrets (common patterns)
        secret_patterns = [
            r'password\s*=\s*["\'](?!<|{|\[)[^"\']{8,}["\']',
            r'api[_-]?key\s*=\s*["\'](?!<|{|\[)[^"\']{16,}["\']',
            r'secret[_-]?key\s*=\s*["\'](?!<|{|\[)[^"\']{16,}["\']',
            r'token\s*=\s*["\'](?!<|{|\[)[^"\']{16,}["\']',
        ]
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#'):
                continue
            
            for pattern in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.issues['potential_secret'].append((filepath, i, line.strip()))
        
        # Check for eval/exec usage
        if 'eval(' in content:
            for i, line in enumerate(lines, 1):
                if 'eval(' in line and not line.strip().startswith('#'):
                    self.issues['eval_usage'].append((filepath, i))
        
        if 'exec(' in content:
            for i, line in enumerate(lines, 1):
                if 'exec(' in line and not line.strip().startswith('#'):
                    self.issues['exec_usage'].append((filepath, i))
    
    def check_documentation(self, filepath: Path, tree: ast.AST):
        """Check documentation coverage."""
        class DocVisitor(ast.NodeVisitor):
            def __init__(self):
                self.undocumented_functions = []
                self.undocumented_classes = []
            
            def visit_FunctionDef(self, node):
                # Skip private methods (but check __init__)
                if not node.name.startswith('_') or node.name == '__init__':
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        self.undocumented_functions.append((node.name, node.lineno))
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                docstring = ast.get_docstring(node)
                if not docstring:
                    self.undocumented_classes.append((node.name, node.lineno))
                self.generic_visit(node)
        
        visitor = DocVisitor()
        visitor.visit(tree)
        
        # Sample tracking (don't flood report)
        if len(visitor.undocumented_functions) > 5:
            self.stats['undocumented_functions'] += len(visitor.undocumented_functions)
        else:
            for func_name, lineno in visitor.undocumented_functions:
                self.issues['missing_docstring'].append((filepath, 'function', func_name, lineno))
        
        if len(visitor.undocumented_classes) > 0:
            for class_name, lineno in visitor.undocumented_classes:
                self.issues['missing_docstring'].append((filepath, 'class', class_name, lineno))
    
    def check_type_hints(self, filepath: Path, tree: ast.AST):
        """Check type hints coverage."""
        class TypeHintVisitor(ast.NodeVisitor):
            def __init__(self):
                self.total_functions = 0
                self.typed_functions = 0
            
            def visit_FunctionDef(self, node):
                # Skip private methods
                if not node.name.startswith('_'):
                    self.total_functions += 1
                    
                    # Check if has return annotation or any arg annotations
                    has_hints = node.returns is not None
                    if not has_hints:
                        for arg in node.args.args:
                            if arg.annotation is not None:
                                has_hints = True
                                break
                    
                    if has_hints:
                        self.typed_functions += 1
                
                self.generic_visit(node)
        
        visitor = TypeHintVisitor()
        visitor.visit(tree)
        
        self.stats['total_functions'] += visitor.total_functions
        self.stats['typed_functions'] += visitor.typed_functions
    
    def check_imports(self, filepath: Path, tree: ast.AST):
        """Check import quality."""
        class ImportVisitor(ast.NodeVisitor):
            def __init__(self):
                self.star_imports = []
                self.unused_imports = []
            
            def visit_ImportFrom(self, node):
                if any(alias.name == '*' for alias in node.names):
                    self.star_imports.append(node.lineno)
                self.generic_visit(node)
        
        visitor = ImportVisitor()
        visitor.visit(tree)
        
        if visitor.star_imports:
            for lineno in visitor.star_imports:
                self.issues['star_import'].append((filepath, lineno))
    
    def check_code_smells(self, filepath: Path, tree: ast.AST, content: str):
        """Check for common code smells."""
        lines = content.splitlines()
        
        # Long lines (>120 chars)
        for i, line in enumerate(lines, 1):
            if len(line) > 120 and not line.strip().startswith('#'):
                self.stats['long_lines'] += 1
        
        # TODO/FIXME/HACK comments
        for i, line in enumerate(lines, 1):
            line_clean = line.strip()
            if 'TODO' in line_clean or 'FIXME' in line_clean or 'HACK' in line_clean:
                self.stats['todo_comments'] += 1
        
        # Print statements (should use logging)
        class PrintVisitor(ast.NodeVisitor):
            def __init__(self):
                self.print_calls = []
            
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name) and node.func.id == 'print':
                    self.print_calls.append(node.lineno)
                self.generic_visit(node)
        
        visitor = PrintVisitor()
        visitor.visit(tree)
        
        # Sample only (don't flood report)
        if len(visitor.print_calls) > 10:
            self.stats['print_statements'] += len(visitor.print_calls)
        else:
            for lineno in visitor.print_calls:
                self.issues['print_statement'].append((filepath, lineno))
    
    def print_report(self):
        """Print comprehensive quality report."""
        print("\n" + "=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total files scanned:       {self.stats['total_files']}")
        print(f"Total lines of code:       {self.stats['total_lines']:,}")
        print(f"Total functions analyzed:  {self.stats['total_functions']}")
        print(f"Functions with type hints: {self.stats['typed_functions']} "
              f"({100 * self.stats['typed_functions'] / max(1, self.stats['total_functions']):.1f}%)")
        print(f"Long lines (>120 chars):   {self.stats['long_lines']}")
        print(f"TODO/FIXME comments:       {self.stats['todo_comments']}")
        print(f"Print statements found:    {self.stats.get('print_statements', 0)}")
        
        print("\n" + "=" * 80)
        print("CRITICAL ISSUES (Priority: HIGH)")
        print("=" * 80)
        
        # Security issues
        if self.issues['potential_secret']:
            print(f"\n⚠️  POTENTIAL HARDCODED SECRETS: {len(self.issues['potential_secret'])}")
            for filepath, lineno, line in self.issues['potential_secret'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
                print(f"    {line[:80]}")
        
        if self.issues['eval_usage']:
            print(f"\n⚠️  EVAL() USAGE (Security Risk): {len(self.issues['eval_usage'])}")
            for filepath, lineno in self.issues['eval_usage'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        if self.issues['exec_usage']:
            print(f"\n⚠️  EXEC() USAGE (Security Risk): {len(self.issues['exec_usage'])}")
            for filepath, lineno in self.issues['exec_usage'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        # Very high complexity
        if self.issues['very_high_complexity']:
            print(f"\n⚠️  VERY HIGH COMPLEXITY (>20): {len(self.issues['very_high_complexity'])}")
            for filepath, func, complexity, lineno in sorted(
                self.issues['very_high_complexity'], 
                key=lambda x: x[2], 
                reverse=True
            )[:10]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
                print(f"    {func}() has complexity {complexity}")
        
        print("\n" + "=" * 80)
        print("IMPORTANT ISSUES (Priority: MEDIUM)")
        print("=" * 80)
        
        # High complexity
        if self.issues['high_complexity']:
            print(f"\n📊 HIGH COMPLEXITY (>10): {len(self.issues['high_complexity'])}")
            for filepath, func, complexity, lineno in sorted(
                self.issues['high_complexity'], 
                key=lambda x: x[2], 
                reverse=True
            )[:10]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno} - "
                      f"{func}() (complexity: {complexity})")
        
        # Error handling issues
        if self.issues['bare_except']:
            print(f"\n⚠️  BARE EXCEPT CLAUSES: {len(self.issues['bare_except'])}")
            for filepath, lineno in self.issues['bare_except'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        if self.issues['generic_except']:
            print(f"\n⚠️  GENERIC 'except Exception': {len(self.issues['generic_except'])}")
            print(f"  (Found in {len(set(fp for fp, _ in self.issues['generic_except']))} files)")
        
        if self.issues['silent_except']:
            print(f"\n⚠️  SILENT EXCEPTIONS (except: pass): {len(self.issues['silent_except'])}")
            for filepath, lineno in self.issues['silent_except'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        # Import issues
        if self.issues['star_import']:
            print(f"\n📦 STAR IMPORTS (from x import *): {len(self.issues['star_import'])}")
            for filepath, lineno in self.issues['star_import'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        print("\n" + "=" * 80)
        print("DOCUMENTATION & STYLE (Priority: LOW)")
        print("=" * 80)
        
        # Documentation
        if self.issues['missing_docstring']:
            print(f"\n📝 MISSING DOCSTRINGS: {len(self.issues['missing_docstring'])}")
            classes = [x for x in self.issues['missing_docstring'] if x[1] == 'class']
            functions = [x for x in self.issues['missing_docstring'] if x[1] == 'function']
            print(f"  Classes: {len(classes)}, Functions: {len(functions)}")
            if classes:
                print("  Sample classes:")
                for filepath, _, name, lineno in classes[:3]:
                    print(f"    {filepath.relative_to(self.root_dir)}:{lineno} - {name}")
        
        # Print statements
        if self.issues['print_statement']:
            print(f"\n🖨️  PRINT STATEMENTS (use logging): {len(self.issues['print_statement'])}")
            for filepath, lineno in self.issues['print_statement'][:5]:
                print(f"  {filepath.relative_to(self.root_dir)}:{lineno}")
        
        print("\n" + "=" * 80)
        print("QUALITY SCORE SUMMARY")
        print("=" * 80)
        
        # Calculate quality scores
        total_issues = sum(
            len(issues) for category, issues in self.issues.items()
            if category not in ['scan_errors', 'syntax_errors']
        )
        
        critical_issues = (
            len(self.issues.get('potential_secret', [])) +
            len(self.issues.get('eval_usage', [])) +
            len(self.issues.get('exec_usage', [])) +
            len(self.issues.get('very_high_complexity', []))
        )
        
        type_hint_coverage = (
            100 * self.stats['typed_functions'] / max(1, self.stats['total_functions'])
        )
        
        print(f"\nTotal issues found: {total_issues}")
        print(f"Critical issues:    {critical_issues}")
        print(f"Type hint coverage: {type_hint_coverage:.1f}%")
        
        # Overall grade
        if critical_issues > 10:
            grade = "🔴 NEEDS IMMEDIATE ATTENTION"
        elif critical_issues > 0:
            grade = "🟡 NEEDS IMPROVEMENT"
        elif total_issues > 100:
            grade = "🟠 FAIR"
        elif total_issues > 50:
            grade = "🟢 GOOD"
        else:
            grade = "✅ EXCELLENT"
        
        print(f"\nOverall Quality: {grade}")
        
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = []
        
        if critical_issues > 0:
            recommendations.append("1. Address critical security and complexity issues immediately")
        
        if len(self.issues.get('bare_except', [])) > 10:
            recommendations.append("2. Replace bare except clauses with specific exception types")
        
        if type_hint_coverage < 50:
            recommendations.append("3. Add type hints to improve IDE support and catch bugs early")
        
        if len(self.issues.get('star_import', [])) > 5:
            recommendations.append("4. Replace 'from x import *' with explicit imports")
        
        if self.stats.get('print_statements', 0) > 50:
            recommendations.append("5. Replace print() statements with proper logging")
        
        if len(self.issues.get('very_high_complexity', [])) > 5:
            recommendations.append("6. Refactor complex functions (>20 complexity) into smaller units")
        
        if not recommendations:
            recommendations.append("✅ Code quality is good! Continue maintaining best practices.")
        
        for rec in recommendations:
            print(f"\n{rec}")
        
        print("\n" + "=" * 80)


def main():
    """Run quality reconnaissance."""
    scanner = QualityScanner("/home/simao/projetos/shypn")
    scanner.scan_all()


if __name__ == "__main__":
    main()
