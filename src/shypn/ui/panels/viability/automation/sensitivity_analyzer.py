#!/usr/bin/env python3
"""Sensitivity Analysis Tools for Parameter Space Exploration.

Implements Latin Hypercube Sampling (LHS) and Partial Rank Correlation
Coefficient (PRCC) analysis for identifying key parameters that influence
model outcomes.

Author: Simão Eugénio
Date: January 23, 2025
"""

import numpy as np
from scipy import stats
from scipy.stats import qmc


class SensitivityAnalyzer:
    """Perform sensitivity analysis using Latin Hypercube Sampling and PRCC.
    
    Sensitivity analysis identifies which parameters have the strongest
    influence on model outputs. Uses:
    - Latin Hypercube Sampling (LHS) for efficient parameter space exploration
    - Partial Rank Correlation Coefficient (PRCC) for quantifying parameter influence
    
    Example:
        >>> # Define parameter ranges
        >>> param_ranges = {
        ...     'ATP': (10, 1000),      # Min, max
        ...     'T4_rate': (0.5, 3.0),
        ...     'Noise': (0.0, 0.5)
        ... }
        >>> 
        >>> analyzer = SensitivityAnalyzer(param_ranges, n_samples=100)
        >>> samples = analyzer.generate_lhs_samples()
        >>> 
        >>> # Run simulations with samples, collect outputs
        >>> outputs = run_experiments(samples)  # User-defined function
        >>> 
        >>> prcc_results = analyzer.compute_prcc(samples, outputs)
        >>> analyzer.plot_tornado(prcc_results)
    """
    
    def __init__(self, parameter_ranges, n_samples=100, seed=None):
        """Initialize sensitivity analyzer.
        
        Args:
            parameter_ranges: Dictionary mapping parameter names to (min, max) tuples
                             e.g., {'ATP': (10, 1000), 'T4_rate': (0.5, 3.0)}
            n_samples: Number of LHS samples to generate (default 100)
            seed: Random seed for reproducibility (optional)
        
        Raises:
            ValueError: If parameter_ranges is empty or n_samples < 10
        """
        self.parameter_ranges = parameter_ranges
        self.param_names = list(parameter_ranges.keys())
        self.n_params = len(self.param_names)
        self.n_samples = n_samples
        self.seed = seed
        
        if self.n_params == 0:
            raise ValueError("parameter_ranges cannot be empty")
        
        if n_samples < 10:
            raise ValueError(f"n_samples must be at least 10 (got {n_samples})")
        
        # Recommended: n_samples >= 10 * n_params for reliable PRCC
        if n_samples < 10 * self.n_params:
            print(f"[WARNING] Recommended n_samples >= {10 * self.n_params} for {self.n_params} parameters")
    
    def generate_lhs_samples(self):
        """Generate Latin Hypercube Sampling samples.
        
        LHS ensures uniform coverage of parameter space by dividing each
        parameter range into n_samples intervals and sampling once per interval.
        
        Returns:
            dict: Dictionary mapping parameter names to numpy arrays of sample values
                 Each array has shape (n_samples,)
        
        Example:
            >>> samples = analyzer.generate_lhs_samples()
            >>> samples['ATP']  # Array of 100 ATP values between min and max
        """
        # Use scipy's qmc.LatinHypercube for high-quality sampling
        sampler = qmc.LatinHypercube(d=self.n_params, seed=self.seed)
        
        # Generate samples in unit hypercube [0, 1]^d
        unit_samples = sampler.random(n=self.n_samples)
        
        # Scale to actual parameter ranges
        samples = {}
        for i, param_name in enumerate(self.param_names):
            min_val, max_val = self.parameter_ranges[param_name]
            scaled_samples = qmc.scale(unit_samples[:, i:i+1], [min_val], [max_val])
            samples[param_name] = scaled_samples.flatten()
        
        return samples
    
    def compute_prcc(self, samples, outputs, output_name='Output'):
        """Compute Partial Rank Correlation Coefficients.
        
        PRCC measures the strength of monotonic relationship between each
        parameter and the output, while controlling for other parameters.
        
        Uses rank-based correlation (Spearman) to handle non-linear relationships.
        
        Args:
            samples: Dictionary of parameter samples (from generate_lhs_samples)
            outputs: Array of output values corresponding to each sample (n_samples,)
            output_name: Name of output metric (for display purposes)
        
        Returns:
            dict: Results containing:
                - prcc_values: Dictionary mapping parameter names to PRCC values
                - p_values: Dictionary mapping parameter names to p-values
                - significant: Dictionary mapping parameter names to bool (p < 0.05)
                - ranked_params: List of (param_name, prcc_value) tuples sorted by |PRCC|
                - output_name: Name of output metric
        
        Raises:
            ValueError: If samples and outputs have mismatched lengths
        """
        outputs = np.array(outputs, dtype=float)
        
        # Validate input lengths
        n_outputs = len(outputs)
        for param_name, param_values in samples.items():
            if len(param_values) != n_outputs:
                raise ValueError(
                    f"Sample length mismatch: {param_name} has {len(param_values)} values "
                    f"but outputs has {n_outputs}"
                )
        
        # Convert samples to matrix (n_samples × n_params)
        X = np.column_stack([samples[name] for name in self.param_names])
        
        # Rank transformation (convert to ranks for Spearman correlation)
        X_ranked = np.column_stack([stats.rankdata(X[:, i]) for i in range(self.n_params)])
        y_ranked = stats.rankdata(outputs)
        
        # Compute PRCC for each parameter
        prcc_values = {}
        p_values = {}
        significant = {}
        
        for i, param_name in enumerate(self.param_names):
            # PRCC = partial correlation between param and output, controlling for others
            prcc, pval = self._partial_rank_correlation(X_ranked, y_ranked, i)
            
            prcc_values[param_name] = prcc
            p_values[param_name] = pval
            significant[param_name] = pval < 0.05
        
        # Rank parameters by absolute PRCC value
        ranked_params = sorted(
            [(name, prcc_values[name]) for name in self.param_names],
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return {
            'prcc_values': prcc_values,
            'p_values': p_values,
            'significant': significant,
            'ranked_params': ranked_params,
            'output_name': output_name,
            'n_samples': n_outputs
        }
    
    def _partial_rank_correlation(self, X_ranked, y_ranked, param_idx):
        """Compute partial rank correlation for a single parameter.
        
        Uses linear regression approach:
        1. Regress parameter on all other parameters
        2. Regress output on all other parameters
        3. Compute Pearson correlation between residuals
        
        Args:
            X_ranked: Ranked parameter matrix (n_samples × n_params)
            y_ranked: Ranked output vector (n_samples,)
            param_idx: Index of parameter to compute PRCC for
        
        Returns:
            tuple: (prcc_value, p_value)
        """
        n_samples, n_params = X_ranked.shape
        
        if n_params == 1:
            # Only one parameter - PRCC is just Pearson correlation of ranks
            return stats.pearsonr(X_ranked[:, param_idx], y_ranked)
        
        # Get indices of other parameters (exclude current parameter)
        other_indices = [i for i in range(n_params) if i != param_idx]
        
        # Regress parameter on other parameters
        X_other = X_ranked[:, other_indices]
        x_param = X_ranked[:, param_idx]
        
        # Fit linear regression: x_param ~ X_other
        # Using least squares: beta = (X^T X)^{-1} X^T y
        try:
            X_other_with_intercept = np.column_stack([np.ones(n_samples), X_other])
            beta_x = np.linalg.lstsq(X_other_with_intercept, x_param, rcond=None)[0]
            residuals_x = x_param - X_other_with_intercept @ beta_x
        except np.linalg.LinAlgError:
            # Singular matrix - use pseudoinverse
            beta_x = np.linalg.pinv(X_other_with_intercept) @ x_param
            residuals_x = x_param - X_other_with_intercept @ beta_x
        
        # Regress output on other parameters
        try:
            beta_y = np.linalg.lstsq(X_other_with_intercept, y_ranked, rcond=None)[0]
            residuals_y = y_ranked - X_other_with_intercept @ beta_y
        except np.linalg.LinAlgError:
            beta_y = np.linalg.pinv(X_other_with_intercept) @ y_ranked
            residuals_y = y_ranked - X_other_with_intercept @ beta_y
        
        # PRCC = Pearson correlation of residuals
        prcc, pval = stats.pearsonr(residuals_x, residuals_y)
        
        return prcc, pval
    
    def format_prcc_results(self, prcc_results, include_insignificant=True):
        """Format PRCC results as human-readable text.
        
        Args:
            prcc_results: Results from compute_prcc()
            include_insignificant: If False, only show significant parameters
        
        Returns:
            str: Formatted text summary
        """
        lines = []
        lines.append(f"Sensitivity Analysis Results ({prcc_results['output_name']})")
        lines.append(f"Latin Hypercube Sampling: {prcc_results['n_samples']} samples")
        lines.append("")
        lines.append("Partial Rank Correlation Coefficients (PRCC):")
        lines.append("=" * 60)
        
        for param_name, prcc_value in prcc_results['ranked_params']:
            pval = prcc_results['p_values'][param_name]
            is_sig = prcc_results['significant'][param_name]
            
            if not include_insignificant and not is_sig:
                continue
            
            sig_marker = "***" if pval < 0.001 else "**" if pval < 0.01 else "*" if pval < 0.05 else "ns"
            direction = "↑" if prcc_value > 0 else "↓"
            
            lines.append(f"{param_name:20s}  PRCC = {prcc_value:+.4f}  {direction}  p = {pval:.4f} {sig_marker}")
        
        lines.append("")
        lines.append("Interpretation:")
        lines.append("  Positive PRCC: Increasing parameter increases output")
        lines.append("  Negative PRCC: Increasing parameter decreases output")
        lines.append("  |PRCC| close to 1: Strong monotonic relationship")
        lines.append("  *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
        
        return "\n".join(lines)
    
    def get_tornado_plot_data(self, prcc_results, top_n=None):
        """Prepare data for tornado plot visualization.
        
        Args:
            prcc_results: Results from compute_prcc()
            top_n: If specified, return only top N most influential parameters
        
        Returns:
            dict: Data for plotting with keys:
                - param_names: List of parameter names (sorted by |PRCC|)
                - prcc_values: List of PRCC values
                - colors: List of colors (green for positive, red for negative)
                - significant: List of bools indicating significance
        """
        ranked = prcc_results['ranked_params']
        
        if top_n is not None:
            ranked = ranked[:top_n]
        
        param_names = [name for name, _ in ranked]
        prcc_values = [prcc for _, prcc in ranked]
        
        # Color code: positive (green), negative (red), insignificant (gray)
        colors = []
        for name in param_names:
            prcc = prcc_results['prcc_values'][name]
            is_sig = prcc_results['significant'][name]
            
            if not is_sig:
                colors.append('#999999')  # Gray for insignificant
            elif prcc > 0:
                colors.append('#2ca02c')  # Green for positive
            else:
                colors.append('#d62728')  # Red for negative
        
        significant = [prcc_results['significant'][name] for name in param_names]
        
        return {
            'param_names': param_names,
            'prcc_values': prcc_values,
            'colors': colors,
            'significant': significant
        }


class LHSExperimentGenerator:
    """Generate experiment configurations from LHS samples.
    
    Helper class to convert LHS samples into experiment snapshot configurations
    that can be executed by BatchExecutor.
    """
    
    @staticmethod
    def samples_to_experiments(samples, base_snapshot, experiment_manager):
        """Convert LHS samples to experiment snapshots.
        
        Args:
            samples: Dictionary from SensitivityAnalyzer.generate_lhs_samples()
            base_snapshot: Baseline ExperimentSnapshot to clone
            experiment_manager: ExperimentManager instance to add snapshots to
        
        Returns:
            list: List of (snapshot_name, snapshot_index) tuples for queue
        """
        n_samples = len(next(iter(samples.values())))
        param_names = list(samples.keys())
        
        experiments = []
        
        for i in range(n_samples):
            # Build name from parameter values
            name_parts = []
            for param_name in param_names:
                value = samples[param_name][i]
                
                # Format value nicely
                if isinstance(value, float):
                    if value.is_integer():
                        value_str = str(int(value))
                    else:
                        value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                
                # Abbreviate parameter name if long
                abbrev = param_name[:6] if len(param_name) > 8 else param_name
                name_parts.append(f"{abbrev}={value_str}")
            
            snapshot_name = f"LHS_{i+1}_" + "_".join(name_parts[:3])  # Limit to 3 params in name
            
            # Create snapshot
            baseline_count = len(experiment_manager.snapshots)
            snapshot = experiment_manager.add_snapshot(snapshot_name)
            # Copy values from base snapshot
            snapshot.place_markings = base_snapshot.place_markings.copy()
            snapshot.arc_weights = base_snapshot.arc_weights.copy()
            snapshot.transition_rates = base_snapshot.transition_rates.copy()
            snapshot.notes = base_snapshot.notes
            
            # Apply parameter values
            # Note: This requires knowledge of parameter types (place/transition/arc)
            # For now, assume parameters are stored in a way that can be applied
            # This would need to be customized based on actual parameter structure
            
            experiments.append((snapshot_name, baseline_count))
        
        return experiments
