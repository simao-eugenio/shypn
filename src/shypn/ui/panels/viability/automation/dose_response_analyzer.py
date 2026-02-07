#!/usr/bin/env python3
"""Dose-Response Curve Fitting and Analysis.

Implements 4-parameter logistic (Hill equation) curve fitting for
dose-response relationships, commonly used in drug discovery for
calculating IC50/EC50 values.

Author: Simão Eugénio
Date: January 23, 2025
"""

import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import t as t_dist


class DoseResponseAnalyzer:
    """Analyze dose-response relationships with curve fitting.
    
    Uses 4-parameter logistic equation (Hill equation):
        Y = Bottom + (Top - Bottom) / (1 + 10^((LogIC50 - X) * HillSlope))
    
    Where:
        - X: log10(dose)
        - Y: response (e.g., viability, deadlock rate)
        - Bottom: minimum response (lower asymptote)
        - Top: maximum response (upper asymptote)
        - LogIC50: log10 of IC50 (dose producing 50% response)
        - HillSlope: steepness of curve (negative for inhibition)
    
    Example:
        >>> doses = [0.1, 1, 10, 100, 1000]  # µM
        >>> responses = [95, 90, 50, 10, 5]  # % viability
        >>> analyzer = DoseResponseAnalyzer(doses, responses)
        >>> analyzer.fit()
        >>> print(f"IC50 = {analyzer.ic50:.2f} µM")
        >>> print(f"Hill slope = {analyzer.hill_slope:.2f}")
    """
    
    def __init__(self, doses, responses):
        """Initialize dose-response analyzer.
        
        Args:
            doses: Array-like of dose values (e.g., concentrations in µM)
            responses: Array-like of response values (e.g., viability %)
        
        Raises:
            ValueError: If doses and responses have different lengths or < 4 points
        """
        self.doses = np.array(doses, dtype=float)
        self.responses = np.array(responses, dtype=float)
        
        if len(self.doses) != len(self.responses):
            raise ValueError(f"Doses ({len(self.doses)}) and responses ({len(self.responses)}) must have same length")
        
        if len(self.doses) < 4:
            raise ValueError(f"Need at least 4 data points for curve fitting (got {len(self.doses)})")
        
        # Filter out invalid values (NaN, Inf)
        valid_mask = np.isfinite(self.doses) & np.isfinite(self.responses)
        self.doses = self.doses[valid_mask]
        self.responses = self.responses[valid_mask]
        
        if len(self.doses) < 4:
            raise ValueError("After filtering invalid values, need at least 4 valid data points")
        
        # Fit parameters (populated by fit())
        self.bottom = None
        self.top = None
        self.log_ic50 = None
        self.hill_slope = None
        
        # Derived values
        self.ic50 = None
        self.r_squared = None
        self.std_errors = None
        self.confidence_intervals = None
        
        # Fit status
        self.is_fitted = False
    
    @staticmethod
    def hill_equation(x, bottom, top, log_ic50, hill_slope):
        """4-parameter logistic (Hill equation).
        
        Args:
            x: log10(dose) values
            bottom: Minimum response (lower asymptote)
            top: Maximum response (upper asymptote)
            log_ic50: log10(IC50)
            hill_slope: Hill slope (negative for inhibition)
        
        Returns:
            Predicted response values
        """
        return bottom + (top - bottom) / (1 + 10**((log_ic50 - x) * hill_slope))
    
    def fit(self, initial_guess=None, bounds=None):
        """Fit 4-parameter logistic curve to dose-response data.
        
        Args:
            initial_guess: Optional (bottom, top, log_ic50, hill_slope) initial values
            bounds: Optional ((min_bottom, min_top, min_log_ic50, min_hill_slope),
                            (max_bottom, max_top, max_log_ic50, max_hill_slope))
        
        Returns:
            self (for method chaining)
        
        Raises:
            RuntimeError: If curve fitting fails
        """
        # Convert doses to log scale for fitting
        # Handle zero doses by adding small epsilon to avoid log10(0) = -inf
        epsilon = 1e-10
        self.safe_doses = np.maximum(self.doses, epsilon)
        log_doses = np.log10(self.safe_doses)
        
        # Auto-detect initial guess if not provided
        if initial_guess is None:
            bottom_guess = np.min(self.responses)
            top_guess = np.max(self.responses)
            log_ic50_guess = np.median(log_doses)
            hill_slope_guess = -1.0  # Typical inhibition curve
            initial_guess = (bottom_guess, top_guess, log_ic50_guess, hill_slope_guess)
        
        # Set reasonable bounds if not provided
        if bounds is None:
            # Calculate response range
            response_range = np.max(self.responses) - np.min(self.responses)
            response_min = np.min(self.responses)
            response_max = np.max(self.responses)
            
            # Handle edge case: all responses are identical
            if response_range < 1e-6:  # Essentially zero
                # Use arbitrary but reasonable bounds around constant response
                response_range = max(abs(response_min), 1.0)  # At least 1.0 unit range
                bottom_min = response_min - response_range
                bottom_max = response_min + 0.5 * response_range
                top_min = response_min + 0.5 * response_range
                top_max = response_min + response_range
            else:
                # Normal case: allow bottom/top to vary ±50% from data range
                bottom_min = response_min - 0.5 * response_range
                bottom_max = response_min + 0.5 * response_range
                top_min = response_max - 0.5 * response_range
                top_max = response_max + 0.5 * response_range
            
            # Ensure ordering: bottom_min < bottom_max < top_min < top_max
            # Add minimum separation of 1e-3 between adjacent bounds
            min_sep = 1e-3
            if bottom_max >= top_min:
                # Adjust to ensure bottom_max < top_min
                midpoint = (bottom_max + top_min) / 2
                bottom_max = midpoint - min_sep
                top_min = midpoint + min_sep
            
            # Allow log_ic50 to vary across dose range
            log_ic50_min = np.min(log_doses) - 1
            log_ic50_max = np.max(log_doses) + 1
            
            # Hill slope typically in range [-5, 5]
            hill_slope_min = -5.0
            hill_slope_max = 5.0
            
            bounds = (
                [bottom_min, top_min, log_ic50_min, hill_slope_min],
                [bottom_max, top_max, log_ic50_max, hill_slope_max]
            )
        
        # Ensure initial guess is within bounds (clamp to valid range)
        if initial_guess is not None and bounds is not None:
            lower_bounds, upper_bounds = bounds
            initial_guess = tuple([
                max(lower_bounds[i], min(upper_bounds[i], initial_guess[i]))
                for i in range(len(initial_guess))
            ])
        
        try:
            # Perform curve fitting
            popt, pcov = curve_fit(
                self.hill_equation,
                log_doses,
                self.responses,
                p0=initial_guess,
                bounds=bounds,
                maxfev=10000
            )
            
            # Extract parameters
            self.bottom, self.top, self.log_ic50, self.hill_slope = popt
            self.ic50 = 10 ** self.log_ic50
            
            # Calculate R-squared
            residuals = self.responses - self.hill_equation(log_doses, *popt)
            ss_res = np.sum(residuals ** 2)
            ss_tot = np.sum((self.responses - np.mean(self.responses)) ** 2)
            self.r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            
            # Calculate standard errors and confidence intervals
            self._calculate_uncertainties(pcov, len(log_doses))
            
            self.is_fitted = True
            
        except Exception as e:
            raise RuntimeError(f"Dose-response fitting failed: {e}")
        
        return self
    
    def _calculate_uncertainties(self, pcov, n_points):
        """Calculate standard errors and 95% confidence intervals.
        
        Args:
            pcov: Covariance matrix from curve_fit
            n_points: Number of data points
        """
        # Standard errors = sqrt of diagonal of covariance matrix
        self.std_errors = np.sqrt(np.diag(pcov))
        
        # 95% confidence intervals using t-distribution
        # Degrees of freedom = n_points - 4 parameters
        dof = max(1, n_points - 4)
        t_value = t_dist.ppf(0.975, dof)  # 97.5th percentile for two-tailed test
        
        # Calculate CIs for each parameter
        self.confidence_intervals = {
            'bottom': (self.bottom - t_value * self.std_errors[0],
                      self.bottom + t_value * self.std_errors[0]),
            'top': (self.top - t_value * self.std_errors[1],
                   self.top + t_value * self.std_errors[1]),
            'log_ic50': (self.log_ic50 - t_value * self.std_errors[2],
                        self.log_ic50 + t_value * self.std_errors[2]),
            'hill_slope': (self.hill_slope - t_value * self.std_errors[3],
                          self.hill_slope + t_value * self.std_errors[3])
        }
        
        # IC50 confidence interval (convert from log space with overflow protection)
        log_ic50_lower, log_ic50_upper = self.confidence_intervals['log_ic50']
        # Clamp to prevent overflow (10^308 is near float64 max)
        log_ic50_lower = np.clip(log_ic50_lower, -300, 300)
        log_ic50_upper = np.clip(log_ic50_upper, -300, 300)
        self.confidence_intervals['ic50'] = (10 ** log_ic50_lower, 10 ** log_ic50_upper)
    
    def predict(self, doses):
        """Predict responses for given doses using fitted curve.
        
        Args:
            doses: Array-like of dose values
        
        Returns:
            Predicted response values
        
        Raises:
            RuntimeError: If fit() has not been called
        """
        if not self.is_fitted:
            raise RuntimeError("Must call fit() before predict()")
        
        # Handle zero doses with epsilon
        epsilon = 1e-10
        safe_input_doses = np.maximum(np.array(doses, dtype=float), epsilon)
        log_doses = np.log10(safe_input_doses)
        return self.hill_equation(log_doses, self.bottom, self.top, self.log_ic50, self.hill_slope)
    
    def get_summary(self):
        """Get summary of fit parameters with uncertainties.
        
        Returns:
            dict: Summary statistics including IC50, hill_slope, R², confidence intervals
        
        Raises:
            RuntimeError: If fit() has not been called
        """
        if not self.is_fitted:
            raise RuntimeError("Must call fit() before get_summary()")
        
        ic50_lower, ic50_upper = self.confidence_intervals['ic50']
        hill_lower, hill_upper = self.confidence_intervals['hill_slope']
        
        return {
            'ic50': self.ic50,
            'ic50_ci': (ic50_lower, ic50_upper),
            'ic50_stderr': (ic50_upper - ic50_lower) / (2 * 1.96),  # Approximate SE from CI
            'hill_slope': self.hill_slope,
            'hill_slope_ci': (hill_lower, hill_upper),
            'hill_slope_stderr': self.std_errors[3],
            'bottom': self.bottom,
            'top': self.top,
            'r_squared': self.r_squared,
            'n_points': len(self.doses)
        }
    
    def generate_smooth_curve(self, n_points=100):
        """Generate smooth dose-response curve for plotting.
        
        Args:
            n_points: Number of points in smooth curve
        
        Returns:
            (doses, responses): Tuple of arrays for plotting
        
        Raises:
            RuntimeError: If fit() has not been called
        """
        if not self.is_fitted:
            raise RuntimeError("Must call fit() before generate_smooth_curve()")
        
        # Generate log-spaced doses covering data range + margins
        # Use safe_doses (with epsilon) to avoid log10(0)
        log_doses_min = np.log10(np.min(self.safe_doses)) - 0.5
        log_doses_max = np.log10(np.max(self.safe_doses)) + 0.5
        log_doses_smooth = np.linspace(log_doses_min, log_doses_max, n_points)
        # Clamp to prevent overflow
        log_doses_smooth = np.clip(log_doses_smooth, -300, 300)
        doses_smooth = 10 ** log_doses_smooth
        
        # Predict responses
        responses_smooth = self.predict(doses_smooth)
        
        return doses_smooth, responses_smooth
