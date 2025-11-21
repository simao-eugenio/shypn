"""
Threshold Evaluator for Dynamic Arc Thresholds

This module provides the ThresholdEvaluator class for evaluating dynamic arc thresholds
in SHYPN simulations. It supports three threshold types:

1. **Numeric**: Simple fixed threshold (backward compatible with weight)
2. **Expression**: String formulas with place references (e.g., "4.0 * (1.0 + AMP / 0.1)")
3. **Function**: Lambda functions with dependencies (e.g., lambda ATP, AMP: ...)

The threshold system allows context-dependent regulation where inhibitor arc thresholds
adapt based on other places in the model, enabling multi-level inhibition patterns
common in biological systems.

**Key Behavior**: When `arc.threshold` is set, it SUPERSEDES `arc.weight` for
enablement checking. The `weight` property is still used for token consumption.

Usage:
    evaluator = ThresholdEvaluator(model)
    context = {'time': current_time}
    effective_threshold = evaluator.evaluate(arc, context)
    
    if source_place.tokens >= effective_threshold:
        # Inhibitor arc blocks transition

See Also:
    - doc/ARC_THRESHOLD_SYSTEM.md - Complete threshold system documentation
    - doc/foundation/DUAL_LAYER_INHIBITION.md - Multi-level inhibition patterns
"""

from typing import Dict, Any, Union, Callable
import math
import re


class ThresholdEvaluator:
    """Evaluate dynamic thresholds for arc enablement.
    
    This evaluator handles three types of threshold specifications:
    
    1. **None**: Falls back to arc.weight (backward compatible)
    2. **Numeric** (int/float): Direct threshold value
    3. **Expression** (str): Formula with place references
    4. **Function** (dict): Lambda with dependencies
    
    The evaluator provides safe expression evaluation with restricted builtins
    and automatic resolution of place references by ID or name.
    
    Attributes:
        model: The Petri net model containing places and transitions
        _expression_cache: Cache for compiled expressions (performance)
    
    Example:
        >>> evaluator = ThresholdEvaluator(model)
        >>> arc.threshold = "4.0 * (1.0 + AMP / 0.1)"
        >>> threshold = evaluator.evaluate(arc, {'time': 0.0})
        >>> # Returns 6.0 if AMP place has 0.05 tokens
    """
    
    def __init__(self, model):
        """Initialize threshold evaluator with model reference.
        
        Args:
            model: Petri net model with places and transitions
        """
        self.model = model
        self._expression_cache = {}
    
    def evaluate(self, arc, context: Dict[str, Any]) -> float:
        """Evaluate arc threshold (supersedes weight if threshold is set).
        
        This is the main entry point for threshold evaluation. It determines
        the effective threshold for arc enablement checking.
        
        **Critical Behavior**:
        - If arc.threshold is None → returns arc.weight (backward compatible)
        - If arc.threshold is set → returns evaluated threshold (SUPERSEDES weight)
        
        The arc.weight property is ALWAYS used for token consumption, regardless
        of whether threshold is set.
        
        Args:
            arc: Arc object with optional threshold property
            context: Evaluation context {'time': float, ...}
            
        Returns:
            Effective threshold value for enablement check
            
        Raises:
            ValueError: If threshold type is invalid
            RuntimeError: If expression/function evaluation fails
        
        Examples:
            >>> # Case 1: No threshold (use weight)
            >>> arc.weight = 5
            >>> arc.threshold = None
            >>> evaluator.evaluate(arc, {})  # Returns 5
            
            >>> # Case 2: Numeric threshold (supersedes weight)
            >>> arc.weight = 1
            >>> arc.threshold = 10.0
            >>> evaluator.evaluate(arc, {})  # Returns 10.0 (not 1!)
            
            >>> # Case 3: Expression threshold
            >>> arc.threshold = "P1.tokens * 0.3"
            >>> evaluator.evaluate(arc, {})  # Returns 30 if P1 has 100 tokens
        """
        # Check if threshold property exists and is set
        if not hasattr(arc, 'threshold') or arc.threshold is None:
            # Fallback to weight (traditional behavior)
            return arc.weight
        
        threshold_spec = arc.threshold
        
        # Dispatch based on threshold type
        if isinstance(threshold_spec, (int, float)):
            # Numeric threshold
            return float(threshold_spec)
        
        elif isinstance(threshold_spec, str):
            # Expression-based threshold
            return self._evaluate_expression(threshold_spec, context)
        
        elif isinstance(threshold_spec, dict):
            # Function-based threshold
            return self._evaluate_function(threshold_spec, context)
        
        else:
            raise ValueError(
                f"Invalid threshold type: {type(threshold_spec)}. "
                f"Expected None, numeric, string expression, or function dict."
            )
    
    def _evaluate_expression(self, expr: str, context: Dict) -> float:
        """Evaluate string expression with place references.
        
        Supports:
        - **Place IDs**: P1, P2, P3, ... (maps to places by ID)
        - **Place names**: ATP, ADP, AMP, ... (maps to places by name)
        - **Math functions**: min, max, abs, math.sin, math.exp, ...
        - **Time reference**: time or t (from context)
        - **Conditional expressions**: (... if ... else ...)
        
        The expression is evaluated in a restricted context with no access
        to arbitrary builtins, preventing security issues.
        
        Args:
            expr: String expression to evaluate
            context: Evaluation context (must contain 'time' key)
            
        Returns:
            Evaluated threshold value
            
        Raises:
            RuntimeError: If expression evaluation fails
        
        Examples:
            >>> expr = "4.0 * (1.0 + AMP / 0.1)"
            >>> # If AMP place has 0.05 tokens:
            >>> result = evaluator._evaluate_expression(expr, {'time': 0.0})
            >>> # Returns: 4.0 * (1.0 + 0.05/0.1) = 4.0 * 1.5 = 6.0
            
            >>> expr = "P1.tokens * (0.2 if P2.tokens > 50 else 0.5)"
            >>> # Conditional threshold based on P2 state
        """
        # Build safe evaluation context
        eval_context = {
            'min': min,
            'max': max,
            'abs': abs,
            'math': math,
            'pow': pow,
            'round': round,
        }
        
        # Add all places from model
        places_dict = self._get_places_dict()
        
        for place_id, place in places_dict.items():
            # Add as P1, P2, P3, ... (by ID)
            eval_context[f'P{place_id}'] = place.tokens
            
            # Add by name (if available)
            if hasattr(place, 'name') and place.name:
                # Use place name directly (e.g., ATP, ADP, AMP)
                eval_context[place.name] = place.tokens
        
        # Add time reference
        eval_context['time'] = context.get('time', 0.0)
        eval_context['t'] = eval_context['time']
        
        try:
            # Evaluate expression with restricted builtins
            result = eval(expr, {"__builtins__": {}}, eval_context)
            return float(result)
        
        except NameError as e:
            # Provide helpful error message with available names
            available_places = [f'P{pid}' for pid in places_dict.keys()]
            available_names = [p.name for p in places_dict.values() if hasattr(p, 'name') and p.name]
            
            raise RuntimeError(
                f"Failed to evaluate threshold expression '{expr}': {e}\n"
                f"Available place IDs: {available_places}\n"
                f"Available place names: {available_names}\n"
                f"Available functions: min, max, abs, math, pow, round\n"
                f"Available variables: time, t"
            )
        
        except Exception as e:
            # Generic evaluation error
            raise RuntimeError(
                f"Failed to evaluate threshold expression '{expr}': {e}\n"
                f"Expression syntax may be invalid or contain unsupported operations."
            )
    
    def _evaluate_function(self, func_spec: Dict, context: Dict) -> float:
        """Evaluate function-based threshold with dependencies.
        
        Function specifications must have the format:
        {
            "type": "function",
            "formula": "lambda ATP, AMP, Ca: 4.0 * (1.0 + AMP / 0.1) * (1.0 - Ca / 10.0)",
            "dependencies": ["P5", "P6", "P7"]  # Place IDs or names
        }
        
        The formula is a lambda function that receives place token values
        as arguments. Dependencies are resolved to place objects by ID or name.
        
        Args:
            func_spec: Function specification dictionary
            context: Evaluation context (must contain 'time' key)
            
        Returns:
            Evaluated threshold value
            
        Raises:
            ValueError: If func_spec is missing required keys
            RuntimeError: If function evaluation fails
        
        Examples:
            >>> func_spec = {
            ...     "type": "function",
            ...     "formula": "lambda ATP, AMP: 4.0 * (1.0 + AMP / 0.1)",
            ...     "dependencies": ["P5", "P6"]
            ... }
            >>> result = evaluator._evaluate_function(func_spec, {'time': 0.0})
        """
        # Extract formula and dependencies
        formula = func_spec.get('formula')
        dependencies = func_spec.get('dependencies', [])
        
        if not formula:
            raise ValueError("Function threshold missing 'formula' key")
        
        # Resolve dependencies to place token values
        places_dict = self._get_places_dict()
        args = {}
        
        for dep in dependencies:
            token_value = None
            
            # Try resolving as direct place ID (integer or string)
            if isinstance(dep, int) and dep in places_dict:
                token_value = places_dict[dep].tokens
                args[f'P{dep}'] = token_value
            
            # Try resolving as place ID string
            elif isinstance(dep, str):
                # Check P1, P2, ... format
                if dep.startswith('P') and dep[1:].isdigit():
                    place_id = int(dep[1:])
                    if place_id in places_dict:
                        token_value = places_dict[place_id].tokens
                        args[dep] = token_value
                
                # Check if it's a place ID directly
                elif dep.isdigit():
                    place_id = int(dep)
                    if place_id in places_dict:
                        token_value = places_dict[place_id].tokens
                        args[f'P{place_id}'] = token_value
                
                # Try resolving as place name
                else:
                    for place_id, place in places_dict.items():
                        if hasattr(place, 'name') and place.name == dep:
                            token_value = place.tokens
                            args[dep] = token_value
                            break
            
            # Warn if dependency couldn't be resolved
            if token_value is None:
                import sys
                print(f"Warning: Could not resolve threshold dependency '{dep}'", file=sys.stderr)
        
        # Add time if referenced in dependencies
        if 'time' in dependencies or 't' in dependencies:
            args['time'] = context.get('time', 0.0)
            args['t'] = args['time']
        
        try:
            # Evaluate lambda function
            # Build safe context with math module
            safe_context = {
                'math': math,
                'min': min,
                'max': max,
                'abs': abs,
            }
            
            func = eval(formula, {"__builtins__": {}}, safe_context)
            
            # Call function with resolved arguments
            result = func(**args)
            return float(result)
        
        except TypeError as e:
            raise RuntimeError(
                f"Failed to call threshold function: {e}\n"
                f"Formula: {formula}\n"
                f"Dependencies: {dependencies}\n"
                f"Resolved arguments: {args}\n"
                f"Check that lambda parameter names match dependency names."
            )
        
        except Exception as e:
            raise RuntimeError(
                f"Failed to evaluate threshold function: {e}\n"
                f"Formula: {formula}\n"
                f"Dependencies: {dependencies}\n"
                f"Resolved arguments: {args}"
            )
    
    def _get_places_dict(self) -> Dict[int, Any]:
        """Get all places from model indexed by ID.
        
        Handles different model architectures:
        - model.places as dict
        - model.places as list
        - model.get_all_places() method
        
        Returns:
            Dictionary mapping place ID (int) to place object
        """
        if hasattr(self.model, 'places'):
            if isinstance(self.model.places, dict):
                # Already a dict, but may be keyed by string IDs
                result = {}
                for key, place in self.model.places.items():
                    if hasattr(place, 'id'):
                        # Use place's actual ID
                        result[place.id if isinstance(place.id, int) else int(place.id)] = place
                    else:
                        # Use dict key as ID
                        result[int(key) if isinstance(key, str) and key.isdigit() else key] = place
                return result
            
            elif isinstance(self.model.places, list):
                # Convert list to dict
                return {
                    p.id if isinstance(p.id, int) else int(p.id): p 
                    for p in self.model.places 
                    if hasattr(p, 'id')
                }
        
        elif hasattr(self.model, 'get_all_places'):
            # Use model method
            places = self.model.get_all_places()
            return {
                p.id if isinstance(p.id, int) else int(p.id): p 
                for p in places 
                if hasattr(p, 'id')
            }
        
        # No places found
        return {}
