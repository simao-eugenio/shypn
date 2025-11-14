"""Expression validator for mathematical expressions in property dialogs.

Provides safe validation and evaluation of user-entered expressions
for transition rates, guards, and other mathematical properties.
"""

import ast
import json
from typing import Tuple, Any, Dict, Optional


class ExpressionValidator:
    """Validate and evaluate mathematical expressions safely.
    
    Provides:
    - Syntax validation for Python expressions
    - Safety checking (no imports, no exec, etc.)
    - Preview evaluation with sample state
    - Support for numeric, dict, and lambda expressions
    """
    
    # Allowed modules for import (currently none - all forbidden)
    ALLOWED_MODULES = set()
    
    # Allowed built-in functions
    ALLOWED_FUNCTIONS = {
        'abs', 'min', 'max', 'round', 'sum',
        'int', 'float', 'str', 'bool', 'len',
    }
    
    # Allowed math functions (if we add math module support)
    MATH_FUNCTIONS = {
        'sin', 'cos', 'tan', 'exp', 'log', 'log10',
        'sqrt', 'pow', 'ceil', 'floor', 'pi', 'e',
    }
    
    @staticmethod
    def validate_expression(expr_str: str, allow_dict: bool = True) -> Tuple[bool, str, Any]:
        """Validate a mathematical expression.
        
        Args:
            expr_str: Expression string to validate
            allow_dict: If True, allow dict literals (for threshold functions)
        
        Returns:
            Tuple of (is_valid, error_message, parsed_value)
            - is_valid: True if expression is valid
            - error_message: Error description if invalid, empty string if valid
            - parsed_value: None, numeric value, compiled code, or dict
        """
        if not expr_str or not expr_str.strip():
            return (True, "", None)
        
        expr_str = expr_str.strip()
        
        # Try to parse as JSON dict first (for threshold functions)
        if allow_dict and (expr_str.startswith('{') or expr_str.startswith('{')):
            try:
                dict_value = json.loads(expr_str)
                if isinstance(dict_value, dict):
                    return (True, "", dict_value)
            except json.JSONDecodeError:
                pass  # Not JSON, continue with other parsers
        
        # Try to parse as numeric value
        try:
            numeric_value = float(expr_str)
            return (True, "", numeric_value)
        except ValueError:
            pass  # Not numeric, continue
        
        # Try to parse as Python expression
        try:
            tree = ast.parse(expr_str, mode='eval')
            
            # Validate AST for safety
            validator = SafeExpressionVisitor()
            validator.visit(tree)
            
            # Compile for later evaluation
            compiled = compile(tree, '<string>', 'eval')
            
            return (True, "", compiled)
            
        except SyntaxError as e:
            return (False, f"Syntax error: {e.msg} at position {e.offset}", None)
        except ValueError as e:
            return (False, f"Invalid expression: {str(e)}", None)
        except Exception as e:
            return (False, f"Error: {str(e)}", None)
    
    @staticmethod
    def evaluate_preview(expr: Any, state: Optional[Dict[str, Any]] = None) -> str:
        """Evaluate expression with sample state for preview.
        
        Args:
            expr: Parsed expression (numeric, compiled code, or dict)
            state: State dictionary for evaluation (e.g., {'P1': 10, 'P2': 5})
        
        Returns:
            Preview string like "≈ 2.5" or "[Error: ...]"
        """
        if expr is None:
            return ""
        
        # If it's already a number
        if isinstance(expr, (int, float)):
            return f"{expr}"
        
        # If it's a dict (threshold function)
        if isinstance(expr, dict):
            return "[Threshold Function]"
        
        # If it's compiled code, try to evaluate
        if state is None:
            state = {}
        
        try:
            # Safe evaluation with restricted builtins
            safe_builtins = {name: __builtins__[name] for name in ExpressionValidator.ALLOWED_FUNCTIONS}
            result = eval(expr, {"__builtins__": safe_builtins}, state)
            
            if isinstance(result, (int, float)):
                return f"≈ {result:.3f}"
            elif isinstance(result, bool):
                return f"{result}"
            elif isinstance(result, dict):
                return "[Threshold Dict]"
            else:
                return f"[{type(result).__name__}]"
                
        except NameError as e:
            # Missing variable in state
            return f"[Needs: {str(e).split(chr(39))[1]}]"
        except Exception as e:
            return f"[Error: {str(e)[:30]}]"
    
    @staticmethod
    def format_for_display(value: Any) -> str:
        """Format a value for display in UI field.
        
        Args:
            value: Can be None, dict, number, or expression string
        
        Returns:
            Formatted string for display
        """
        if value is None:
            return ""
        elif isinstance(value, dict):
            # Format dict as JSON for readability
            return json.dumps(value, indent=2)
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value)
        else:
            return str(value)


class SafeExpressionVisitor(ast.NodeVisitor):
    """AST visitor to validate expression safety.
    
    Ensures expressions don't contain:
    - Import statements
    - Exec/eval calls
    - Attribute access (to prevent OS access)
    - Function definitions
    - Class definitions
    - Dangerous operations
    """
    
    # Allowed AST node types for safe expressions
    ALLOWED_NODES = {
        # Basic structure
        ast.Expression,
        
        # Operators
        ast.BinOp, ast.UnaryOp, ast.Compare,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or,
        
        # Comparisons
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Is, ast.IsNot, ast.In, ast.NotIn,
        
        # Values (ast.Num/ast.Str unified as ast.Constant in modern Python)
        ast.Constant,
        
        # Containers
        ast.List, ast.Tuple, ast.Dict, ast.Set,
        
        # Variables and subscripting
        ast.Name, ast.Load, ast.Store,
        ast.Subscript, ast.Index, ast.Slice,
        
        # Conditionals
        ast.IfExp,  # Ternary operator: x if condition else y
        ast.BoolOp,
        
        # Function calls (with restrictions)
        ast.Call,
        
        # Lambda (for inline functions)
        ast.Lambda,
        ast.arguments, ast.arg,
    }
    
    # Forbidden names (prevent access to dangerous builtins)
    FORBIDDEN_NAMES = {
        'eval', 'exec', 'compile', 'open', 'input',
        '__import__', '__builtins__', 'globals', 'locals',
        'vars', 'dir', 'help', 'quit', 'exit',
    }
    
    def visit(self, node):
        """Visit node and validate it's allowed."""
        node_type = type(node)
        
        # Check if node type is allowed
        if node_type not in self.ALLOWED_NODES:
            raise ValueError(
                f"Forbidden operation: {node_type.__name__}. "
                f"Expressions must be simple mathematical operations."
            )
        
        # Additional checks for specific node types
        if isinstance(node, ast.Name):
            if node.id in self.FORBIDDEN_NAMES:
                raise ValueError(f"Forbidden name: '{node.id}'")
        
        if isinstance(node, ast.Call):
            # Check function being called
            if isinstance(node.func, ast.Name):
                if node.func.id in self.FORBIDDEN_NAMES:
                    raise ValueError(f"Forbidden function call: '{node.func.id}'")
                
                # Only allow whitelisted functions
                if node.func.id not in ExpressionValidator.ALLOWED_FUNCTIONS:
                    # Allow it but warn that it needs to be in scope
                    pass
        
        # Attribute access is forbidden (prevents os.system, etc.)
        if isinstance(node, ast.Attribute):
            raise ValueError(
                f"Attribute access forbidden: '{node.attr}'. "
                f"Cannot access object attributes for security reasons."
            )
        
        # Recursively visit child nodes
        return super().visit(node)
    
    def generic_visit(self, node):
        """Override to provide better error messages."""
        try:
            return super().generic_visit(node)
        except ValueError:
            raise  # Re-raise our validation errors
        except Exception as e:
            raise ValueError(f"Invalid expression structure: {str(e)}")


# Convenience function for quick validation
def validate_rate_expression(expr_str: str) -> Tuple[bool, str, Any]:
    """Convenience wrapper for validating rate expressions."""
    return ExpressionValidator.validate_expression(expr_str, allow_dict=False)


def validate_guard_expression(expr_str: str) -> Tuple[bool, str, Any]:
    """Convenience wrapper for validating guard expressions."""
    return ExpressionValidator.validate_expression(expr_str, allow_dict=True)


def validate_threshold_expression(expr_str: str) -> Tuple[bool, str, Any]:
    """Convenience wrapper for validating threshold expressions (allows dicts)."""
    return ExpressionValidator.validate_expression(expr_str, allow_dict=True)
