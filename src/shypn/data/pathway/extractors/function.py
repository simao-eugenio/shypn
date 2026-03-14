"""
Function Definition Extractor

Extracts SBML function definitions (user-defined functions in MathML).
Parses lambda expressions and stores them for formula expansion.
"""

from typing import Dict, List
import re

try:
    import libsbml
except ImportError:
    libsbml = None

from .base import BaseExtractor


class FunctionDefinition:
    """Represents an SBML function definition.
    
    Attributes:
        id: Function identifier (used in formulas)
        name: Human-readable name
        arguments: List of parameter names
        body: MathML expression (simplified to infix notation)
        body_raw: Raw MathML formula for debugging
    """
    
    def __init__(self, id: str, name: str, arguments: List[str], body: str, body_raw: str = ""):
        self.id = id
        self.name = name
        self.arguments = arguments
        self.body = body
        self.body_raw = body_raw
    
    def expand(self, arg_values: List[str]) -> str:
        """Expand function call with actual arguments.
        
        Args:
            arg_values: List of actual argument expressions
            
        Returns:
            Expanded formula with arguments substituted
            
        Example:
            func = FunctionDefinition('MM', 'Michaelis-Menten', ['S', 'Km', 'Vmax'], 
                                     'Vmax * S / (Km + S)')
            result = func.expand(['ATP', '0.5', '100'])
            # Returns: '100 * ATP / (0.5 + ATP)'
        """
        if len(arg_values) != len(self.arguments):
            raise ValueError(
                f"Function {self.id} expects {len(self.arguments)} arguments, "
                f"got {len(arg_values)}"
            )
        
        # Substitute each argument with its value
        result = self.body
        for param, value in zip(self.arguments, arg_values):
            # Use word boundaries to avoid partial matches
            # e.g., replacing 'S' shouldn't affect 'Vmax'
            result = re.sub(r'\b' + re.escape(param) + r'\b', f'({value})', result)
        
        return result
    
    def __repr__(self):
        args = ', '.join(self.arguments)
        return f"FunctionDefinition({self.id}({args}) = {self.body})"


class FunctionDefinitionExtractor(BaseExtractor[Dict[str, FunctionDefinition]]):
    """
    Extracts SBML function definitions.
    
    Parses <functionDefinition> elements containing MathML lambda expressions.
    Converts MathML to simplified infix notation for formula expansion.
    
    Example SBML:
        <functionDefinition id="MM">
          <math xmlns="http://www.w3.org/1998/Math/MathML">
            <lambda>
              <bvar><ci>S</ci></bvar>
              <bvar><ci>Km</ci></bvar>
              <bvar><ci>Vmax</ci></bvar>
              <apply><divide/>
                <apply><times/><ci>Vmax</ci><ci>S</ci></apply>
                <apply><plus/><ci>Km</ci><ci>S</ci></apply>
              </apply>
            </lambda>
          </math>
        </functionDefinition>
    """
    
    def extract(self) -> Dict[str, FunctionDefinition]:
        """
        Extract all function definitions from SBML model.
        
        Returns:
            Dict mapping function IDs to FunctionDefinition objects
        """
        functions: Dict[str, FunctionDefinition] = {}
        
        num_functions = self.model.getNumFunctionDefinitions()
        
        if num_functions == 0:
            self.logger.debug("No function definitions in model")
            return functions
        
        self.logger.info(f"Extracting {num_functions} function definitions...")
        
        for i in range(num_functions):
            func_def = self.model.getFunctionDefinition(i)
            
            try:
                function = self._extract_function(func_def)
                functions[function.id] = function
                self.logger.debug(f"  Extracted: {function}")
            except (AttributeError, ValueError, TypeError) as e:
                self.logger.warning(
                    f"Failed to extract function {func_def.getId()}: {e}"
                )
        
        return functions
    
    def _extract_function(self, func_def) -> FunctionDefinition:
        """Extract a single function definition.
        
        Args:
            func_def: libsbml FunctionDefinition object
            
        Returns:
            FunctionDefinition object
        """
        func_id = func_def.getId()
        func_name = func_def.getName() or func_id
        
        # Get MathML AST
        math_ast = func_def.getMath()
        if math_ast is None:
            raise ValueError(f"Function {func_id} has no math definition")
        
        # MathML lambda structure: <lambda> <bvar>...</bvar>+ <body> </lambda>
        if math_ast.getType() != libsbml.AST_LAMBDA:
            raise ValueError(f"Function {func_id} math is not a lambda expression")
        
        # Extract arguments (bound variables)
        arguments = []
        num_children = math_ast.getNumChildren()
        
        # All children except the last are <bvar> (bound variables)
        # The last child is the function body
        for i in range(num_children - 1):
            bvar = math_ast.getChild(i)
            if bvar.isName():
                arguments.append(bvar.getName())
            else:
                self.logger.warning(
                    f"Function {func_id}: bvar {i} is not a name, skipping"
                )
        
        # Extract function body (last child)
        body_ast = math_ast.getChild(num_children - 1)
        body = self._ast_to_infix(body_ast)
        body_raw = libsbml.formulaToL3String(body_ast)
        
        return FunctionDefinition(func_id, func_name, arguments, body, body_raw)
    
    def _ast_to_infix(self, ast_node) -> str:
        """Convert MathML AST to infix notation string.
        
        Args:
            ast_node: libsbml ASTNode
            
        Returns:
            Infix formula string
            
        Example:
            <apply><plus/><ci>A</ci><ci>B</ci></apply>  →  "A + B"
        """
        node_type = ast_node.getType()
        
        # Numbers
        if ast_node.isNumber():
            if ast_node.isInteger():
                return str(ast_node.getInteger())
            else:
                return str(ast_node.getReal())
        
        # Variables (names)
        if ast_node.isName():
            return ast_node.getName()
        
        # Constants
        if ast_node.isConstant():
            if node_type == libsbml.AST_CONSTANT_E:
                return "e"
            elif node_type == libsbml.AST_CONSTANT_PI:
                return "pi"
            elif node_type == libsbml.AST_CONSTANT_TRUE:
                return "True"
            elif node_type == libsbml.AST_CONSTANT_FALSE:
                return "False"
        
        # Operators
        num_children = ast_node.getNumChildren()
        
        # Binary operators
        if node_type == libsbml.AST_PLUS:
            return self._binary_op(ast_node, "+")
        elif node_type == libsbml.AST_MINUS:
            if num_children == 1:
                # Unary minus
                return f"-({self._ast_to_infix(ast_node.getChild(0))})"
            else:
                return self._binary_op(ast_node, "-")
        elif node_type == libsbml.AST_TIMES:
            return self._binary_op(ast_node, "*")
        elif node_type == libsbml.AST_DIVIDE:
            return self._binary_op(ast_node, "/")
        elif node_type == libsbml.AST_POWER:
            left = self._ast_to_infix(ast_node.getChild(0))
            right = self._ast_to_infix(ast_node.getChild(1))
            return f"({left})**({right})"
        
        # Relational operators
        elif node_type == libsbml.AST_RELATIONAL_EQ:
            return self._binary_op(ast_node, "==")
        elif node_type == libsbml.AST_RELATIONAL_NEQ:
            return self._binary_op(ast_node, "!=")
        elif node_type == libsbml.AST_RELATIONAL_LT:
            return self._binary_op(ast_node, "<")
        elif node_type == libsbml.AST_RELATIONAL_LEQ:
            return self._binary_op(ast_node, "<=")
        elif node_type == libsbml.AST_RELATIONAL_GT:
            return self._binary_op(ast_node, ">")
        elif node_type == libsbml.AST_RELATIONAL_GEQ:
            return self._binary_op(ast_node, ">=")
        
        # Logical operators
        elif node_type == libsbml.AST_LOGICAL_AND:
            return self._binary_op(ast_node, "and")
        elif node_type == libsbml.AST_LOGICAL_OR:
            return self._binary_op(ast_node, "or")
        elif node_type == libsbml.AST_LOGICAL_NOT:
            return f"not ({self._ast_to_infix(ast_node.getChild(0))})"
        
        # Functions
        elif node_type == libsbml.AST_FUNCTION:
            func_name = ast_node.getName()
            args = [self._ast_to_infix(ast_node.getChild(i)) 
                   for i in range(num_children)]
            return f"{func_name}({', '.join(args)})"
        
        # Built-in functions
        elif ast_node.isFunction():
            return self._builtin_function(ast_node)
        
        # Piecewise (if-then-else)
        elif node_type == libsbml.AST_FUNCTION_PIECEWISE:
            return self._piecewise(ast_node)
        
        # Fallback: use libsbml's formula conversion
        return libsbml.formulaToL3String(ast_node)
    
    def _binary_op(self, ast_node, operator: str) -> str:
        """Convert binary operator to infix.
        
        Args:
            ast_node: libsbml ASTNode with 2+ children
            operator: Infix operator string (+, -, *, /, etc.)
            
        Returns:
            Infix expression with parentheses
        """
        num_children = ast_node.getNumChildren()
        
        if num_children == 2:
            left = self._ast_to_infix(ast_node.getChild(0))
            right = self._ast_to_infix(ast_node.getChild(1))
            return f"({left} {operator} {right})"
        else:
            # N-ary operator (e.g., a + b + c)
            operands = [self._ast_to_infix(ast_node.getChild(i)) 
                       for i in range(num_children)]
            return f"({f' {operator} '.join(operands)})"
    
    def _builtin_function(self, ast_node) -> str:
        """Convert built-in mathematical function.
        
        Args:
            ast_node: libsbml ASTNode representing a function
            
        Returns:
            Python function call string
        """
        node_type = ast_node.getType()
        num_children = ast_node.getNumChildren()
        
        # Special handling for power function (can be AST_FUNCTION_POWER or AST_POWER)
        if node_type == libsbml.AST_FUNCTION_POWER:
            if num_children == 2:
                base = self._ast_to_infix(ast_node.getChild(0))
                exponent = self._ast_to_infix(ast_node.getChild(1))
                return f"(({base})**({exponent}))"
        
        # Map SBML function types to Python equivalents
        function_map = {
            libsbml.AST_FUNCTION_ABS: 'abs',
            libsbml.AST_FUNCTION_ARCCOS: 'acos',
            libsbml.AST_FUNCTION_ARCCOSH: 'acosh',
            libsbml.AST_FUNCTION_ARCCOT: 'acot',
            libsbml.AST_FUNCTION_ARCCOTH: 'acoth',
            libsbml.AST_FUNCTION_ARCCSC: 'acsc',
            libsbml.AST_FUNCTION_ARCCSCH: 'acsch',
            libsbml.AST_FUNCTION_ARCSEC: 'asec',
            libsbml.AST_FUNCTION_ARCSECH: 'asech',
            libsbml.AST_FUNCTION_ARCSIN: 'asin',
            libsbml.AST_FUNCTION_ARCSINH: 'asinh',
            libsbml.AST_FUNCTION_ARCTAN: 'atan',
            libsbml.AST_FUNCTION_ARCTANH: 'atanh',
            libsbml.AST_FUNCTION_CEILING: 'ceil',
            libsbml.AST_FUNCTION_COS: 'cos',
            libsbml.AST_FUNCTION_COSH: 'cosh',
            libsbml.AST_FUNCTION_COT: 'cot',
            libsbml.AST_FUNCTION_COTH: 'coth',
            libsbml.AST_FUNCTION_CSC: 'csc',
            libsbml.AST_FUNCTION_CSCH: 'csch',
            libsbml.AST_FUNCTION_EXP: 'exp',
            libsbml.AST_FUNCTION_FLOOR: 'floor',
            libsbml.AST_FUNCTION_LN: 'log',
            libsbml.AST_FUNCTION_LOG: 'log10',
            libsbml.AST_FUNCTION_ROOT: 'sqrt',  # Special case for square root
            libsbml.AST_FUNCTION_SEC: 'sec',
            libsbml.AST_FUNCTION_SECH: 'sech',
            libsbml.AST_FUNCTION_SIN: 'sin',
            libsbml.AST_FUNCTION_SINH: 'sinh',
            libsbml.AST_FUNCTION_TAN: 'tan',
            libsbml.AST_FUNCTION_TANH: 'tanh',
        }
        
        func_name = function_map.get(node_type, 'unknown')
        
        # Special handling for root (degree, radicand)
        if node_type == libsbml.AST_FUNCTION_ROOT:
            if num_children == 1:
                # Square root
                arg = self._ast_to_infix(ast_node.getChild(0))
                return f"sqrt({arg})"
            elif num_children == 2:
                # Nth root: root(degree, radicand)
                degree = self._ast_to_infix(ast_node.getChild(0))
                radicand = self._ast_to_infix(ast_node.getChild(1))
                return f"({radicand})**(1.0/({degree}))"
        
        # Standard function call
        args = [self._ast_to_infix(ast_node.getChild(i)) 
               for i in range(num_children)]
        return f"{func_name}({', '.join(args)})"
    
    def _piecewise(self, ast_node) -> str:
        """Convert piecewise (if-then-else) to Python ternary.
        
        Args:
            ast_node: libsbml ASTNode of type AST_FUNCTION_PIECEWISE
            
        Returns:
            Python conditional expression
            
        Example:
            <piecewise>
              <piece><ci>A</ci><apply><gt/><ci>x</ci><cn>0</cn></apply></piece>
              <otherwise><ci>B</ci></otherwise>
            </piecewise>
            
            Converts to: "A if x > 0 else B"
        """
        num_children = ast_node.getNumChildren()
        
        # Piecewise structure: (value1, condition1, value2, condition2, ..., otherwise)
        # Must have odd number of children (pairs + otherwise)
        
        if num_children < 2:
            return "0"  # Degenerate case
        
        # Build nested ternary from right to left
        # Start with the "otherwise" value (last child if odd, else 0)
        if num_children % 2 == 1:
            result = self._ast_to_infix(ast_node.getChild(num_children - 1))
            pairs = num_children - 1
        else:
            result = "0"
            pairs = num_children
        
        # Process pairs in reverse (value, condition)
        for i in range(pairs - 2, -1, -2):
            value = self._ast_to_infix(ast_node.getChild(i))
            condition = self._ast_to_infix(ast_node.getChild(i + 1))
            result = f"({value} if {condition} else {result})"
        
        return result
