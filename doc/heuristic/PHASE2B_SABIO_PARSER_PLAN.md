# Phase 2B: SABIO-RK Parser Implementation

**Date**: October 19, 2025  
**Status**: 🔨 **IN PROGRESS**  
**Goal**: Complete SABIO-RK API parser for online enzyme kinetics lookup

---

## Objective

Enable online fetching of enzyme kinetic parameters from SABIO-RK API, providing access to 39,000+ curated kinetic entries from scientific literature.

## Current State

### What's Done ✅
- EnzymeKineticsAPI framework complete
- SABIO-RK HTTP request working
- Cache system functional
- Offline fallback working

### What's Missing ⚠️
- SABIO-RK response parser (skeleton only)
- Unit conversion to standard format
- Parameter extraction logic
- Multiple substrate handling

## SABIO-RK API Overview

### Endpoint
```
GET http://sabiork.h-its.org/sabioRestWebServices/kineticLaws
Parameters:
  - ECNumber: EC number (e.g., "2.7.1.1")
  - format: "json" or "xml"
  - Organism: Optional filter (e.g., "Homo sapiens")
```

### Response Format

SABIO-RK returns a JSON array of kinetic law entries:

```json
[
  {
    "kinlawid": 123456,
    "EntryID": 45678,
    "Name": "kinetic law for Hexokinase",
    "Enzyme": "Hexokinase",
    "ECNumber": "2.7.1.1",
    "Organism": "Homo sapiens",
    "Tissue": "brain",
    "CellularLocation": "cytoplasm",
    "KineticMechanismType": "Michaelis-Menten",
    "Equation": "v = Vmax * [S] / (Km + [S])",
    "parameter": [
      {
        "parameterId": 1001,
        "parameterName": "Km",
        "parameterType": "Km",
        "SBOTerm": "SBO:0000027",
        "value": "0.05",
        "unit": "mM",
        "associatedSpecies": "D-glucose",
        "substrate": true
      },
      {
        "parameterId": 1002,
        "parameterName": "kcat",
        "parameterType": "kcat",
        "SBOTerm": "SBO:0000025",
        "value": "450",
        "unit": "1/s",
        "associatedSpecies": "",
        "substrate": false
      }
    ],
    "Publication": {
      "pubmedID": "12345678",
      "title": "Kinetic properties of hexokinase...",
      "author": "Wilson JE",
      "year": "2003"
    },
    "ExperimentalConditions": {
      "temperature": "37",
      "temperatureUnit": "°C",
      "ph": "7.4",
      "buffer": "phosphate"
    }
  }
]
```

## Implementation Plan

### Step 1: Understand Real SABIO-RK Response

First, let's fetch a real response to see the actual format.

### Step 2: Implement Parameter Extraction

Parse the `parameter` array and extract:
- Km values (for each substrate)
- kcat or Vmax values
- Units (for conversion)

### Step 3: Unit Conversion

Convert to standard units:
- Km: mM (millimolar)
- Vmax: μmol/min/mg protein
- kcat: 1/s (per second)

### Step 4: Handle Multiple Organisms

Prefer human data, but accept other organisms if human not available.

### Step 5: Select Best Entry

When multiple entries exist, select based on:
1. Organism match (prefer Homo sapiens)
2. Wildtype enzyme (not mutant)
3. Most complete parameter set
4. Most recent publication

---

## Implementation

Let me start by testing the real SABIO-RK API to understand the actual response format.
