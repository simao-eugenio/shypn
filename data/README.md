# Data Directory

This directory contains data files, models, templates, and resources used by the SHYpn application.

## Contents

### biomodels_test/
Test data from BioModels database for validation and testing purposes.

### templates/
Template files for:
- New Petri net models
- Project structures
- Default configurations

## Purpose

This directory serves as a repository for:
- **Static data**: Reference data used by the application
- **Test models**: Sample Petri net models for testing and validation
- **Templates**: Starting points for new models and projects
- **Configuration data**: Default settings and schemas

## Usage

The application reads from this directory during:
- Model creation (templates)
- Testing (biomodels_test)
- Import operations (reference data)
- Default configuration loading

## Related Directories

- `models/`: User-created Petri net model files (.shy format)
- `workspace/examples/`: Example models for users
- `workspace/projects/`: User project directories