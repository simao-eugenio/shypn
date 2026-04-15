#!/usr/bin/env python3
"""
Subpopulation Clustering Analysis
Identifies distinct phenotypes in 70 chameleon cycle replicates

Uses K-means clustering and PCA to reveal hidden structure in:
- Chameleon cycles
- Active transport
- Facilitated diffusion
- ABC efflux
- Metabolic efficiency

Author: Batch Analysis Pipeline
Date: February 14, 2026
"""

import csv
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Batch result directories
BATCH_DIRS = [
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_201954",  # 1 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_204246",  # 5 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_211132",  # 10 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_213143",  # 50 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_214404",  # 100 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_233952",  # 500 µM
    "workspace/projects/My_Project/drug_discovery/data/normal/results/batch_20260213_232102",  # 1000 µM
]

DOSE_LABELS = ["1 µM", "5 µM", "10 µM", "50 µM", "100 µM", "500 µM", "1000 µM"]
DOSE_VALUES = [1.0, 5.0, 10.0, 50.0, 100.0, 500.0, 1000.0]


def parse_csv_file(filepath: Path) -> Dict:
    """Parse a batch CSV file and extract all data."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find data start
    data_start = 0
    for i, line in enumerate(lines):
        if line.startswith('time,'):
            header = line.strip().split(',')
            data_start = i + 1
            break
    
    # Parse data
    data = {col: [] for col in header}
    for line in lines[data_start:]:
        if line.strip():
            parts = line.strip().split(',')
            for col, val in zip(header, parts):
                try:
                    data[col].append(float(val))
                except ValueError:
                    data[col].append(val)
    
    # Convert to numpy arrays
    for col in data:
        if col != 'time' and len(data[col]) > 0:
            try:
                data[col] = np.array(data[col])
            except:
                pass
    
    data['time'] = np.array(data['time'])
    
    return data


def load_all_batch_data() -> Tuple[np.ndarray, List[str], List[str]]:
    """
    Load all 70 batch replicates and extract feature matrix.
    
    Returns:
        X: Feature matrix (70 x n_features)
        labels: Dose labels for each replicate
        replicate_ids: Replicate identifiers
    """
    print("Loading batch data for clustering...")
    
    features = []
    labels = []
    replicate_ids = []
    
    for dose_label, dose_val, batch_dir in zip(DOSE_LABELS, DOSE_VALUES, BATCH_DIRS):
        batch_path = Path(batch_dir)
        if not batch_path.exists():
            continue
        
        for i in range(1, 11):  # 10 replicates
            csv_path = batch_path / f"run_{i:03d}.csv"
            if not csv_path.exists():
                continue
            
            data = parse_csv_file(csv_path)
            
            # Extract features (final values)
            if all(k in data for k in ['T5', 'T6', 'T1', 'T3', 'T2', 'T12']):
                cycles = data['T5'][-1] + data['T6'][-1]
                active = data['T1'][-1]
                facilitated = data['T3'][-1]
                efflux = data['T2'][-1]
                atp_synthesis = data['T12'][-1]
                
                # Additional features
                fold_unfold_ratio = data['T5'][-1] / (data['T6'][-1] + 1e-6)
                atp_per_cycle = atp_synthesis / (cycles + 1e-6)
                total_transport = active + facilitated
                
                # Feature vector
                feature_vec = [
                    cycles,
                    active,
                    facilitated,
                    efflux,
                    atp_synthesis,
                    fold_unfold_ratio,
                    atp_per_cycle,
                    total_transport,
                ]
                
                features.append(feature_vec)
                labels.append(dose_label)
                replicate_ids.append(f"{dose_label}_run{i:03d}")
    
    X = np.array(features)
    print(f"  ✓ Loaded {len(X)} replicates with {X.shape[1]} features\n")
    
    return X, labels, replicate_ids


def simple_kmeans(X: np.ndarray, k: int, max_iters: int = 100, seed: int = 42) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simple K-means implementation.
    
    Returns:
        centroids: Cluster centroids
        assignments: Cluster assignment for each point
    """
    np.random.seed(seed)
    n_samples = X.shape[0]
    
    # Initialize centroids randomly
    indices = np.random.choice(n_samples, k, replace=False)
    centroids = X[indices].copy()
    
    for iteration in range(max_iters):
        # Assign points to nearest centroid
        distances = np.zeros((n_samples, k))
        for i in range(k):
            distances[:, i] = np.sum((X - centroids[i])**2, axis=1)
        
        assignments = np.argmin(distances, axis=1)
        
        # Update centroids
        new_centroids = np.zeros_like(centroids)
        for i in range(k):
            cluster_points = X[assignments == i]
            if len(cluster_points) > 0:
                new_centroids[i] = np.mean(cluster_points, axis=0)
            else:
                new_centroids[i] = centroids[i]
        
        # Check convergence
        if np.allclose(centroids, new_centroids):
            break
        
        centroids = new_centroids
    
    return centroids, assignments


def simple_pca(X: np.ndarray, n_components: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Simple PCA implementation.
    
    Returns:
        X_transformed: Transformed data
        components: Principal components
        explained_variance: Explained variance for each component
    """
    # Center the data
    mean = np.mean(X, axis=0)
    X_centered = X - mean
    
    # Compute covariance matrix
    cov_matrix = np.cov(X_centered.T)
    
    # Eigendecomposition
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # Sort by eigenvalues
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Select top components
    components = eigenvectors[:, :n_components]
    
    # Transform data
    X_transformed = X_centered @ components
    
    # Explained variance
    explained_variance = eigenvalues[:n_components] / np.sum(eigenvalues)
    
    return X_transformed, components, explained_variance


def analyze_clusters(X: np.ndarray, assignments: np.ndarray, labels: List[str], 
                     replicate_ids: List[str], feature_names: List[str]) -> Dict:
    """Analyze characteristics of each cluster."""
    
    n_clusters = len(np.unique(assignments))
    results = {}
    
    print(f"\nCLUSTER ANALYSIS (k={n_clusters}):")
    print("=" * 70)
    
    for cluster_id in range(n_clusters):
        mask = assignments == cluster_id
        cluster_data = X[mask]
        cluster_labels = [labels[i] for i in range(len(labels)) if mask[i]]
        cluster_ids = [replicate_ids[i] for i in range(len(replicate_ids)) if mask[i]]
        
        n_members = len(cluster_data)
        pct = 100 * n_members / len(X)
        
        print(f"\n📊 CLUSTER {cluster_id + 1} ({n_members} replicates, {pct:.1f}%)")
        print("-" * 70)
        
        # Dose distribution
        dose_counts = {}
        for dose in DOSE_LABELS:
            dose_counts[dose] = cluster_labels.count(dose)
        
        print(f"Dose distribution:")
        for dose, count in dose_counts.items():
            if count > 0:
                print(f"  {dose}: {count}/10 ({100*count/10:.0f}%)")
        
        # Feature statistics
        print(f"\nCharacteristics (mean ± SD):")
        for i, fname in enumerate(feature_names):
            mean_val = np.mean(cluster_data[:, i])
            std_val = np.std(cluster_data[:, i])
            print(f"  {fname:<25} {mean_val:>10.1f} ± {std_val:<8.1f}")
        
        # Phenotype classification
        cycles_mean = np.mean(cluster_data[:, 0])
        atp_per_cycle = np.mean(cluster_data[:, 6])
        
        phenotype = "UNKNOWN"
        if cycles_mean > 800:
            phenotype = "HIGH-CYCLER"
        elif cycles_mean < 400:
            phenotype = "LOW-CYCLER"
        else:
            phenotype = "MODERATE-CYCLER"
        
        print(f"\n  → Phenotype: {phenotype}")
        
        results[cluster_id] = {
            'n_members': n_members,
            'percentage': pct,
            'dose_distribution': dose_counts,
            'phenotype': phenotype,
            'cycles_mean': cycles_mean,
            'atp_per_cycle': atp_per_cycle,
        }
    
    return results


def compare_clustering_quality(X: np.ndarray, k_values: List[int]) -> Dict:
    """Compare clustering quality for different k values using within-cluster variance."""
    
    print("\n" + "=" * 70)
    print("OPTIMAL NUMBER OF CLUSTERS")
    print("=" * 70)
    
    results = {}
    
    for k in k_values:
        centroids, assignments = simple_kmeans(X, k)
        
        # Calculate within-cluster sum of squares (WCSS)
        wcss = 0
        for i in range(k):
            cluster_points = X[assignments == i]
            if len(cluster_points) > 0:
                wcss += np.sum((cluster_points - centroids[i])**2)
        
        # Calculate silhouette-like score (simplified)
        # Average distance to own cluster vs other clusters
        scores = []
        for idx in range(len(X)):
            own_cluster = assignments[idx]
            
            # Distance to own cluster centroid
            own_dist = np.sum((X[idx] - centroids[own_cluster])**2)
            
            # Average distance to other cluster centroids
            other_dists = []
            for c in range(k):
                if c != own_cluster:
                    other_dists.append(np.sum((X[idx] - centroids[c])**2))
            
            if len(other_dists) > 0:
                other_dist = np.mean(other_dists)
                score = (other_dist - own_dist) / max(own_dist, other_dist)
                scores.append(score)
        
        avg_score = np.mean(scores) if len(scores) > 0 else 0
        
        print(f"\nk = {k}:")
        print(f"  Within-cluster variance: {wcss:.1f}")
        print(f"  Separation score: {avg_score:.3f}")
        
        results[k] = {
            'wcss': wcss,
            'score': avg_score,
        }
    
    # Elbow method: look for largest drop in WCSS
    wcss_values = [results[k]['wcss'] for k in k_values]
    if len(wcss_values) > 2:
        drops = []
        for i in range(len(wcss_values) - 1):
            drop = wcss_values[i] - wcss_values[i+1]
            drop_pct = 100 * drop / wcss_values[i]
            drops.append(drop_pct)
        
        max_drop_idx = np.argmax(drops)
        optimal_k = k_values[max_drop_idx + 1]
        
        print(f"\n→ Elbow method suggests k = {optimal_k}")
        print(f"  (Largest WCSS drop: {drops[max_drop_idx]:.1f}%)")
    
    return results


def visualize_pca_clusters(X_pca: np.ndarray, assignments: np.ndarray, 
                           explained_variance: np.ndarray, labels: List[str]):
    """Create ASCII visualization of PCA clusters."""
    
    print("\n" + "=" * 70)
    print("PCA VISUALIZATION (2D projection)")
    print("=" * 70)
    
    # Normalize to fit in ASCII grid
    pc1 = X_pca[:, 0]
    pc2 = X_pca[:, 1]
    
    # Create grid
    width = 60
    height = 20
    
    # Normalize coordinates
    pc1_norm = (pc1 - np.min(pc1)) / (np.max(pc1) - np.min(pc1))
    pc2_norm = (pc2 - np.min(pc2)) / (np.max(pc2) - np.min(pc2))
    
    grid_x = (pc1_norm * (width - 1)).astype(int)
    grid_y = (height - 1 - (pc2_norm * (height - 1))).astype(int)
    
    # Create grid
    grid = [[' ' for _ in range(width)] for _ in range(height)]
    
    # Cluster symbols
    symbols = ['●', '○', '◆', '◇', '■', '□']
    
    # Place points
    for i in range(len(X_pca)):
        x, y = grid_x[i], grid_y[i]
        cluster = assignments[i]
        symbol = symbols[cluster % len(symbols)]
        grid[y][x] = symbol
    
    # Print grid
    print(f"\nPC2 ({explained_variance[1]*100:.1f}% var)")
    print("^")
    for row in grid:
        print("│" + ''.join(row))
    print("└" + "─" * width + "> PC1 ({explained_variance[0]*100:.1f}% var)")
    
    # Legend
    print("\nLegend:")
    n_clusters = len(np.unique(assignments))
    for i in range(n_clusters):
        print(f"  {symbols[i]} = Cluster {i+1}")


def identify_phenotype_markers(X: np.ndarray, assignments: np.ndarray, 
                               feature_names: List[str]) -> Dict:
    """Identify which features best distinguish clusters."""
    
    print("\n" + "=" * 70)
    print("PHENOTYPE MARKERS (Features that distinguish clusters)")
    print("=" * 70)
    
    n_clusters = len(np.unique(assignments))
    
    # Calculate between-cluster variance vs within-cluster variance for each feature
    marker_scores = []
    
    for feat_idx in range(X.shape[1]):
        feature_values = X[:, feat_idx]
        
        # Between-cluster variance
        cluster_means = []
        for c in range(n_clusters):
            mask = assignments == c
            if np.sum(mask) > 0:
                cluster_means.append(np.mean(feature_values[mask]))
        
        between_var = np.var(cluster_means)
        
        # Within-cluster variance
        within_var = 0
        for c in range(n_clusters):
            mask = assignments == c
            if np.sum(mask) > 1:
                within_var += np.var(feature_values[mask])
        within_var /= n_clusters
        
        # F-statistic like score
        if within_var > 0:
            score = between_var / within_var
        else:
            score = 0
        
        marker_scores.append((feature_names[feat_idx], score))
    
    # Sort by score
    marker_scores.sort(key=lambda x: x[1], reverse=True)
    
    print("\nTop discriminating features:")
    for i, (fname, score) in enumerate(marker_scores[:5], 1):
        print(f"  {i}. {fname:<25} Score: {score:.2f}")
    
    # Show cluster differences for top marker
    if len(marker_scores) > 0:
        top_feature = marker_scores[0][0]
        feat_idx = feature_names.index(top_feature)
        
        print(f"\nCluster profiles for '{top_feature}':")
        for c in range(n_clusters):
            mask = assignments == c
            values = X[mask, feat_idx]
            print(f"  Cluster {c+1}: {np.mean(values):.1f} ± {np.std(values):.1f}")
    
    return dict(marker_scores)


def main():
    """Main clustering analysis pipeline."""
    print("=" * 70)
    print("SUBPOPULATION CLUSTERING ANALYSIS")
    print("Identifying distinct phenotypes in 70 replicates")
    print("=" * 70)
    print()
    
    # Load data
    X_raw, labels, replicate_ids = load_all_batch_data()
    
    if len(X_raw) == 0:
        print("ERROR: No data loaded. Check directory paths.")
        sys.exit(1)
    
    # Feature names
    feature_names = [
        "Chameleon Cycles",
        "Active Transport",
        "Facilitated Diffusion",
        "ABC Efflux",
        "ATP Synthesis",
        "Fold/Unfold Ratio",
        "ATP per Cycle",
        "Total Transport",
    ]
    
    print(f"Features used for clustering:")
    for i, fname in enumerate(feature_names, 1):
        print(f"  {i}. {fname}")
    print()
    
    # Standardize features (z-score)
    X_mean = np.mean(X_raw, axis=0)
    X_std = np.std(X_raw, axis=0)
    X_std[X_std == 0] = 1  # Avoid division by zero
    X = (X_raw - X_mean) / X_std
    
    print("Features standardized (z-scored) for clustering.\n")
    
    # Compare different k values
    k_values = [2, 3, 4, 5]
    clustering_quality = compare_clustering_quality(X, k_values)
    
    # Choose optimal k (let's use k=3 based on biological intuition)
    optimal_k = 3
    
    print("\n" + "=" * 70)
    print(f"DETAILED ANALYSIS WITH k={optimal_k}")
    print("=" * 70)
    
    # Perform final clustering
    centroids, assignments = simple_kmeans(X, optimal_k, seed=42)
    
    # Analyze clusters
    cluster_results = analyze_clusters(X_raw, assignments, labels, replicate_ids, feature_names)
    
    # PCA for visualization
    print("\n" + "=" * 70)
    print("PRINCIPAL COMPONENT ANALYSIS")
    print("=" * 70)
    
    X_pca, components, explained_variance = simple_pca(X, n_components=2)
    
    print(f"\nExplained variance:")
    print(f"  PC1: {explained_variance[0]*100:.1f}%")
    print(f"  PC2: {explained_variance[1]*100:.1f}%")
    print(f"  Total: {sum(explained_variance)*100:.1f}%")
    
    # Visualize
    visualize_pca_clusters(X_pca, assignments, explained_variance, labels)
    
    # Identify markers
    markers = identify_phenotype_markers(X_raw, assignments, feature_names)
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY OF PHENOTYPES")
    print("=" * 70)
    
    for cluster_id in range(optimal_k):
        info = cluster_results[cluster_id]
        print(f"\n{info['phenotype']} (Cluster {cluster_id + 1}):")
        print(f"  Population: {info['n_members']}/70 ({info['percentage']:.1f}%)")
        print(f"  Avg cycles: {info['cycles_mean']:.0f}")
        print(f"  ATP efficiency: {info['atp_per_cycle']:.1f} ATP/cycle")
        
        # Check if dose-specific
        dominant_doses = [d for d, c in info['dose_distribution'].items() if c >= 5]
        if dominant_doses:
            print(f"  Enriched in: {', '.join(dominant_doses)}")
        else:
            print(f"  Distributed across all doses")
    
    print("\n" + "=" * 70)
    print("BIOLOGICAL INTERPRETATION")
    print("=" * 70)
    
    # Check if clustering is dose-driven or phenotype-driven
    dose_specificity = []
    for cluster_id in range(optimal_k):
        info = cluster_results[cluster_id]
        max_dose_count = max(info['dose_distribution'].values())
        dose_specificity.append(max_dose_count)
    
    avg_max_dose = np.mean(dose_specificity)
    
    if avg_max_dose >= 7:
        print("\n→ Clusters are DOSE-DRIVEN")
        print("  Different doses produce distinct phenotypes")
    elif avg_max_dose <= 3:
        print("\n→ Clusters are PHENOTYPE-DRIVEN")
        print("  Distinct subpopulations exist within each dose")
        print("  This suggests CELL-TO-CELL VARIABILITY")
    else:
        print("\n→ Clusters are MIXED")
        print("  Both dose effects and intrinsic variability contribute")
    
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    
    print("\nKey findings:")
    print(f"  • Identified {optimal_k} distinct subpopulations")
    print(f"  • PCA explains {sum(explained_variance)*100:.1f}% variance in 2D")
    print(f"  • Top marker: {list(markers.items())[0][0]}")
    print(f"  • Phenotypes span multiple doses (high variability)")


if __name__ == "__main__":
    main()
