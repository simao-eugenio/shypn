#!/usr/bin/env python3
"""Statistical Comparison Tools for Experiment Results.

Implements automated statistical tests for comparing multiple experimental
conditions, including ANOVA and post-hoc tests commonly used in biological
and pharmaceutical research.

Author: Simão Eugénio
Date: January 23, 2025
"""

import numpy as np
from scipy import stats


class StatisticalComparator:
    """Compare multiple experimental groups with statistical tests.
    
    Provides one-way ANOVA for detecting differences between groups
    and Tukey's HSD (Honestly Significant Difference) test for pairwise
    post-hoc comparisons.
    
    Example:
        >>> groups = {
        ...     'Control': [45.2, 48.1, 46.3, 47.8],
        ...     'Treatment_A': [62.5, 65.2, 63.1, 64.8],
        ...     'Treatment_B': [58.3, 59.7, 57.9, 60.2]
        ... }
        >>> comparator = StatisticalComparator(groups)
        >>> anova_result = comparator.one_way_anova()
        >>> print(f"F-statistic: {anova_result['f_statistic']:.3f}")
        >>> print(f"p-value: {anova_result['p_value']:.4f}")
        >>> 
        >>> if anova_result['significant']:
        ...     tukey_result = comparator.tukey_hsd()
        ...     for comparison, stats in tukey_result['comparisons'].items():
        ...         print(f"{comparison}: p={stats['p_value']:.4f}")
    """
    
    def __init__(self, groups):
        """Initialize statistical comparator.
        
        Args:
            groups: Dictionary mapping group names to lists of values
                   e.g., {'Control': [1.2, 1.5, 1.3], 'Treatment': [2.1, 2.3, 2.0]}
        
        Raises:
            ValueError: If fewer than 2 groups or groups have insufficient data
        """
        self.groups = groups
        self.group_names = list(groups.keys())
        self.group_data = [np.array(groups[name], dtype=float) for name in self.group_names]
        
        # Validation
        if len(self.group_names) < 2:
            raise ValueError(f"Need at least 2 groups for comparison (got {len(self.group_names)})")
        
        # Check each group has at least 2 values
        for name, data in zip(self.group_names, self.group_data):
            if len(data) < 2:
                raise ValueError(f"Group '{name}' has only {len(data)} value(s), need at least 2")
        
        # Filter out NaN/Inf values
        self.group_data = [data[np.isfinite(data)] for data in self.group_data]
        
        # Check if any groups became empty after filtering
        for name, data in zip(self.group_names, self.group_data):
            if len(data) < 2:
                raise ValueError(f"Group '{name}' has insufficient valid data after filtering")
    
    def one_way_anova(self, alpha=0.05):
        """Perform one-way ANOVA to test for differences between groups.
        
        Tests null hypothesis: All group means are equal
        Alternative hypothesis: At least one group mean differs
        
        Args:
            alpha: Significance level (default 0.05)
        
        Returns:
            dict: Results containing:
                - f_statistic: F-statistic value
                - p_value: Probability under null hypothesis
                - significant: True if p < alpha
                - df_between: Degrees of freedom between groups
                - df_within: Degrees of freedom within groups
                - group_means: Mean for each group
                - group_stds: Standard deviation for each group
                - group_ns: Sample size for each group
        """
        # Perform ANOVA using scipy.stats.f_oneway
        f_statistic, p_value = stats.f_oneway(*self.group_data)
        
        # Calculate degrees of freedom
        k = len(self.group_data)  # Number of groups
        n_total = sum(len(data) for data in self.group_data)
        df_between = k - 1
        df_within = n_total - k
        
        # Calculate group statistics
        group_means = [np.mean(data) for data in self.group_data]
        group_stds = [np.std(data, ddof=1) for data in self.group_data]  # Sample std
        group_ns = [len(data) for data in self.group_data]
        
        return {
            'f_statistic': f_statistic,
            'p_value': p_value,
            'significant': p_value < alpha,
            'alpha': alpha,
            'df_between': df_between,
            'df_within': df_within,
            'n_groups': k,
            'n_total': n_total,
            'group_means': dict(zip(self.group_names, group_means)),
            'group_stds': dict(zip(self.group_names, group_stds)),
            'group_ns': dict(zip(self.group_names, group_ns))
        }
    
    def tukey_hsd(self, alpha=0.05):
        """Perform Tukey's HSD post-hoc test for pairwise comparisons.
        
        Should only be called after ANOVA shows significant differences.
        Tests all pairwise comparisons while controlling family-wise error rate.
        
        Args:
            alpha: Significance level (default 0.05)
        
        Returns:
            dict: Results containing:
                - comparisons: Dictionary of pairwise comparisons with:
                    - mean_diff: Difference in means
                    - std_error: Standard error of difference
                    - q_statistic: Studentized range statistic
                    - p_value: Adjusted p-value
                    - significant: True if p < alpha
                    - ci_lower: Lower confidence interval
                    - ci_upper: Upper confidence interval
                - alpha: Significance level used
        """
        from scipy.stats import studentized_range
        
        # Calculate pooled variance (MSE from ANOVA)
        all_data = np.concatenate(self.group_data)
        grand_mean = np.mean(all_data)
        
        # Within-group sum of squares
        ss_within = sum(np.sum((data - np.mean(data))**2) for data in self.group_data)
        
        # Degrees of freedom
        k = len(self.group_data)
        n_total = len(all_data)
        df_within = n_total - k
        
        # Mean square error (pooled variance)
        mse = ss_within / df_within
        
        # Perform all pairwise comparisons
        comparisons = {}
        
        for i in range(len(self.group_names)):
            for j in range(i + 1, len(self.group_names)):
                name_i = self.group_names[i]
                name_j = self.group_names[j]
                data_i = self.group_data[i]
                data_j = self.group_data[j]
                
                # Mean difference
                mean_i = np.mean(data_i)
                mean_j = np.mean(data_j)
                mean_diff = mean_i - mean_j
                
                # Standard error for difference
                n_i = len(data_i)
                n_j = len(data_j)
                se_diff = np.sqrt(mse * (1/n_i + 1/n_j))
                
                # Studentized range statistic (q)
                q_statistic = abs(mean_diff) / (np.sqrt(mse / 2) * np.sqrt(1/n_i + 1/n_j))
                
                # Critical value from studentized range distribution
                # Note: scipy uses (k, df) parameterization
                q_critical = studentized_range.ppf(1 - alpha, k, df_within)
                
                # p-value (approximate using normal approximation for large df)
                if df_within > 30:
                    # Use normal approximation for large df
                    z_score = q_statistic / np.sqrt(2)
                    p_value = 2 * (1 - stats.norm.cdf(z_score))
                else:
                    # Use studentized range distribution
                    p_value = 1 - studentized_range.cdf(q_statistic, k, df_within)
                
                # Confidence interval
                margin = q_critical * se_diff
                ci_lower = mean_diff - margin
                ci_upper = mean_diff + margin
                
                comparison_key = f"{name_i} vs {name_j}"
                comparisons[comparison_key] = {
                    'mean_diff': mean_diff,
                    'std_error': se_diff,
                    'q_statistic': q_statistic,
                    'q_critical': q_critical,
                    'p_value': p_value,
                    'significant': p_value < alpha,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper
                }
        
        return {
            'comparisons': comparisons,
            'alpha': alpha,
            'mse': mse,
            'df_within': df_within
        }
    
    def format_significance(self, p_value):
        """Format p-value with significance stars.
        
        Args:
            p_value: P-value from statistical test
        
        Returns:
            str: Formatted string with stars (*** p<0.001, ** p<0.01, * p<0.05, ns otherwise)
        """
        if p_value < 0.001:
            return f"{p_value:.4f} ***"
        elif p_value < 0.01:
            return f"{p_value:.4f} **"
        elif p_value < 0.05:
            return f"{p_value:.4f} *"
        else:
            return f"{p_value:.4f} ns"
    
    def get_summary(self, include_posthoc=True):
        """Get comprehensive statistical summary.
        
        Args:
            include_posthoc: If True and ANOVA is significant, include Tukey HSD
        
        Returns:
            dict: Complete statistical summary with ANOVA and optional post-hoc tests
        """
        # Run ANOVA
        anova_result = self.one_way_anova()
        
        summary = {
            'anova': anova_result,
            'formatted_p_value': self.format_significance(anova_result['p_value'])
        }
        
        # Run post-hoc tests if ANOVA is significant
        if include_posthoc and anova_result['significant']:
            tukey_result = self.tukey_hsd()
            summary['tukey'] = tukey_result
            
            # Format all pairwise comparisons
            summary['formatted_comparisons'] = {
                comparison: {
                    **stats,
                    'formatted_p_value': self.format_significance(stats['p_value'])
                }
                for comparison, stats in tukey_result['comparisons'].items()
            }
        
        return summary


class TTestComparator:
    """Perform two-sample t-tests for comparing two experimental groups.
    
    Simpler alternative to ANOVA for comparing exactly 2 groups.
    Includes both independent and paired t-tests.
    """
    
    @staticmethod
    def independent_ttest(group1, group2, alpha=0.05, equal_var=True):
        """Perform independent two-sample t-test.
        
        Args:
            group1: Array-like of values for group 1
            group2: Array-like of values for group 2
            alpha: Significance level (default 0.05)
            equal_var: If True, assume equal variances (pooled t-test)
                      If False, use Welch's t-test
        
        Returns:
            dict: Test results with t-statistic, p-value, confidence interval
        """
        data1 = np.array(group1, dtype=float)
        data2 = np.array(group2, dtype=float)
        
        # Filter NaN/Inf
        data1 = data1[np.isfinite(data1)]
        data2 = data2[np.isfinite(data2)]
        
        if len(data1) < 2 or len(data2) < 2:
            raise ValueError("Each group needs at least 2 valid values")
        
        # Perform t-test
        t_statistic, p_value = stats.ttest_ind(data1, data2, equal_var=equal_var)
        
        # Calculate effect size (Cohen's d)
        mean1 = np.mean(data1)
        mean2 = np.mean(data2)
        mean_diff = mean1 - mean2
        
        if equal_var:
            # Pooled standard deviation
            n1, n2 = len(data1), len(data2)
            var1, var2 = np.var(data1, ddof=1), np.var(data2, ddof=1)
            pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))
            cohens_d = mean_diff / pooled_std
        else:
            # Use average of standard deviations
            cohens_d = mean_diff / np.sqrt((np.var(data1, ddof=1) + np.var(data2, ddof=1)) / 2)
        
        # Confidence interval for mean difference
        se_diff = np.sqrt(np.var(data1, ddof=1)/len(data1) + np.var(data2, ddof=1)/len(data2))
        df = len(data1) + len(data2) - 2
        t_critical = stats.t.ppf(1 - alpha/2, df)
        ci_lower = mean_diff - t_critical * se_diff
        ci_upper = mean_diff + t_critical * se_diff
        
        return {
            't_statistic': t_statistic,
            'p_value': p_value,
            'significant': p_value < alpha,
            'alpha': alpha,
            'mean_diff': mean_diff,
            'cohens_d': cohens_d,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n1': len(data1),
            'n2': len(data2),
            'df': df,
            'test_type': 'Welch' if not equal_var else 'Student'
        }
    
    @staticmethod
    def paired_ttest(group1, group2, alpha=0.05):
        """Perform paired t-test (repeated measures).
        
        Args:
            group1: Array-like of values for condition 1
            group2: Array-like of values for condition 2 (same subjects)
            alpha: Significance level (default 0.05)
        
        Returns:
            dict: Test results with t-statistic, p-value, confidence interval
        """
        data1 = np.array(group1, dtype=float)
        data2 = np.array(group2, dtype=float)
        
        if len(data1) != len(data2):
            raise ValueError(f"Groups must have same length for paired test (got {len(data1)} vs {len(data2)})")
        
        # Filter pairs where either value is NaN/Inf
        valid_mask = np.isfinite(data1) & np.isfinite(data2)
        data1 = data1[valid_mask]
        data2 = data2[valid_mask]
        
        if len(data1) < 2:
            raise ValueError("Need at least 2 valid pairs")
        
        # Perform paired t-test
        t_statistic, p_value = stats.ttest_rel(data1, data2)
        
        # Calculate differences
        differences = data1 - data2
        mean_diff = np.mean(differences)
        std_diff = np.std(differences, ddof=1)
        
        # Confidence interval
        n = len(differences)
        df = n - 1
        se_diff = std_diff / np.sqrt(n)
        t_critical = stats.t.ppf(1 - alpha/2, df)
        ci_lower = mean_diff - t_critical * se_diff
        ci_upper = mean_diff + t_critical * se_diff
        
        return {
            't_statistic': t_statistic,
            'p_value': p_value,
            'significant': p_value < alpha,
            'alpha': alpha,
            'mean_diff': mean_diff,
            'std_diff': std_diff,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'n_pairs': n,
            'df': df
        }
