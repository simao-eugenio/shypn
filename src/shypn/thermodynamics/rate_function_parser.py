"""Rate function parser for thermodynamic validation.

Extracts forward and reverse rate constants from transition rate functions,
supporting both expression-based and catalog function formats.
"""

import re
import logging
from typing import Optional, Tuple, Dict


logger = logging.getLogger(__name__)


class RateFunctionParser:
    """Parse rate functions to extract forward/reverse components for thermodynamic validation.
    
    Supports multiple formats:
    1. Separate rate_forward/rate_reverse attributes
    2. Net rate expressions: "k_f*[A]*[B] - k_r*[C]*[D]"
    3. Mass action: "1e6*[ATP]*[H2O] - 1e3*[ADP]*[Pi]"
    4. Catalog functions with parameters
    
    Example:
        >>> parser = RateFunctionParser()
        >>> k_f, k_r = parser.extract_rate_constants(transition, reactants, products)
        >>> if k_f and k_r:
        ...     # Can validate thermodynamics
    """
    
    def __init__(self):
        """Initialize rate function parser."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_rate_constants(
        self,
        transition,
        reactants: Dict[str, int],
        products: Dict[str, int]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Extract forward and reverse rate constants from transition.
        
        Tries multiple strategies in order:
        1. Direct attributes (rate_forward, rate_reverse)
        2. Properties dictionary (k_forward, k_reverse)
        3. Rate function parsing (rate_function property)
        
        Args:
            transition: Transition object
            reactants: Dict of {compound_id: stoichiometry} for reactants
            products: Dict of {compound_id: stoichiometry} for products
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None) if not extractable
        """
        # Strategy 1: Direct attributes
        k_f, k_r = self._extract_from_attributes(transition)
        if k_f is not None and k_r is not None:
            return k_f, k_r
        
        # Strategy 2: Properties dictionary
        k_f, k_r = self._extract_from_properties(transition)
        if k_f is not None and k_r is not None:
            return k_f, k_r
        
        # Strategy 3: Parse rate function
        k_f, k_r = self._parse_rate_function(transition, reactants, products)
        if k_f is not None and k_r is not None:
            return k_f, k_r
        
        return None, None
    
    def _extract_from_attributes(self, transition) -> Tuple[Optional[float], Optional[float]]:
        """Extract from rate_forward/rate_reverse attributes.
        
        Args:
            transition: Transition object
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        try:
            if hasattr(transition, 'rate_forward') and hasattr(transition, 'rate_reverse'):
                if transition.rate_forward and transition.rate_reverse:
                    k_f = float(transition.rate_forward)
                    k_r = float(transition.rate_reverse)
                    if k_r > 0:  # Must be reversible
                        self.logger.debug(f"Extracted from attributes: k_f={k_f}, k_r={k_r}")
                        return k_f, k_r
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.debug(f"Failed to extract from attributes: {e}")
        
        return None, None
    
    def _extract_from_properties(self, transition) -> Tuple[Optional[float], Optional[float]]:
        """Extract from properties dictionary.
        
        Args:
            transition: Transition object
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        try:
            properties = getattr(transition, 'properties', None)
            if properties and isinstance(properties, dict):
                k_f = properties.get('k_forward')
                k_r = properties.get('k_reverse')
                
                if k_f is not None and k_r is not None:
                    k_f = float(k_f)
                    k_r = float(k_r)
                    if k_r > 0:  # Must be reversible
                        self.logger.debug(f"Extracted from properties: k_f={k_f}, k_r={k_r}")
                        return k_f, k_r
        except (ValueError, TypeError, AttributeError) as e:
            self.logger.debug(f"Failed to extract from properties: {e}")
        
        return None, None
    
    def _parse_rate_function(
        self,
        transition,
        reactants: Dict[str, int],
        products: Dict[str, int]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Parse rate_function property to extract rate constants.
        
        Handles formats like:
        - "k_f*[A]*[B] - k_r*[C]*[D]"
        - "1e6*[ATP]*[H2O] - 1e3*[ADP]*[Pi]"
        - "forward_rate([A],[B]) - reverse_rate([C],[D])"
        
        Args:
            transition: Transition object
            reactants: Dict of reactant compound IDs
            products: Dict of product compound IDs
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        # Get rate function string - check both attribute and properties
        rate_func = None
        if hasattr(transition, 'rate_function'):
            rate_func_val = getattr(transition, 'rate_function', None)
            if rate_func_val:
                rate_func = str(rate_func_val)
        
        # Also check in properties if not found
        if not rate_func:
            properties = getattr(transition, 'properties', None)
            if properties and isinstance(properties, dict):
                rate_func_val = properties.get('rate_function')
                if rate_func_val:
                    rate_func = str(rate_func_val)
        
        if not rate_func:
            return None, None
        
        self.logger.debug(f"Parsing rate function: {rate_func}")
        
        # Try different parsing strategies
        
        # Strategy A: Net mass action with subtraction
        result = self._parse_net_mass_action(rate_func, reactants, products)
        if result[0] is not None:
            return result
        
        # Strategy B: Explicit k_f and k_r symbols
        result = self._parse_explicit_constants(rate_func)
        if result[0] is not None:
            return result
        
        # Strategy C: Function calls (catalog functions)
        result = self._parse_catalog_function(rate_func)
        if result[0] is not None:
            return result
        
        self.logger.warning(f"Could not parse rate function: {rate_func}")
        return None, None
    
    def _parse_net_mass_action(
        self,
        rate_func: str,
        reactants: Dict[str, int],
        products: Dict[str, int]
    ) -> Tuple[Optional[float], Optional[float]]:
        """Parse net mass action: "k_f*terms - k_r*terms".
        
        Pattern: coefficient * [species] * [species] - coefficient * [species]
        
        Args:
            rate_func: Rate function string
            reactants: Reactant compound IDs
            products: Product compound IDs
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        # Pattern: number (e.g., 1e6, 1.5e-3) followed by multiplication and species
        # Example: "1e6*[ATP]*[H2O] - 1e3*[ADP]*[Pi]" or "10.0*ATP*H2O - 0.01*ADP*Pi"
        
        self.logger.info(f"Parsing net mass action: {rate_func}")
        
        # Split on minus sign (but not inside brackets or in scientific notation)
        # Negative lookahead (?![^[]*\]) ensures we don't split inside brackets
        # Negative lookbehind (?<![eE]) ensures we don't split scientific notation like 1e-10
        parts = re.split(r'(?<![eE])\s*-\s*(?![^[]*\])', rate_func)
        
        self.logger.info(f"Split into {len(parts)} parts: {parts}")
        
        if len(parts) != 2:
            self.logger.warning(f"Expected 2 parts (forward - reverse), got {len(parts)}")
            return None, None
        
        forward_part = parts[0].strip()
        reverse_part = parts[1].strip()
        
        self.logger.info(f"Forward part: {forward_part}")
        self.logger.info(f"Reverse part: {reverse_part}")
        
        # Extract leading coefficient from each part
        k_f = self._extract_leading_coefficient(forward_part)
        k_r = self._extract_leading_coefficient(reverse_part)
        
        self.logger.info(f"Extracted k_f={k_f}, k_r={k_r}")
        
        if k_f is not None and k_r is not None and k_r > 0:
            self.logger.info(f"Successfully parsed net mass action: k_f={k_f}, k_r={k_r}")
            return k_f, k_r
        
        self.logger.warning(f"Failed to extract valid rate constants: k_f={k_f}, k_r={k_r}")
        return None, None
    
    def _extract_leading_coefficient(self, expr: str) -> Optional[float]:
        """Extract leading numerical coefficient from expression.
        
        Examples:
            "1e6*[ATP]*[H2O]" → 1e6
            "10.0*ATP*H2O" → 10.0
            "0.5*[A]" → 0.5
            "[ATP]" → 1.0 (implicit)
            "ATP" → 1.0 (implicit)
        
        Args:
            expr: Expression string
            
        Returns:
            Coefficient as float or None
        """
        expr = expr.strip()
        
        # Pattern: optional number (with scientific notation) followed by *
        match = re.match(r'^([+\-]?\d+\.?\d*(?:[eE][+\-]?\d+)?)\s*\*', expr)
        
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        
        # If no explicit coefficient, check if it starts with species name (implicit 1.0)
        # Matches: [Species] or Species (word characters)
        if expr.startswith('[') or re.match(r'^\w+', expr):
            return 1.0
        
        return None
    
    def _parse_explicit_constants(self, rate_func: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse explicit k_f and k_r symbols.
        
        Patterns:
            "k_f=1e6, k_r=1e3"
            "k_forward=1e6, k_reverse=1e3"
            "kf=1e6, kr=1e3"
        
        Args:
            rate_func: Rate function string
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        k_f = None
        k_r = None
        
        # Try various patterns for forward rate
        for pattern in [r'k_f\s*=\s*([\d.eE+\-]+)', r'k_forward\s*=\s*([\d.eE+\-]+)', r'kf\s*=\s*([\d.eE+\-]+)']:
            match = re.search(pattern, rate_func, re.IGNORECASE)
            if match:
                try:
                    k_f = float(match.group(1))
                    break
                except ValueError:
                    pass
        
        # Try various patterns for reverse rate
        for pattern in [r'k_r\s*=\s*([\d.eE+\-]+)', r'k_reverse\s*=\s*([\d.eE+\-]+)', r'kr\s*=\s*([\d.eE+\-]+)']:
            match = re.search(pattern, rate_func, re.IGNORECASE)
            if match:
                try:
                    k_r = float(match.group(1))
                    break
                except ValueError:
                    pass
        
        if k_f is not None and k_r is not None and k_r > 0:
            self.logger.debug(f"Parsed explicit constants: k_f={k_f}, k_r={k_r}")
            return k_f, k_r
        
        return None, None
    
    def _parse_catalog_function(self, rate_func: str) -> Tuple[Optional[float], Optional[float]]:
        """Parse catalog function calls.
        
        Patterns:
            "reversible_mass_action(1e6, 1e3, [A], [B], [C])"
            "michaelis_menten_reversible(Vf=1e6, Vr=1e3, ...)"
        
        Args:
            rate_func: Rate function string
            
        Returns:
            Tuple of (k_forward, k_reverse) or (None, None)
        """
        # Pattern: function_name(args)
        match = re.match(r'(\w+)\s*\((.*)\)', rate_func)
        
        if not match:
            return None, None
        
        func_name = match.group(1).lower()
        args_str = match.group(2)
        
        # Handle reversible_mass_action(k_f, k_r, ...)
        if 'reversible' in func_name and 'mass' in func_name:
            # Extract first two numeric arguments
            numbers = re.findall(r'([\d.eE+\-]+)', args_str)
            if len(numbers) >= 2:
                try:
                    k_f = float(numbers[0])
                    k_r = float(numbers[1])
                    if k_r > 0:
                        self.logger.debug(f"Parsed catalog function: k_f={k_f}, k_r={k_r}")
                        return k_f, k_r
                except ValueError:
                    pass
        
        # Handle named parameters: Vf=..., Vr=...
        vf_match = re.search(r'[Vv]f?\s*=\s*([\d.eE+\-]+)', args_str)
        vr_match = re.search(r'[Vv]r?\s*=\s*([\d.eE+\-]+)', args_str)
        
        if vf_match and vr_match:
            try:
                k_f = float(vf_match.group(1))
                k_r = float(vr_match.group(1))
                if k_r > 0:
                    self.logger.debug(f"Parsed named parameters: k_f={k_f}, k_r={k_r}")
                    return k_f, k_r
            except ValueError:
                pass
        
        return None, None
    
    def is_reversible(self, transition) -> bool:
        """Check if transition is reversible (has both forward and reverse components).
        
        Args:
            transition: Transition object
            
        Returns:
            True if reversible, False otherwise
        """
        t_id = getattr(transition, 'id', 'unknown')
        self.logger.info(f"Checking reversibility for transition {t_id}")
        
        # Check attributes
        if hasattr(transition, 'rate_forward') and hasattr(transition, 'rate_reverse'):
            rate_reverse = getattr(transition, 'rate_reverse', None)
            self.logger.info(f"  Found rate_reverse attribute: {rate_reverse}")
            if rate_reverse:
                try:
                    if float(rate_reverse) > 0:
                        self.logger.info(f"  → REVERSIBLE (rate_reverse={rate_reverse})")
                        return True
                except (ValueError, TypeError):
                    pass
        
        # Check properties dictionary (might be None)
        properties = getattr(transition, 'properties', None)
        if properties and isinstance(properties, dict):
            self.logger.info(f"  Checking properties dict: {list(properties.keys())}")
            if properties.get('is_reversible'):
                self.logger.info("  → REVERSIBLE (is_reversible flag)")
                return True
            
            k_r = properties.get('k_reverse')
            if k_r is not None:
                try:
                    if float(k_r) > 0:
                        self.logger.info(f"  → REVERSIBLE (k_reverse in properties={k_r})")
                        return True
                except (ValueError, TypeError):
                    pass
        
        # Check rate function (check both attribute and properties)
        rate_func = None
        if hasattr(transition, 'rate_function'):
            rate_func = getattr(transition, 'rate_function', None)
            if rate_func:
                rate_func = str(rate_func)

                self.logger.info(f"  Found rate_function attribute: {rate_func}")
        
        # Also check in properties if not found as attribute
        if not rate_func and properties and isinstance(properties, dict):
            rate_func = properties.get('rate_function')
            if rate_func:
                rate_func = str(rate_func)

                self.logger.info(f"  Found rate_function in properties: {rate_func}")
        
        if rate_func:
            # Simple heuristic: contains minus sign (net rate) or explicit k_r
            if '-' in rate_func or 'k_r' in rate_func.lower() or 'reverse' in rate_func.lower():
                self.logger.info("  → REVERSIBLE (rate_function contains '-' or 'k_r')")
                return True
        

        self.logger.info("  → NOT REVERSIBLE")
        return False
        
        # Also check in properties if not found as attribute
        if not rate_func and properties and isinstance(properties, dict):
            rate_func = properties.get('rate_function')
            if rate_func:
                rate_func = str(rate_func)
        
        if rate_func:
            # Simple heuristic: contains minus sign (net rate) or explicit k_r
            if '-' in rate_func or 'k_r' in rate_func.lower() or 'reverse' in rate_func.lower():
                return True
        
        return False
