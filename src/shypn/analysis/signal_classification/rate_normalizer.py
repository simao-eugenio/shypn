"""
Rate Function Normalizer

Normalizes rate functions from different sources into analysis-ready expressions.

Problem:
- SBML/KEGG imports store function calls: "michaelis_menten(S, vmax=1.0, km=0.5)"
- Manual entry uses expressions: "Vmax * S / (Km + S)"
- Signal classification needs biochemical expressions for pattern matching

Solution:
- Parse function call syntax
- Convert to equivalent biochemical expressions
- Maintain bidirectional mapping for reconstruction
- Support multiple kinetic law types

Author: Signal Classification System
Date: 2024-12-31
"""

import re
import logging
from typing import Optional, Dict, List, Tuple


class RateFunctionNormalizer:
    """
    Normalizes rate functions from different formats to analysis-ready expressions.
    
    Supports:
    - Function call syntax: michaelis_menten(S, vmax=1.0, km=0.5)
    - Biochemical expressions: Vmax * S / (Km + S)
    - Numeric values: 2.5
    - Complex expressions: kf * A * B - kr * C
    
    Converts function calls to expressions for pattern matching analysis.
    """
    
    # Catalog function patterns (function call → expression template)
    FUNCTION_TEMPLATES = {
        'michaelis_menten': {
            'pattern': r'michaelis_menten\(([^,]+)(?:,\s*vmax=([^,]+))?(?:,\s*km=([^,]+))?\)',
            'expression': lambda s, vmax, km: f"({vmax} * {s} / ({km} + {s}))",
            'parameters': ['substrate', 'vmax', 'km'],
            'default_params': {'vmax': 'Vmax', 'km': 'Km'}
        },
        'hill': {
            'pattern': r'hill\(([^,]+)(?:,\s*vmax=([^,]+))?(?:,\s*k=([^,]+))?(?:,\s*n=([^,]+))?\)',
            'expression': lambda s, vmax, k, n: f"({vmax} * {s}^{n} / ({k}^{n} + {s}^{n}))",
            'parameters': ['substrate', 'vmax', 'k', 'n'],
            'default_params': {'vmax': 'Vmax', 'k': 'K', 'n': 'n'}
        },
        'mass_action': {
            # Pattern: mass_action(A) or mass_action(A, B) or mass_action(A, rate_constant=k) or mass_action(A, B, rate_constant=k)
            'pattern': r'mass_action\(([^,]+)(?:,\s*(?:rate_constant=([^)]+)|([^,]+)))?(?:,\s*rate_constant=([^)]+))?\)',
            'expression': lambda a, k1, b, k2: (
                # k2 takes precedence (last rate_constant), then k1, then default
                f"({k2 or k1 or 'k'} * {a} * {b})" if b and b != '1.0'
                else f"({k1 or 'k'} * {a})"
            ),
            'parameters': ['reactant1', 'rate_constant1', 'reactant2', 'rate_constant2'],
            'default_params': {'rate_constant1': 'k', 'reactant2': '1.0', 'rate_constant2': 'k'}
        },
        'reversible_mass_action': {
            'pattern': r'reversible_mass_action\(([^,]+),\s*([^,]+)(?:,\s*kf=([^,]+))?(?:,\s*kr=([^,]+))?\)',
            'expression': lambda a, b, kf, kr: f"({kf} * {a} - {kr} * {b})",
            'parameters': ['forward_reactant', 'reverse_reactant', 'kf', 'kr'],
            'default_params': {'kf': 'kf', 'kr': 'kr'}
        },
        'competitive_inhibition': {
            'pattern': r'competitive_inhibition\(([^,]+),\s*([^,]+)(?:,\s*vmax=([^,]+))?(?:,\s*km=([^,]+))?(?:,\s*ki=([^,]+))?\)',
            'expression': lambda s, i, vmax, km, ki: f"({vmax} * {s} / ({km} * (1 + {i}/{ki}) + {s}))",
            'parameters': ['substrate', 'inhibitor', 'vmax', 'km', 'ki'],
            'default_params': {'vmax': 'Vmax', 'km': 'Km', 'ki': 'Ki'}
        }
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize normalizer.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def normalize(self, rate_value) -> List[str]:
        """
        Normalize rate function to analysis-ready expression(s).
        
        Args:
            rate_value: Rate value (string, numeric, or None)
            
        Returns:
            List of normalized expression strings
            Empty list if rate is numeric or None
        """
        if not rate_value:
            return []
        
        # Numeric rates don't reference places
        if isinstance(rate_value, (int, float)):
            return []
        
        # Must be string expression
        if not isinstance(rate_value, str):
            return []
        
        rate_str = rate_value.strip()
        
        # Empty after stripping
        if not rate_str:
            return []
        
        # Try to parse as function call
        expressions = self._parse_function_calls(rate_str)
        if expressions:
            return expressions
        
        # Not a function call - return as-is (already an expression)
        return [rate_str]
    
    def _parse_function_calls(self, rate_str: str) -> List[str]:
        """
        Parse function call syntax and convert to expressions.
        
        Handles:
        - Single function: michaelis_menten(S, vmax=1.0, km=0.5)
        - Multiple functions: michaelis_menten(S1, vmax=1.0, km=0.5) * (S2 / (0.5 + S2))
        - Nested functions: hill(S, vmax=michaelis_menten(E, vmax=1.0, km=0.1), k=0.5, n=2)
        
        Args:
            rate_str: Rate function string
            
        Returns:
            List of normalized expressions
            Empty list if no function calls found
        """
        expressions = []
        
        # Track what we've converted to avoid duplicate processing
        converted = rate_str
        made_conversion = False
        
        # Try each function type
        for func_name, template in self.FUNCTION_TEMPLATES.items():
            pattern = template['pattern']
            
            # Find all matches of this function
            matches = list(re.finditer(pattern, converted, re.IGNORECASE))
            
            for match in reversed(matches):  # Process from end to preserve positions
                # Extract matched groups
                groups = match.groups()
                
                # Build expression from template
                try:
                    expr = self._build_expression(func_name, groups, template)
                    
                    if expr:
                        # Replace function call with expression in converted string
                        converted = converted[:match.start()] + expr + converted[match.end():]
                        made_conversion = True
                        
                        self.logger.debug(
                            f"Converted {func_name}(...) → {expr}"
                        )
                    
                except Exception as e:
                    self.logger.warning(
                        f"Failed to convert {func_name} call: {match.group(0)}, error: {e}"
                    )
        
        # If we made conversions, return the converted string
        if made_conversion:
            expressions.append(converted)
        
        return expressions
    
    def _build_expression(
        self,
        func_name: str,
        groups: Tuple,
        template: Dict
    ) -> str:
        """
        Build biochemical expression from function template and parameters.
        
        Args:
            func_name: Function name
            groups: Regex match groups
            template: Function template
            
        Returns:
            Biochemical expression string
        """
        param_names = template['parameters']
        default_params = template.get('default_params', {})
        
        # Extract values from groups, keeping None for missing groups
        values = []
        for i, group_value in enumerate(groups):
            if i < len(param_names):
                if group_value:
                    values.append(group_value.strip())
                else:
                    values.append(None)  # Keep None for missing groups
        
        # Pad with None if needed
        while len(values) < len(param_names):
            values.append(None)
        
        # Replace None with defaults where needed
        final_values = []
        for i, value in enumerate(values):
            if value is None:
                param_name = param_names[i]
                default = default_params.get(param_name)
                final_values.append(default if default else '1.0')
            else:
                final_values.append(value)
        
        # Apply expression template
        expression_func = template['expression']
        return expression_func(*final_values)
    
    def is_function_call(self, rate_str: str) -> bool:
        """
        Check if rate string is a function call.
        
        Args:
            rate_str: Rate function string
            
        Returns:
            True if string matches any function call pattern
        """
        if not isinstance(rate_str, str):
            return False
        
        for template in self.FUNCTION_TEMPLATES.values():
            if re.search(template['pattern'], rate_str, re.IGNORECASE):
                return True
        
        return False
    
    def get_function_name(self, rate_str: str) -> Optional[str]:
        """
        Extract function name from function call.
        
        Args:
            rate_str: Rate function string
            
        Returns:
            Function name or None
        """
        if not isinstance(rate_str, str):
            return None
        
        for func_name, template in self.FUNCTION_TEMPLATES.items():
            if re.search(template['pattern'], rate_str, re.IGNORECASE):
                return func_name
        
        return None
    
    def denormalize(self, expression: str, target_format: str = 'expression') -> str:
        """
        Convert expression back to specified format (future extension).
        
        Args:
            expression: Biochemical expression
            target_format: 'expression' or 'function_call'
            
        Returns:
            Expression in target format
        """
        # Currently just returns expression as-is
        # Could implement reverse conversion: (Vmax * S / (Km + S)) → michaelis_menten(S, vmax=Vmax, km=Km)
        return expression
