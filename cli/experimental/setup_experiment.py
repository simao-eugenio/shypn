#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Experiment - Initialize experiment directory structure

Creates a standardized directory structure for large-scale validation experiments
including configuration, data directories, and metadata tracking.

Usage:
    python -m shypn.cli.experimental.setup_experiment \\
        --name "tau_leaping_validation_93_models" \\
        --models model_list.csv \\
        --output experiments/tau_leaping/

Author: SHYpn Development Team
License: MIT
Version: 1.0.0
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Initialize experiment directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic usage
    %(prog)s --name my_experiment --models list.csv --output exp/

    # With custom description
    %(prog)s --name validation --models list.csv --output exp/ \\
             --description "Parallel τ-leaping validation"

For more information, see: https://shypn.readthedocs.io/cli/experimental/
        """
    )
    
    parser.add_argument('--name', required=True,
                        help='Experiment name (used in reports)')
    parser.add_argument('--models', required=True,
                        help='Path to model list CSV file')
    parser.add_argument('--output', required=True,
                        help='Output directory for experiment')
    parser.add_argument('--description', default='',
                        help='Optional experiment description')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0.0')
    
    return parser.parse_args()


def create_directory_structure(base_path: Path):
    """Create experiment directory structure."""
    directories = [
        'models',
        'data/replicates',
        'data/statistics',
        'data/timing',
        'validation',
        'figures/violin_plots',
        'figures/heatmaps',
        'figures/scatter_plots',
        'reports',
        'checkpoints'
    ]
    
    for dir_path in directories:
        (base_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    return directories


def create_config(base_path: Path, name: str, description: str):
    """Create experiment configuration file."""
    config = {
        'name': name,
        'description': description,
        'created_at': datetime.now().isoformat(),
        'version': '1.0.0',
        'settings': {
            'default_replicates': 1000,
            'default_duration': 100.0,
            'default_epsilon': 0.03,
            'random_seed_base': 42
        }
    }
    
    with open(base_path / 'config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    return config


def create_manifest(base_path: Path):
    """Create experiment manifest with metadata."""
    manifest = {
        'created_at': datetime.now().isoformat(),
        'tool_versions': {
            'setup_experiment': '1.0.0',
            'shypn': '2.0.0'  # Update with actual version
        },
        'directory_structure': 'standard_v1'
    }
    
    with open(base_path / 'manifest.json', 'w') as f:
        json.dump(manifest, f, indent=2)
    
    return manifest


def main():
    """Main entry point."""
    args = parse_arguments()
    
    try:
        # Validate inputs
        models_path = Path(args.models)
        if not models_path.exists():
            print(f"ERROR: Model list not found: {args.models}", file=sys.stderr)
            sys.exit(1)
        
        output_path = Path(args.output)
        
        # Check if directory already exists
        if output_path.exists():
            response = input(f"Directory {output_path} already exists. Overwrite? [y/N]: ")
            if response.lower() != 'y':
                print("Aborted.")
                sys.exit(0)
        
        # Create directory structure
        print(f"Creating experiment directory: {output_path}")
        create_directory_structure(output_path)
        
        # Copy model list
        print(f"Copying model list...")
        shutil.copy(models_path, output_path / 'models' / 'model_list.csv')
        
        # Create configuration
        print(f"Creating configuration...")
        config = create_config(output_path, args.name, args.description)
        
        # Create manifest
        print(f"Creating manifest...")
        manifest = create_manifest(output_path)
        
        # Create README
        readme_content = f"""# {args.name}

{args.description}

## Experiment Information

- **Created**: {manifest['created_at']}
- **Tool Version**: {manifest['tool_versions']['setup_experiment']}

## Directory Structure

- `models/` - Model list and SBML files
- `data/` - Generated data (trajectories, statistics, timing)
- `validation/` - Validation results (MAE, CV, KS tests)
- `figures/` - Generated plots and visualizations
- `reports/` - Final reports and summaries
- `checkpoints/` - Progress checkpoints for resuming

## Configuration

See `config.json` for experiment parameters.

## Next Steps

1. Run batch replicates:
   ```bash
   shypn-batch-replicates --models models/model_list.csv --output data/replicates/
   ```

2. Validate equivalence:
   ```bash
   shypn-validate-equivalence --parallel ... --sequential ... --output validation/
   ```

3. Generate report:
   ```bash
   shypn-generate-report --experiment-dir . --output reports/FINAL_REPORT.md
   ```
"""
        
        with open(output_path / 'README.md', 'w') as f:
            f.write(readme_content)
        
        # Success
        print("\n" + "="*60)
        print("✅ Experiment setup complete!")
        print("="*60)
        print(f"\nExperiment directory: {output_path.absolute()}")
        print(f"Configuration: {(output_path / 'config.json').absolute()}")
        print(f"\nNext: Run batch replicates with:")
        print(f"  shypn-batch-replicates --models {output_path}/models/model_list.csv \\")
        print(f"                         --output {output_path}/data/replicates/")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
