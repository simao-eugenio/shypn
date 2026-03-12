"""Safe expression evaluation utilities.

Provides secure alternatives to eval() for mathematical expression evaluation.
Uses AST parsing and validation to prevent code injection attacks.

This module replaces unsafe eval() calls throughout the codebase with
validated, compiled expression evaluation.

Security Notes:
- No attribute access (prevents os.system, etc.)
- No imports (prevents __import__)
- No exec/eval/compile nesting
- Validates AST before compilation
- Restricted namespace at evaluation time

Usage:
    >>> from shypn.utils.safe_eval import safe_eval_numeric
    >>> context = {'P1': 10, 'P2': 5}
    >>> result = safe_eval_numeric("P1 + P2 * 2", context)
    >>> print(result)  # 20.0
"""

import ast
import math
from typing import Dict, Any, Optional, Union

# Module-level cache: expression string → compiled code object.
# AST validation runs once per unique expression, then the compiled bytecode is reused.
_COMPILED_EXPR_CACHE: dict = {}

# Pre-built base namespaces reused across every call (never mutated — always .copy()-ed).
_BASE_MATH_NS: dict = {
    "__builtins__": {},
    'abs': abs, 'min': min, 'max': max,
    'round': round, 'int': int, 'float': float,
    'sum': sum, 'len': len,
    'math': math,
}
_BASE_NO_MATH_NS: dict = {"__builtins__": {}}


def _get_compiled(expr: str) -> object:
    """Return the compiled bytecode for *expr*, parsing/validating only on first use."""
    cached = _COMPILED_EXPR_CACHE.get(expr)
    if cached is not None:
        return cached
    tree = ast.parse(expr, mode='eval')
    SafeExpressionValidator().visit(tree)
    compiled = compile(tree, '<safe_eval>', 'eval')
    _COMPILED_EXPR_CACHE[expr] = compiled
    return compiled


class SafeExpressionValidator(ast.NodeVisitor):
    """AST visitor to validate expression safety.
    
    Ensures expressions don't contain:
    - Import statements
    - Exec/eval calls
    - Attribute access (to prevent OS/module access)
    - Function/class definitions
    - Dangerous operations
    
    This is a security-focused validator used before eval().
    """
    
    # Allowed AST node types for safe mathematical expressions
    ALLOWED_NODES = {
        # Basic structure
        ast.Expression,
        
        # Arithmetic operators
        ast.BinOp, ast.UnaryOp,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd,
        
        # Comparison operators
        ast.Compare,
        ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
        ast.Is, ast.IsNot, ast.In, ast.NotIn,
        
        # Boolean operators
        ast.BoolOp, ast.And, ast.Or, ast.Not,
        
        # Values (ast.Num/ast.Str unified as ast.Constant in Python 3.8+)
        ast.Constant,
        ast.Num,  # For Python 3.7 compatibility
        ast.Str,  # For Python 3.7 compatibility
        
        # Containers
        ast.List, ast.Tuple, ast.Dict, ast.Set,
        
        # Variables and subscripting
        ast.Name, ast.Load, ast.Store,
        ast.Subscript, ast.Index, ast.Slice,
        
        # Attribute access (restricted to math.* only)
        ast.Attribute,
        
        # Conditionals (ternary: x if condition else y)
        ast.IfExp,
        
        # Function calls (with restrictions - only allowed functions)
        ast.Call,
        
        # Lambda functions (for threshold functions)
        ast.Lambda,
        ast.arguments, ast.arg, ast.keyword,
    }
    
    # Forbidden names that could enable code execution or system access
    FORBIDDEN_NAMES = {
        'eval', 'exec', 'compile', 'open', 'input', 'print',
        '__import__', '__builtins__', 'globals', 'locals',
        'vars', 'dir', 'help', 'quit', 'exit', 'getattr', 'setattr',
        'delattr', 'hasattr', 'callable', 'classmethod', 'staticmethod',
    }
    
    def visit(self, node):
        """Visit node and validate it's allowed."""
        node_type = type(node)
        
        # Check if node type is allowed
        if node_type not in self.ALLOWED_NODES:
            raise ValueError(
                f"⚠️ Security: Forbidden operation '{node_type.__name__}'. "
                f"Only mathematical expressions are allowed."
            )
        
        # Check for forbidden names
        if isinstance(node, ast.Name):
            if node.id in self.FORBIDDEN_NAMES:
                raise ValueError(
                    f"⚠️ Security: Forbidden name '{node.id}'. "
                    f"This could enable code execution."
                )
        
        # Check function calls
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in self.FORBIDDEN_NAMES:
                    raise ValueError(
                        f"⚠️ Security: Forbidden function '{node.func.id}'. "
                        f"This could enable code execution."
                    )
        
        # CRITICAL: Attribute access is mostly forbidden
        # This prevents os.system(), module.dangerous_func(), etc.
        # Exception: Allow math.function_name patterns
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == 'math':
                # Allow math.sin, math.cos, math.sqrt, etc.
                # Don't raise error, continue with visitor
                pass
            else:
                raise ValueError(
                    f"⚠️ Security: Attribute access forbidden ('{node.attr}'). "
                    f"Cannot access object attributes for security."
                )
        
        # Recursively visit child nodes
        return super().visit(node)


def safe_eval_numeric(
    expr: str,
    context: Dict[str, Any],
    default_on_error: Optional[float] = None,
    allow_math: bool = True
) -> float:
    """Safely evaluate a mathematical expression to a float.
    
    This is the primary replacement for eval() throughout the codebase.
    Uses AST validation to prevent code injection attacks.
    
    Args:
        expr: Expression string (e.g., "P1 + P2 * 2")
        context: Variable namespace (e.g., {'P1': 10, 'P2': 5})
        default_on_error: Value to return on error (None = raise exception)
        allow_math: If True, include math module functions
    
    Returns:
        Float result of evaluation
    
    Raises:
        ValueError: If expression is unsafe or invalid syntax
        RuntimeError: If evaluation fails and no default provided
    
    Examples:
        >>> safe_eval_numeric("P1 + P2", {'P1': 10, 'P2': 5})
        15.0
        
        >>> safe_eval_numeric("2 * P1 ** 2", {'P1': 3})
        18.0
        
        >>> safe_eval_numeric("min(P1, P2)", {'P1': 10, 'P2': 5}, allow_math=True)
        5.0
    
    Security:
        - Validates AST before execution
        - No attribute access allowed
        - No imports, exec, eval allowed
        - Restricted namespace
    """
    try:
        compiled = _get_compiled(expr)
        
        # Use context directly as locals — no per-call dict merge.
        # _BASE_MATH_NS / _BASE_NO_MATH_NS (globals) provides math builtins and
        # disables __builtins__; context (locals) provides place tokens + params.
        globals_ns = _BASE_MATH_NS if allow_math else _BASE_NO_MATH_NS
        result = eval(compiled, globals_ns, context)
        return float(result)
        
    except (SyntaxError, ValueError) as e:
        # Invalid expression or security violation
        if default_on_error is not None:
            return default_on_error
        raise ValueError(f"Invalid expression '{expr}': {e}")
        
    except Exception as e:
        # Evaluation error (e.g., NameError, ZeroDivisionError)
        if default_on_error is not None:
            return default_on_error
        raise RuntimeError(f"Failed to evaluate '{expr}': {e}")


def safe_eval_bool(
    expr: str,
    context: Dict[str, Any],
    default_on_error: Optional[bool] = None
) -> bool:
    """Safely evaluate an expression to a boolean.
    
    Used for guard conditions and boolean expressions.
    
    Args:
        expr: Expression string (e.g., "P1 > 5 and P2 < 10")
        context: Variable namespace
        default_on_error: Value to return on error (None = raise exception)
    
    Returns:
        Boolean result
    
    Examples:
        >>> safe_eval_bool("P1 > 5", {'P1': 10})
        True
        
        >>> safe_eval_bool("P1 < P2", {'P1': 10, 'P2': 5})
        False
    """
    try:
        compiled = _get_compiled(expr)
        result = eval(compiled, _BASE_MATH_NS, context)
        return bool(result)
        
    except Exception as e:
        if default_on_error is not None:
            return default_on_error
        raise RuntimeError(f"Failed to evaluate '{expr}': {e}")


def safe_eval_function(
    formula: str,
    args: Dict[str, Any]
) -> Any:
    """Safely evaluate a lambda function with arguments.
    
    Used for threshold functions: lambda P1, P2: P1 + P2
    
    Args:
        formula: Lambda expression string
        args: Arguments to pass to lambda
    
    Returns:
        Result of lambda evaluation
    
    Examples:
        >>> safe_eval_function("lambda x, y: x + y", {'x': 10, 'y': 5})
        15
    """
    try:
        # Parse and validate
        tree = ast.parse(formula, mode='eval')
        validator = SafeExpressionValidator()
        validator.visit(tree)
        compiled = compile(tree, '<safe_eval>', 'eval')
        
        # Evaluate lambda
        safe_namespace = {
            "__builtins__": {},
            'math': math,
            'abs': abs,
            'min': min,
            'max': max,
        }
        
        func = eval(compiled, safe_namespace)
        
        # Call lambda with arguments
        result = func(**args)
        return float(result)
        
    except Exception as e:
        raise RuntimeError(
            f"Failed to evaluate lambda '{formula}' with args {args}: {e}"
        )


def preprocess_expression(expr: str) -> str:
    """Preprocess expression to support chemistry notation.
    
    Converts [PlaceName] to PlaceName for chemistry notation compatibility.
    This is used in rate functions where [ATP] means "concentration of ATP".
    
    Args:
        expr: Raw expression string
    
    Returns:
        Preprocessed expression string
    
    Examples:
        >>> preprocess_expression("[ATP] + [ADP]")
        'ATP + ADP'
        
        >>> preprocess_expression("2 * [P1]")
        '2 * P1'
    """
    import re
    return re.sub(r'\[([^\]]+)\]', r'\1', expr)


# Backward compatibility aliases for gradual migration
def safe_numeric_eval(expr: str, context: Dict[str, Any]) -> float:
    """Alias for safe_eval_numeric (backward compatibility)."""
    return safe_eval_numeric(expr, context)


def safe_boolean_eval(expr: str, context: Dict[str, Any]) -> bool:
    """Alias for safe_eval_bool (backward compatibility)."""
    return safe_eval_bool(expr, context)
