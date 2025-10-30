# Rate Function Plot Preview in Transition Properties Dialog

**Date:** October 30, 2025  
**Feature:** Automatic matplotlib plot preview for rate functions in transition properties dialog

## Overview

Added real-time matplotlib plotting to the Transition Properties Dialog that automatically:
- ✅ Detects the type of rate function (Hill, Michaelis-Menten, Sigmoid, Exponential, etc.)
- ✅ Adjusts X-axis range based on function characteristics
- ✅ Shows appropriate parameter annotations (Kd, Vmax, Km, etc.)
- ✅ Updates plot in real-time as user types
- ✅ Handles errors gracefully with informative messages

## Function Types Detected

### 1. **Hill Equation**
```python
hill_equation(P1, vmax=10, kd=5, n=2)
```
**Plot Configuration:**
- X-axis: 0 to 4×Kd (concentration range)
- Y-axis: 0 to 1.2×Vmax
- Annotations: Vertical line at Kd showing half-maximal response
- Labels: "Concentration (P1)" vs "Reaction Rate (v)"

### 2. **Michaelis-Menten**
```python
michaelis_menten(P1, vmax=10, km=5)
```
**Plot Configuration:**
- X-axis: 0 to 4×Km (substrate range)
- Y-axis: 0 to 1.2×Vmax
- Annotations: Vertical line at Km showing V=Vmax/2
- Labels: "Substrate [P1]" vs "Velocity (v)"

### 3. **Sigmoid/Logistic**
```python
sigmoid(t, 10, 0.5)
```
**Plot Configuration:**
- X-axis: 0 to 2×center (time range)
- Y-axis: 0 to 1.2 (normalized)
- Annotations: Vertical line at center (inflection point)
- Labels: "Time (t)" vs "Rate"

### 4. **Exponential Growth**
```python
math.exp(0.1 * t)
```
**Plot Configuration:**
- X-axis: 0 to 50 (default time range)
- Y-axis: Auto-scaled to function output
- Labels: "Time (t)" vs "Rate"

### 5. **Exponential Decay**
```python
math.exp(-0.1 * t)
```
**Plot Configuration:**
- X-axis: 0 to 50 (decay period)
- Y-axis: 0 to 1.2×initial_value
- Labels: "Time (t)" vs "Rate"

### 6. **Linear/Polynomial**
```python
0.5 * P1
2.0 * P1 + 3.0
```
**Plot Configuration:**
- X-axis: 0 to 20 (default range)
- Y-axis: Auto-scaled
- Labels: Based on variable detected

### 7. **Constant**
```python
5.0
```
**Plot Configuration:**
- X-axis: 0 to 10 (time)
- Y-axis: 0 to 1.2×constant
- Horizontal line showing constant rate

## Implementation

### File Changes

#### 1. `src/shypn/helpers/transition_prop_dialog_loader.py`

Added new methods:

```python
def _setup_rate_function_plot(self):
    """Setup matplotlib plot widget for rate function preview."""
    # Create matplotlib figure and canvas
    # Insert into dialog layout
    # Connect to rate_textview changes

def _update_rate_plot(self, buffer=None):
    """Update plot based on current rate function text."""
    # Parse rate function
    # Detect function type
    # Configure appropriate X/Y ranges
    # Add annotations
    # Render plot

def _detect_function_type(self, expr_str):
    """Detect the type of rate function from expression string."""
    # Returns: ('hill', {'vmax': 10, 'kd': 5, 'n': 2})
    # Or: ('michaelis_menten', {'vmax': 10, 'km': 5})
    # Or: ('sigmoid', {'center': 10, 'steepness': 0.5})
    # etc.

def _plot_hill_equation(self, params):
    """Plot Hill equation with appropriate scaling."""
    # X-axis: 0 to 4×kd
    # Show Kd annotation line
    # Label axes appropriately

def _plot_michaelis_menten(self, params):
    """Plot Michaelis-Menten with appropriate scaling."""
    # X-axis: 0 to 4×km
    # Show Km annotation line

def _plot_sigmoid(self, params):
    """Plot sigmoid with appropriate scaling."""
    # X-axis: 0 to 2×center
    # Show inflection point

def _plot_exponential(self, params, decay=False):
    """Plot exponential growth or decay."""
    # Auto-detect decay vs growth
    # Scale appropriately

def _plot_generic(self, expr_str):
    """Plot generic expression with default range."""
    # Use safe defaults
    # Auto-scale axes
```

#### 2. UI Integration

The plot widget is inserted in the Behavior tab, after the rate function TextView:

```
┌─ Behavior Tab ─────────────────────────────────┐
│                                                 │
│  Guard Function:                                │
│  ┌───────────────────────────────────────────┐ │
│  │ P1 > 5 and t > 10                         │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Rate Function:                                 │
│  ┌───────────────────────────────────────────┐ │
│  │ hill_equation(P1, vmax=10, kd=5, n=2)     │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  Function Preview:  [NEW!]                      │
│  ┌───────────────────────────────────────────┐ │
│  │         Hill Equation Plot                 │ │
│  │   Vmax = 10, Kd = 5, n = 2                 │ │
│  │                                             │ │
│  │   10 |                  ____________       │ │
│  │      |               __/                    │ │
│  │    5 |          ___/  │                     │ │
│  │      |      ___/      │ Kd = 5              │ │
│  │    0 |_____/__________|__________           │ │
│  │        0    5    10   15   20               │ │
│  │            Concentration (P1)               │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

## Usage

### For Users:

1. Open Transition Properties dialog (right-click transition → Properties)
2. Navigate to "Behavior" tab
3. Type a rate function in the "Rate Function" field
4. **Plot updates automatically** as you type
5. See the function shape, parameters, and key points annotated

### Examples:

**Type:** `hill_equation(P1, vmax=10, kd=5, n=2)`  
**See:** S-curve with Kd=5 marked, showing cooperative binding

**Type:** `michaelis_menten(P1, vmax=15, km=3)`  
**See:** Hyperbolic curve with Km=3 marked, showing enzyme saturation

**Type:** `sigmoid(t, 10, 0.5)`  
**See:** S-curve over time, inflection at t=10

**Type:** `math.exp(0.2 * t)`  
**See:** Exponential growth curve

**Type:** `5.0`  
**See:** Flat line at y=5

## Technical Details

### Function Detection Algorithm

```python
def _detect_function_type(self, expr_str):
    """Intelligent function type detection using regex and AST parsing."""
    
    # 1. Check for known function names
    if 'hill_equation' in expr_str:
        # Extract parameters: vmax, kd, n
        # Return ('hill', params)
    
    elif 'michaelis_menten' in expr_str:
        # Extract parameters: vmax, km
        # Return ('michaelis_menten', params)
    
    elif 'sigmoid' in expr_str:
        # Extract parameters: center, steepness
        # Return ('sigmoid', params)
    
    # 2. Check for exponential patterns
    elif 'math.exp' in expr_str or 'exp(' in expr_str:
        # Detect growth vs decay from sign
        # Return ('exponential', {'rate': k, 'decay': bool})
    
    # 3. Check for polynomial patterns
    elif re.match(r'[\d\.]+\s*\*\s*[A-Za-z_]\w*', expr_str):
        # Linear: "0.5 * P1"
        # Return ('linear', {'slope': a, 'var': 'P1'})
    
    # 4. Constant
    elif expr_str.replace('.', '').isdigit():
        # Return ('constant', {'value': float(expr_str)})
    
    # 5. Unknown/complex
    else:
        # Return ('generic', {})
```

### Axis Scaling Rules

| Function Type | X-axis Range | Y-axis Range |
|---------------|--------------|--------------|
| Hill | 0 to 4×Kd | 0 to 1.2×Vmax |
| Michaelis-Menten | 0 to 4×Km | 0 to 1.2×Vmax |
| Sigmoid | 0 to 2×center | 0 to 1.2 |
| Exponential Growth | 0 to 50 | Auto-scaled |
| Exponential Decay | 0 to 50 | 0 to 1.2×initial |
| Linear | 0 to 20 | Auto-scaled |
| Constant | 0 to 10 | 0 to 1.2×value |

### Error Handling

The plot gracefully handles:
- ✅ Syntax errors → Shows error message in plot area
- ✅ Missing parameters → Uses default values
- ✅ Invalid parameter types → Shows warning
- ✅ Unknown functions → Falls back to generic plot
- ✅ Empty input → Shows "Enter a rate function" message

## Benefits

### 1. **Immediate Visual Feedback**
- See the exact shape of your rate function
- Understand parameter effects instantly
- Catch mistakes before simulation

### 2. **Educational**
- Learn how parameters affect function shape
- Understand cooperative binding (Hill n parameter)
- Visualize enzyme kinetics concepts

### 3. **Professional Quality**
- Matplotlib plots match scientific standards
- Proper axis labels and units
- Parameter annotations for key points

### 4. **Productivity**
- No need to run simulation to see function behavior
- Iterate on parameters quickly
- Compare different functions side-by-side

## Future Enhancements

Potential improvements:

1. **Multi-Variable Plots**
   - 3D surface plots for functions with 2+ variables
   - Contour plots for complex dependencies

2. **Parameter Sliders**
   - Interactive sliders to adjust parameters
   - See plot update in real-time

3. **Function Library**
   - Dropdown with common function templates
   - One-click insertion of standard kinetics

4. **Export**
   - Save plot as PNG/PDF
   - Copy function code to clipboard

5. **Comparison Mode**
   - Overlay multiple functions
   - Compare parameter effects

## Compatibility

- ✅ GTK3 integration
- ✅ Matplotlib 3.x
- ✅ Python 3.x
- ✅ All existing transition types
- ✅ All rate function syntax

## Testing

Run: `python3 test_rate_function_plot_preview.py`

Test cases:
1. Hill equation with various n values (1, 2, 4)
2. Michaelis-Menten with different Km values
3. Sigmoid with different centers and steepness
4. Exponential growth and decay
5. Linear functions
6. Constants
7. Complex expressions
8. Syntax errors
9. Empty input
10. Real-time updates as typing

## Summary

This feature brings professional-grade function visualization directly into the properties dialog, making it easy to design and understand complex biochemical rate functions. The automatic function type detection and smart axis scaling ensure that users always see meaningful, well-scaled plots regardless of the function complexity.

**Status:** ✅ **READY TO IMPLEMENT**
