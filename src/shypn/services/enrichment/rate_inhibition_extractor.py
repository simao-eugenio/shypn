"""Rate Function Inhibition Extractor.

Extracts Hill inhibition terms from rate functions and converts them to
inhibitor arcs for signal hierarchy compliance.

This ensures:
- Inhibition logic is represented as arc-level topology (inhibitor arcs)
- Threshold functions on arcs (not buried in rate expressions)
- Proper signal hierarchy analysis
- Separation of concerns: topology vs kinetics

Example:
    Rate: "vmax * S / (Km + S) / (1 + (I / Ki)^n)"
    
    Extracted:
    - Inhibitor place: I
    - Inhibitor arc: I ⊣ Transition
    - Arc threshold: Ki
    - Hill coefficient (n): stored in arc metadata
    - Simplified rate: "vmax * S / (Km + S)"
"""

import re
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class InhibitionTerm:
    """Extracted inhibition term from rate function.
    
    Attributes:
        inhibitor_place: Name of inhibiting place (e.g., "ATP", "P5")
        ki_value: Inhibition constant (Ki)
        hill_coefficient: Hill coefficient (n) for cooperativity
        original_term: Original inhibition term string
        term_pattern: Pattern type ('hill_denominator', 'hill_fraction', 'competitive')
    """
    inhibitor_place: str
    ki_value: float
    hill_coefficient: float = 1.0
    original_term: str = ""
    term_pattern: str = ""


class RateInhibitionExtractor:
    """Extracts Hill inhibition terms from rate functions.
    
    Detects common inhibition patterns:
    1. Hill denominator: "/ (1 + (I/Ki)^n)" or "/ (1.0 + (I/Ki)**n)"
    2. Hill fraction: "/ (1 + I^n/Ki^n)"
    3. Competitive inhibition: "Km*(1 + I/Ki)"
    
    Usage:
        extractor = RateInhibitionExtractor()
        inhibition, simplified_rate = extractor.extract(rate_function)
        if inhibition:
            # Create inhibitor arc with threshold=Ki and metadata['hill_coefficient']=n
            pass
    """
    
    # Pattern 1: Hill inhibition in denominator - / (1 + (I/Ki)^n)
    HILL_DENOM_PATTERN = r'/\s*\(\s*1(?:\.0)?\s*\+\s*\(([A-Za-z_][A-Za-z0-9_]*)\s*/\s*([\d.]+)\)\s*\*\*\s*([\d.]+)\s*\)'
    
    # Pattern 2: Alternative Hill - / (1 + I^n/Ki^n)
    HILL_ALT_PATTERN = r'/\s*\(\s*1(?:\.0)?\s*\+\s*([A-Za-z_][A-Za-z0-9_]*)\s*\*\*\s*([\d.]+)\s*/\s*([\d.]+)\s*\*\*\s*[\d.]+\s*\)'
    
    # Pattern 3: Power operator alternatives - ^ or **
    HILL_CARET_PATTERN = r'/\s*\(\s*1(?:\.0)?\s*\+\s*\(([A-Za-z_][A-Za-z0-9_]*)\s*/\s*([\d.]+)\)\s*\^\s*([\d.]+)\s*\)'
    
    # Pattern 4: Competitive inhibition in Km term - Km*(1 + I/Ki)
    COMPETITIVE_PATTERN = r'([A-Za-z_][A-Za-z0-9_]*)\s*\*\s*\(\s*1(?:\.0)?\s*\+\s*([A-Za-z_][A-Za-z0-9_]*)\s*/\s*([\d.]+)\s*\)'
    
    def extract(self, rate_function: str) -> Tuple[Optional[InhibitionTerm], str]:
        """Extract inhibition term from rate function.
        
        Args:
            rate_function: Rate function string
        
        Returns:
            Tuple of (InhibitionTerm or None, simplified_rate_function)
            If no inhibition found, returns (None, original_rate_function)
        """
        if not rate_function or not isinstance(rate_function, str):
            return None, rate_function
        
        # Try Hill denominator pattern first (most common)
        inhibition, simplified = self._extract_hill_denominator(rate_function)
        if inhibition:
            return inhibition, simplified
        
        # Try alternative Hill pattern
        inhibition, simplified = self._extract_hill_alternative(rate_function)
        if inhibition:
            return inhibition, simplified
        
        # Try caret operator (^) variant
        inhibition, simplified = self._extract_hill_caret(rate_function)
        if inhibition:
            return inhibition, simplified
        
        # Try competitive inhibition
        inhibition, simplified = self._extract_competitive(rate_function)
        if inhibition:
            return inhibition, simplified
        
        return None, rate_function
    
    def _extract_hill_denominator(self, rate_func: str) -> Tuple[Optional[InhibitionTerm], str]:
        """Extract Hill inhibition from denominator: / (1 + (I/Ki)^n)
        
        Example: "vmax * S / (Km + S) / (1.0 + (ATP / 2.5)**4)"
        """
        match = re.search(self.HILL_DENOM_PATTERN, rate_func)
        if not match:
            return None, rate_func
        
        inhibitor = match.group(1)
        ki = float(match.group(2))
        n = float(match.group(3))
        original_term = match.group(0)
        
        # Remove inhibition term from rate function
        simplified = rate_func.replace(original_term, '')
        simplified = self._cleanup_expression(simplified)
        
        inhibition = InhibitionTerm(
            inhibitor_place=inhibitor,
            ki_value=ki,
            hill_coefficient=n,
            original_term=original_term,
            term_pattern='hill_denominator'
        )
        
        logger.debug(
            f"Extracted Hill inhibition: {inhibitor} with Ki={ki}, n={n}"
        )
        
        return inhibition, simplified
    
    def _extract_hill_alternative(self, rate_func: str) -> Tuple[Optional[InhibitionTerm], str]:
        """Extract alternative Hill form: / (1 + I^n/Ki^n)"""
        match = re.search(self.HILL_ALT_PATTERN, rate_func)
        if not match:
            return None, rate_func
        
        inhibitor = match.group(1)
        n = float(match.group(2))
        ki_n = float(match.group(3))
        ki = ki_n ** (1.0 / n)  # Extract Ki from Ki^n
        original_term = match.group(0)
        
        simplified = rate_func.replace(original_term, '')
        simplified = self._cleanup_expression(simplified)
        
        inhibition = InhibitionTerm(
            inhibitor_place=inhibitor,
            ki_value=ki,
            hill_coefficient=n,
            original_term=original_term,
            term_pattern='hill_alternative'
        )
        
        return inhibition, simplified
    
    def _extract_hill_caret(self, rate_func: str) -> Tuple[Optional[InhibitionTerm], str]:
        """Extract Hill with caret operator: / (1 + (I/Ki)^n)"""
        match = re.search(self.HILL_CARET_PATTERN, rate_func)
        if not match:
            return None, rate_func
        
        inhibitor = match.group(1)
        ki = float(match.group(2))
        n = float(match.group(3))
        original_term = match.group(0)
        
        simplified = rate_func.replace(original_term, '')
        simplified = self._cleanup_expression(simplified)
        
        inhibition = InhibitionTerm(
            inhibitor_place=inhibitor,
            ki_value=ki,
            hill_coefficient=n,
            original_term=original_term,
            term_pattern='hill_caret'
        )
        
        return inhibition, simplified
    
    def _extract_competitive(self, rate_func: str) -> Tuple[Optional[InhibitionTerm], str]:
        """Extract competitive inhibition: Km*(1 + I/Ki)
        
        Example: "vmax * S / (Km*(1 + ATP/2.0) + S)"
        """
        match = re.search(self.COMPETITIVE_PATTERN, rate_func)
        if not match:
            return None, rate_func
        
        km_var = match.group(1)
        inhibitor = match.group(2)
        ki = float(match.group(3))
        original_term = match.group(0)
        
        # Replace with just Km (inhibition moved to arc)
        simplified = rate_func.replace(original_term, km_var)
        
        inhibition = InhibitionTerm(
            inhibitor_place=inhibitor,
            ki_value=ki,
            hill_coefficient=1.0,  # Competitive is non-cooperative
            original_term=original_term,
            term_pattern='competitive'
        )
        
        logger.debug(
            f"Extracted competitive inhibition: {inhibitor} with Ki={ki}"
        )
        
        return inhibition, simplified
    
    def _cleanup_expression(self, expr: str) -> str:
        """Clean up expression after term removal.
        
        Removes:
        - Double operators (e.g., "* /" becomes "*")
        - Trailing operators
        - Extra whitespace
        """
        # Remove double division
        expr = re.sub(r'/\s*/', '/', expr)
        
        # Remove trailing operators
        expr = re.sub(r'[*/]\s*$', '', expr)
        
        # Clean up whitespace
        expr = re.sub(r'\s+', ' ', expr).strip()
        
        return expr
    
    def extract_all(self, rate_function: str) -> Tuple[List[InhibitionTerm], str]:
        """Extract all inhibition terms from rate function.
        
        Handles multiple inhibitors in same rate function.
        
        Args:
            rate_function: Rate function string
        
        Returns:
            Tuple of (list of InhibitionTerms, simplified_rate_function)
        """
        inhibitions = []
        simplified = rate_function
        
        # Keep extracting until no more inhibitions found
        while True:
            inhibition, simplified = self.extract(simplified)
            if not inhibition:
                break
            inhibitions.append(inhibition)
        
        return inhibitions, simplified
