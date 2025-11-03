# 🎯 Implementation Plan: SABIO-RK Stochastic Rate Enrichment

## 📋 Overview
Implement a complete enrichment system for **stochastic transitions** using SABIO-RK database, similar to the existing BRENDA enrichment but focused on elementary reaction rate constants.

**Date Created:** November 2, 2025  
**Status:** Planning Phase  
**Estimated Time:** 7-8 hours (+ 3-4 hours for real BRENDA API)

---

## ⚠️ CRITICAL: Real BRENDA API Integration Required

### Current Limitation Discovered:
🚨 **The system is currently using ONLY mock/hardcoded data, NOT querying real BRENDA!**

**Evidence from logs:**
```
[BRENDA_API] Mock data for 2.7.1.11: Phosphofructokinase  ← Found in local mock
[BRENDA_API] No mock data for 1.2.1.3                     ← Not in mock, skipped
```

**Current code:**
```python
def fetch_from_brenda_api(self, ec_number: str, organism: str = None):
    # TODO: Implement BRENDA SOAP API integration
    # Requires zeep library and BRENDA credentials
    
    # For now, return mock data for common enzymes  ← THIS IS RUNNING!
    mock_brenda_data = { ... }
    return mock_brenda_data.get(ec_number)
```

### 🔥 Priority Task: Implement Real BRENDA SOAP API

**Must be done BEFORE SABIO-RK to validate enrichment architecture!**

---

## 🏗️ Phase 0: Real BRENDA API Integration (NEW - DO FIRST!)

### Estimated Time: 3-4 hours
### Priority: HIGHEST ⚠️

### Step 0.1: Setup BRENDA Credentials (30 mins)
- [ ] Register for BRENDA academic license (https://www.brenda-enzymes.org/soap.php)
- [ ] Get email + password for SOAP API access
- [ ] Store credentials securely (NOT in code!)
  - Option 1: Environment variables (`BRENDA_EMAIL`, `BRENDA_PASSWORD`)
  - Option 2: Config file in `~/.config/shypn/brenda_credentials.json`
  - Option 3: Project-level settings (encrypted)

### Step 0.2: Install SOAP Client (10 mins)
- [ ] Add `zeep` library to dependencies
  ```bash
  pip install zeep
  # Or add to pyproject.toml:
  # dependencies = [..., "zeep>=4.2.1"]
  ```
- [ ] Test SOAP client installation
  ```python
  from zeep import Client
  wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
  client = Client(wsdl)
  ```

### Step 0.3: Implement Real API Calls (2-3 hours)
**File:** `src/shypn/helpers/brenda_enrichment_controller.py`

**Replace mock implementation with real SOAP calls:**

```python
def fetch_from_brenda_api(self, ec_number: str, organism: str = "Homo sapiens") -> Optional[Dict[str, Any]]:
    """Fetch kinetic data from BRENDA SOAP API.
    
    Args:
        ec_number: EC number to query (e.g., "2.7.1.1")
        organism: Organism filter (default: "Homo sapiens")
    
    Returns:
        Dict with BRENDA data or None if not available
    """
    try:
        from zeep import Client
        
        # Get credentials
        email, password = self._get_brenda_credentials()
        if not email or not password:
            print("[BRENDA_API] No credentials found, falling back to mock data")
            return self._get_mock_data(ec_number)
        
        # Initialize SOAP client
        wsdl = "https://www.brenda-enzymes.org/soap/brenda_zeep.wsdl"
        client = Client(wsdl)
        
        print(f"[BRENDA_API] 🌐 Querying real BRENDA for EC {ec_number}...")
        
        # Query KM values
        km_result = client.service.getKmValue(email, password, ec_number, organism)
        km_values = self._parse_km_values(km_result)
        
        # Query Kcat values
        kcat_result = client.service.getTurnoverNumber(email, password, ec_number, organism)
        kcat_values = self._parse_kcat_values(kcat_result)
        
        # Query Ki values (inhibition constants)
        ki_result = client.service.getKiValue(email, password, ec_number, organism)
        ki_values = self._parse_ki_values(ki_result)
        
        # Get enzyme name
        enzyme_result = client.service.getEnzymeName(email, password, ec_number)
        enzyme_name = enzyme_result if enzyme_result else f"EC {ec_number}"
        
        # Construct result
        if km_values or kcat_values or ki_values:
            print(f"[BRENDA_API] ✅ Found real BRENDA data for {ec_number}")
            return {
                'ec_number': ec_number,
                'enzyme_name': enzyme_name,
                'organism': organism,
                'km_values': km_values,
                'kcat_values': kcat_values,
                'ki_values': ki_values,
                'vmax_values': [],  # Calculate from kcat if needed
                'citations': []
            }
        else:
            print(f"[BRENDA_API] ⚠️ No kinetic data in real BRENDA for {ec_number}")
            return None
            
    except ImportError:
        print("[BRENDA_API] ⚠️ zeep not installed, using mock data")
        return self._get_mock_data(ec_number)
    except Exception as e:
        print(f"[BRENDA_API] ❌ Error querying BRENDA: {e}")
        return self._get_mock_data(ec_number)  # Fallback to mock

def _get_brenda_credentials(self):
    """Get BRENDA credentials from config/environment."""
    # Try environment variables first
    import os
    email = os.environ.get('BRENDA_EMAIL')
    password = os.environ.get('BRENDA_PASSWORD')
    
    if email and password:
        return email, password
    
    # Try config file
    config_path = os.path.expanduser('~/.config/shypn/brenda_credentials.json')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            creds = json.load(f)
            return creds.get('email'), creds.get('password')
    
    return None, None

def _parse_km_values(self, km_result: str) -> List[Dict]:
    """Parse BRENDA KM result string."""
    # BRENDA returns results as formatted strings
    # Format: "#ID# value unit #organism# Org name #commentary# ..."
    values = []
    if not km_result:
        return values
    
    # Split by entry markers
    entries = km_result.split('#')
    for i in range(0, len(entries), 2):
        if i+1 < len(entries):
            try:
                # Extract value and unit
                value_str = entries[i+1].strip()
                parts = value_str.split()
                if len(parts) >= 2:
                    value = float(parts[0])
                    unit = parts[1]
                    values.append({
                        'substrate': 'unknown',  # Parse from commentary if available
                        'value': value,
                        'unit': unit
                    })
            except (ValueError, IndexError):
                continue
    
    return values

def _parse_kcat_values(self, kcat_result: str) -> List[Dict]:
    """Parse BRENDA Kcat (turnover number) result string."""
    # Similar parsing logic as KM
    values = []
    if not kcat_result:
        return values
    
    entries = kcat_result.split('#')
    for i in range(0, len(entries), 2):
        if i+1 < len(entries):
            try:
                value_str = entries[i+1].strip()
                parts = value_str.split()
                if len(parts) >= 2:
                    value = float(parts[0])
                    unit = parts[1]
                    values.append({
                        'value': value,
                        'unit': unit
                    })
            except (ValueError, IndexError):
                continue
    
    return values

def _parse_ki_values(self, ki_result: str) -> List[Dict]:
    """Parse BRENDA Ki (inhibition) result string."""
    values = []
    if not ki_result:
        return values
    
    entries = ki_result.split('#')
    for i in range(0, len(entries), 2):
        if i+1 < len(entries):
            try:
                value_str = entries[i+1].strip()
                parts = value_str.split()
                if len(parts) >= 2:
                    value = float(parts[0])
                    unit = parts[1]
                    values.append({
                        'inhibitor': 'unknown',  # Parse from commentary
                        'value': value,
                        'unit': unit
                    })
            except (ValueError, IndexError):
                continue
    
    return values

def _get_mock_data(self, ec_number: str) -> Optional[Dict[str, Any]]:
    """Fallback to mock data if API unavailable."""
    # Keep existing mock_brenda_data for testing
    mock_brenda_data = { ... }  # Existing mock data
    return mock_brenda_data.get(ec_number)
```

### Step 0.4: Test Real API Integration (30 mins)
- [ ] Test with known EC numbers (2.7.1.1, 5.3.1.9)
- [ ] Verify real data differs from mock data
- [ ] Test error handling (bad credentials, network issues)
- [ ] Test fallback to mock data when API unavailable
- [ ] Add logging to distinguish real vs mock data

### Step 0.5: Update UI to Show Data Source (15 mins)
- [ ] Add indicator in Report panel: "Data source: BRENDA API" vs "Mock database"
- [ ] Show warning if using mock data
- [ ] Add settings dialog for BRENDA credentials

### Success Criteria for Phase 0:
- [ ] Real BRENDA SOAP API successfully queried
- [ ] Returns different data than mock database
- [ ] Credentials stored securely
- [ ] Graceful fallback to mock if API fails
- [ ] Clear logging shows "🌐 Querying real BRENDA..." vs "Mock data"

---

## 🏗️ Architecture

### Phase 1: Core SABIO-RK Controller (Similar to BRENDA)
**File:** `src/shypn/helpers/sabio_rk_enrichment_controller.py`

**Components:**
1. **SABIO-RK API Client**
   - REST API integration (http://sabiork.h-its.org/sabioRestWebServices/)
   - Query by: EC number, KEGG reaction ID, compound IDs
   - Parse JSON/XML responses
   - Handle rate limiting and errors

2. **Mock Database** (for development/testing)
   ```python
   SABIO_MOCK_DATA = {
       'R00200': {  # KEGG reaction ID
           'reaction_id': 'R00200',
           'name': 'ATP + D-Glucose <=> ADP + D-Glucose 6-phosphate',
           'k_forward': 0.5,  # s^-1
           'k_reverse': 0.01,  # s^-1
           'temperature': 298.15,  # K
           'ph': 7.4,
           'citations': ['PMID:12345678']
       },
       # Add ~20-30 common glycolysis reactions
   }
   ```

3. **Parameter Extraction**
   - Extract: k_forward, k_reverse, k_cat (for mass action)
   - Handle units conversion (s^-1, M^-1·s^-1, etc.)
   - Store experimental conditions (T, pH, organism)

4. **Transition Matching**
   - Match by: KEGG reaction ID (from transition metadata)
   - Match by: substrate/product compound IDs
   - Fallback: EC number (if stochastic but has EC)

5. **Rate Function Generation**
   ```python
   # For reversible stochastic reactions
   rate_function = "mass_action_reversible(substrates, products, k_forward, k_reverse)"
   
   # For irreversible stochastic reactions
   rate_function = "mass_action(substrates, k_forward)"
   ```

---

### Phase 2: UI Architecture Refactoring ⚠️ IMPORTANT

**REFACTORING REQUIRED**: Move enrichment controls from Report panel to Pathway Operations panel

#### Step 2.1: Move BRENDA Controls to Pathway Operations Panel
**File:** `src/shypn/ui/panels/pathway_operations/brenda_category.py` (EXISTS)

**Changes:**
1. **Move from Report Panel to BRENDA Category**
   - Currently: Enrich button is in `report_panel.py`
   - New location: Move to existing `brenda_category.py`
   - Keep: All enrichment logic in `brenda_enrichment_controller.py`

2. **BRENDA Category UI**
   ```
   ┌─────────────────────────────────────┐
   │ BRENDA Enrichment                   │
   ├─────────────────────────────────────┤
   │ Target: Continuous (Enzymatic)      │
   │                                     │
   │ [🧬 Enrich from API]               │
   │ [📁 Load from File]                │
   │                                     │
   │ ☑ Override KEGG Heuristics (always) │
   │ ☐ Override SBML Curated Data        │
   │                                     │
   │ Parameters: Km, Kcat, Vmax, Ki      │
   │ Color: Blue (#2563eb)               │
   └─────────────────────────────────────┘
   ```

3. **Wire to Report Panel**
   - BRENDA category triggers enrichment
   - Report panel displays results (color-coded table)
   - No enrichment controls in Report panel

#### Step 2.2: Create SABIO-RK Category Panel
**File:** `src/shypn/ui/panels/pathway_operations/sabio_rk_category.py` (NEW)

**Layout (mirror BRENDA structure):**
```python
class SabioRKCategory(Gtk.Box):
    """SABIO-RK enrichment category in Pathway Operations panel"""
    
    def __init__(self, model_canvas, project_manager):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        # Title
        title = Gtk.Label()
        title.set_markup("<b>SABIO-RK Enrichment</b>")
        
        # Info label
        info = Gtk.Label("Enrich stochastic transitions with rate constants")
        
        # Enrich buttons
        enrich_api_btn = Gtk.Button(label="🔬 Enrich from API")
        enrich_file_btn = Gtk.Button(label="📁 Load from File")
        
        # Override options
        override_kegg_check = Gtk.CheckButton(label="Override KEGG Heuristics")
        override_kegg_check.set_active(True)  # Default ON
        
        override_sbml_check = Gtk.CheckButton(label="Override SBML Curated Data")
        override_sbml_check.set_active(False)  # Default OFF
        
        # Parameters info
        params_label = Gtk.Label("Parameters: k_forward, k_reverse")
        color_label = Gtk.Label("Color: Purple (#9333ea)")
```

#### Step 2.3: Update Pathway Operations Panel
**File:** `src/shypn/ui/panels/pathway_operations_panel.py`

**Changes:**
1. **Add SABIO-RK category to stack**
   ```python
   # Existing categories
   self.stack.add_titled(brenda_category, "brenda", "BRENDA")
   
   # NEW: Add SABIO-RK category
   sabio_rk_category = SabioRKCategory(model_canvas, project_manager)
   self.stack.add_titled(sabio_rk_category, "sabio_rk", "SABIO-RK")
   ```

2. **Navigation**
   ```
   Pathway Operations:
   - KEGG Import
   - SBML Import
   - BRENDA       ← Existing
   - SABIO-RK     ← NEW
   - BioPAX
   - etc.
   ```

#### Step 2.4: Remove Controls from Report Panel
**File:** `src/shypn/ui/panels/report/report_panel.py`

**Changes:**
1. **Remove Enrich button** (moved to BRENDA category)
2. **Remove Override checkbox** (moved to BRENDA category)
3. **Keep only display logic** (table, colors, refresh)

**Report Panel becomes display-only:**
```
┌─────────────────────────────────────────────────────┐
│ Model Structure Report                              │
├─────────────────────────────────────────────────────┤
│ [🔄 Refresh]  (only refresh button)                │
├─────────────────────────────────────────────────────┤
│ Species Table                                       │
│ Reactions Table (with color-coded parameters)      │
│                                                     │
│ Legend:                                             │
│ 🔵 Blue = BRENDA    🟣 Purple = SABIO-RK           │
│ 🟢 Green = KEGG DB  ⚫ Gray = Heuristic             │
└─────────────────────────────────────────────────────┘
```

---

### Phase 3: Report Panel Display

**File:** `src/shypn/ui/panels/report/model_structure_category.py`

**Changes:**
1. **Expand Reactions Table to 20 columns**
   - Add columns: `k_forward`, `k_forward_source`, `k_reverse`, `k_reverse_source`
   - Keep existing: Km, Kcat, Vmax, Ki columns

2. **New Color Coding**
   ```python
   Color Scheme (expanded):
   - Green (#16a34a): Real KEGG/SBML database kinetics
   - Blue (#2563eb): BRENDA enzymatic data
   - Purple (#9333ea): SABIO-RK stochastic rates  ← NEW!
   - Gray italic (#6b7280): KEGG/Shypn heuristics
   - Orange (#ea580c): User edits
   - Light gray (#9ca3af): Missing/N/A
   ```

3. **Smart Column Display**
   - **Continuous transitions**: Show Km, Kcat, Vmax, Ki (hide k columns)
   - **Stochastic transitions**: Show k_forward, k_reverse (hide MM columns)
   - Auto-detect based on `transition_type`

---

### Phase 4: Enrichment Workflow

**File:** `src/shypn/helpers/sabio_rk_enrichment_controller.py`

**Methods:**
```python
class SabioRKEnrichmentController:
    def __init__(self, model_canvas, project_manager):
        self.model_canvas = model_canvas
        self.project_manager = project_manager
        self.base_url = "http://sabiork.h-its.org/sabioRestWebServices"
    
    def scan_stochastic_transitions(self):
        """Find all stochastic transitions in canvas"""
        # Filter by transition_type == 'stochastic'
        # Extract KEGG reaction IDs, compound IDs
        
    def query_sabio_by_reaction_id(self, kegg_reaction_id):
        """Query SABIO-RK by KEGG reaction ID"""
        # GET /searchKineticLaws/sbml?q=KeggReactionID:{id}
        
    def query_sabio_by_compounds(self, substrates, products):
        """Query by substrate/product compound IDs"""
        # GET /searchKineticLaws/sbml?q=Substrates:{S1}+{S2}...
        
    def extract_rate_constants(self, sabio_response):
        """Parse SABIO-RK response and extract k values"""
        # Extract kineticLaw parameters
        # Handle different kinetic law types
        
    def apply_to_transition(self, transition_id, rate_data):
        """Apply SABIO-RK rate constants to transition"""
        # transition.metadata['k_forward'] = ...
        # transition.metadata['k_forward_source'] = 'sabio_rk_enriched'
        # Generate rate_function
        
    def enrich_canvas_from_api(self, override_existing=False):
        """Main enrichment workflow"""
        # 1. Scan stochastic transitions
        # 2. Query SABIO-RK for each
        # 3. Apply rate constants
        # 4. Generate rate functions
        # 5. Return summary
```

---

### Phase 5: Data Source Intelligence

**File:** `src/shypn/helpers/sabio_rk_enrichment_controller.py`

**Smart Override Logic** (same as BRENDA):
```python
def should_enrich_stochastic(transition):
    has_rates = transition.get('has_rate_constants')
    data_source = transition.get('data_source')
    
    if not has_rates:
        return True  # No rates, always enrich
    elif data_source == 'kegg_import':
        return True  # KEGG has no real rates, override
    elif override_existing:
        return True  # User forced override
    else:
        return False  # Respect SBML curated rates
```

---

## 📊 Expanded Report Panel Layout

### Reactions Table (20 columns):

| Column | Display For | Source Color |
|--------|-------------|--------------|
| Index | All | - |
| Petri Net ID | All | - |
| Name | All | - |
| Reaction ID | All | - |
| EC Number | All | - |
| Type | All | - |
| **Km** | Continuous only | Blue/Green/Gray |
| **Kcat** | Continuous only | Blue/Green/Gray |
| **Vmax** | Continuous only | Blue/Green/Gray |
| **Ki** | Continuous only | Blue/Green/Gray |
| **k_forward** | Stochastic only | Purple/Green/Gray |
| **k_reverse** | Stochastic only | Purple/Green/Gray |
| Rate Law | All | - |
| Reversible | All | - |

---

## 🔧 Implementation Steps

### ⚠️ Phase 0: Real BRENDA API Integration (DO THIS FIRST!)
**Time: 3-4 hours | Priority: HIGHEST**

- [ ] Register for BRENDA academic license (free)
- [ ] Install zeep SOAP client library
- [ ] Implement `_get_brenda_credentials()` method
- [ ] Replace mock implementation with real SOAP API calls
- [ ] Implement result parsers (`_parse_km_values`, `_parse_kcat_values`, `_parse_ki_values`)
- [ ] Test with real BRENDA queries (verify different from mock)
- [ ] Add fallback to mock data if API unavailable
- [ ] Update logging to show real vs mock data source
- [ ] Add UI indicator for data source

### Step 1: UI Refactoring (1-2 hours) ⚠️ DO AFTER PHASE 0
**PREREQUISITE**: Move BRENDA controls before implementing SABIO-RK

- [ ] Move Enrich button from `report_panel.py` to `brenda_category.py`
- [ ] Move Override checkbox to BRENDA category
- [ ] Test BRENDA enrichment still works from new location (with real API!)
- [ ] Remove enrichment controls from Report panel
- [ ] Report panel becomes display-only (table + refresh)
- [ ] Update callback wiring (BRENDA category → enrichment controller → Report refresh)

### Step 2: Create SABIO-RK Controller (1-2 hours)
- [ ] Create `sabio_rk_enrichment_controller.py`
- [ ] Implement mock database with 20 glycolysis reactions
- [ ] Write scan_stochastic_transitions()
- [ ] Write parameter extraction logic

### Step 3: API Integration (1 hour)
- [ ] Implement REST API client
- [ ] Test with real SABIO-RK queries
- [ ] Handle error cases and timeouts

### Step 4: Rate Function Generation (1 hour)
- [ ] Implement mass_action() rate function generator
- [ ] Handle reversible vs irreversible reactions
- [ ] Detect substrates/products from arcs

### Step 5: UI Updates - SABIO-RK Category (1 hour)
- [ ] Create `sabio_rk_category.py` in pathway_operations panel
- [ ] Add "🔬 Enrich from API" button
- [ ] Add "📁 Load from File" button
- [ ] Add override checkboxes (KEGG=ON, SBML=OFF)
- [ ] Add SABIO-RK category to pathway_operations_panel.py stack
- [ ] Wire to sabio_rk_enrichment_controller

### Step 6: Report Panel Display Updates (1 hour)
- [ ] Add k_forward/k_reverse columns to Reactions table
- [ ] Implement purple color coding for SABIO-RK data
- [ ] Add smart column hiding (show relevant columns per type)
- [ ] Update legend with SABIO-RK purple color

### Step 7: Testing (30 mins)
- [ ] Test BRENDA enrichment from Pathway Operations panel
- [ ] Test SABIO-RK enrichment from Pathway Operations panel
- [ ] Verify Report panel displays both enrichments correctly
- [ ] Test with hsa00010 model
- [ ] Verify stochastic transitions enriched with purple
- [ ] Verify continuous transitions still blue (BRENDA)
- [ ] Verify SBML models protected

### Step 8: Documentation (30 mins)
- [ ] Update user guide
- [ ] Add SABIO-RK section to docs
- [ ] Document new UI architecture (Pathway Operations → Report)
- [ ] Document color scheme

---

## 🎨 Visual Design

### Pathway Operations Panel (Enrichment Controls):
```
┌─────────────────────────────────────┐
│ Pathway Operations                  │
├─────────────────────────────────────┤
│ Stack Switcher:                     │
│ [KEGG][SBML][BRENDA][SABIO-RK]...  │
├─────────────────────────────────────┤
│                                     │
│ ┌─ BRENDA Category ─────────────┐  │
│ │ 🧬 Enrichment Controls         │  │
│ │                                │  │
│ │ [🧬 Enrich from API]          │  │
│ │ [� Load from File]           │  │
│ │                                │  │
│ │ ☑ Override KEGG Heuristics     │  │
│ │ ☐ Override SBML Curated        │  │
│ │                                │  │
│ │ Target: Continuous (enzymatic) │  │
│ │ Parameters: Km,Kcat,Vmax,Ki   │  │
│ │ Color: 🔵 Blue                 │  │
│ └────────────────────────────────┘  │
│                                     │
│ ┌─ SABIO-RK Category ───────────┐  │
│ │ 🔬 Enrichment Controls         │  │
│ │                                │  │
│ │ [🔬 Enrich from API]          │  │
│ │ [📁 Load from File]           │  │
│ │                                │  │
│ │ ☑ Override KEGG Heuristics     │  │
│ │ ☐ Override SBML Curated        │  │
│ │                                │  │
│ │ Target: Stochastic (mass act.) │  │
│ │ Parameters: k_fwd, k_rev      │  │
│ │ Color: 🟣 Purple               │  │
│ └────────────────────────────────┘  │
└─────────────────────────────────────┘
```

### Report Panel (Display Only):
```
┌─────────────────────────────────────────────────────┐
│ Model Structure Report                              │
├─────────────────────────────────────────────────────┤
│ [🔄 Refresh] (only refresh - no enrich buttons)    │
├─────────────────────────────────────────────────────┤
│ Reactions Table                                     │
│ ┌──────┬────┬──────────┬──────┬───────┬──────────┐│
│ │ ID   │Type│ Km       │ Vmax │k_fwd  │ k_rev    ││
│ ├──────┼────┼──────────┼──────┼───────┼──────────┤│
│ │ T1   │Cont│ 0.05 (B) │ 2.5  │  -    │   -      ││  ← Blue = BRENDA
│ │ T2   │Stoc│   -      │  -   │ 0.5(S)│ 0.01 (S) ││  ← Purple = SABIO-RK
│ │ T3   │Cont│ 10.0 (H) │ 0.5  │  -    │   -      ││  ← Gray = Heuristic
│ └──────┴────┴──────────┴──────┴───────┴──────────┘│
├─────────────────────────────────────────────────────┤
│ Legend:                                             │
│ 🔵 Blue = BRENDA    🟣 Purple = SABIO-RK           │
│ 🟢 Green = KEGG DB  ⚫ Gray Italic = Heuristic      │
│ 🟠 Orange = User Edit                               │
└─────────────────────────────────────────────────────┘

Enrichment → Pathway Operations panel
Display → Report panel (read-only)
```

---

## 🚀 Benefits

1. **Complete Coverage**: Enzymatic (BRENDA) + Stochastic (SABIO-RK)
2. **Data Provenance**: Clear color coding for all data sources
3. **Smart Override**: Respects SBML curated data, overrides KEGG heuristics
4. **Dual Simulation**: Support both continuous (ODE) and stochastic (SSA)
5. **Consistent UX**: Same workflow as BRENDA enrichment

---

## 🌐 SABIO-RK API Reference

### Base URL
```
http://sabiork.h-its.org/sabioRestWebServices
```

### Key Endpoints

1. **Search by KEGG Reaction ID**
   ```
   GET /searchKineticLaws/sbml?q=KeggReactionID:R00200
   ```

2. **Search by EC Number**
   ```
   GET /searchKineticLaws/sbml?q=ECNumber:2.7.1.1
   ```

3. **Search by Substrates/Products**
   ```
   GET /searchKineticLaws/sbml?q=Substrate:glucose%20Product:glucose-6-phosphate
   ```

4. **Search by Compound IDs**
   ```
   GET /searchKineticLaws/sbml?q=KeggCompoundID:C00031+C00668
   ```

### Response Format
- Returns SBML with `<kineticLaw>` elements
- Contains `<parameter>` elements with k values
- Includes metadata: organism, temperature, pH, citations

---

## 📚 Alternative Databases

If SABIO-RK proves insufficient, consider:

1. **BioNumbers** (http://bionumbers.hms.harvard.edu/)
   - Best for individual rate constants
   - Excellent citations and conditions
   - REST API available

2. **BioModels** (https://www.ebi.ac.uk/biomodels/)
   - Extract rates from validated SBML models
   - 40,000+ curated models
   - REST API available

3. **JWS Online** (https://jjj.bio.vu.nl/)
   - Curated kinetic models
   - Focus on metabolism

---

## ⏱️ Estimated Time

| Phase | Time | Difficulty | Priority |
|-------|------|------------|----------|
| **Phase 0: Real BRENDA API** | **3-4 hours** | **Medium** | **HIGHEST ⚠️** |
| - Setup credentials | 30 mins | Easy | - |
| - Install zeep | 10 mins | Easy | - |
| - Implement SOAP calls | 2-3 hours | Medium | - |
| - Test & validate | 30 mins | Easy | - |
| **Step 1: UI Refactoring** | **2 hours** | **Medium** | **High** |
| - Move BRENDA to Pathway Ops | 1 hour | Medium | - |
| - Clean up Report panel | 30 mins | Easy | - |
| - Test callback wiring | 30 mins | Easy | - |
| Controller scaffold | 1 hour | Easy | Medium |
| Mock database | 30 mins | Easy | Low |
| API integration | 1 hour | Medium | Medium |
| Rate function gen | 1 hour | Medium | Medium |
| SABIO-RK category UI | 1 hour | Easy | Medium |
| Report display updates | 1 hour | Easy | Medium |
| Testing | 30 mins | Easy | High |
| Documentation | 30 mins | Easy | Low |
| **TOTAL** | **10-12 hours** | **Medium** | - |

**Note:** Phase 0 (Real BRENDA API) is now critical priority. Must be done before SABIO-RK to ensure enrichment architecture works with real data!

---

## 🎯 Success Criteria

- [ ] **UI Refactoring Complete**
  - [ ] BRENDA controls moved to `brenda_category.py`
  - [ ] Report panel controls removed (display only)
  - [ ] BRENDA enrichment still works from new location
  - [ ] Callbacks properly wired (Pathway Ops → Controller → Report refresh)
  
- [ ] **SABIO-RK Implementation**
  - [ ] SABIO-RK controller implemented with mock data
  - [ ] SABIO-RK category created in Pathway Operations panel
  - [ ] Stochastic transitions show purple k_forward/k_reverse values
  - [ ] Continuous transitions still show blue BRENDA values
  - [ ] Smart override works: KEGG auto-overridden, SBML protected
  - [ ] Rate functions auto-generated for stochastic reactions
  
- [ ] **Display & UX**
  - [ ] Report panel table expanded to 20 columns
  - [ ] Color legend updated in UI
  - [ ] Smart column hiding (show relevant params per type)
  - [ ] Both enrichments coexist without conflicts
  
- [ ] **Documentation**
  - [ ] User guide updated with new UI flow
  - [ ] SABIO-RK usage documented
  - [ ] Architecture diagram updated

---

**Next Steps Tomorrow:**
1. ⚠️ **START WITH PHASE 0**: Implement real BRENDA SOAP API integration
2. Register for BRENDA academic license (5 minutes online)
3. Install zeep and test SOAP client
4. Implement real API calls and verify different results from mock
5. Then proceed with UI refactoring (move to Pathway Operations)
6. Finally implement SABIO-RK with validated architecture

**Why Phase 0 is Critical:**
- Currently using hardcoded mock data (only 21 enzymes)
- Real BRENDA has 83,000+ enzymes with experimental data
- Need to validate enrichment workflow with real API before expanding to SABIO-RK
- Ensures proper error handling, rate limiting, credential management

**Current BRENDA Implementation:**
- `src/shypn/helpers/brenda_enrichment_controller.py` (reference architecture)
- ⚠️ `src/shypn/ui/panels/pathway_operations/brenda_category.py` (NEEDS REFACTORING - add controls here)
- ⚠️ `src/shypn/ui/panels/report/report_panel.py` (NEEDS REFACTORING - remove controls, keep display)
- `src/shypn/ui/panels/report/model_structure_category.py` (table display - add columns)
- `src/shypn/ui/panels/pathway_operations_panel.py` (add SABIO-RK to stack)

**To Be Created:**
- `src/shypn/helpers/sabio_rk_enrichment_controller.py` (NEW)
- `src/shypn/ui/panels/pathway_operations/sabio_rk_category.py` (NEW)
- `doc/SABIO_RK_USAGE.md` (NEW)

**Architecture Flow:**
```
User clicks "Enrich" in Pathway Operations
    ↓
BRENDA/SABIO-RK Category Panel
    ↓
brenda/sabio_enrichment_controller.py
    ↓
Updates transition metadata
    ↓
Report panel auto-refreshes (display only)
    ↓
Shows color-coded results
```

---

## 📝 Notes

- SABIO-RK has ~40,000 kinetic laws in database
- Most comprehensive for non-enzymatic reactions
- Good coverage of signaling pathways
- Less coverage than BRENDA for pure metabolism
- Consider combining both for complete coverage

---

**Next Steps Tomorrow:**
1. Start with Step 1: Create controller with mock database
2. Test architecture with existing BRENDA patterns
3. Validate color coding with sample data
