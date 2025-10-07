# Palette Appearance Comparison Analysis

## Overview
This document compares the visual design and implementation differences between the Zoom Palette and the Edit Palettes (Tools and Operations) in the shypn application.

---

## 1. ZOOM PALETTE

### Location
- **Position**: Bottom-right corner of canvas
- **Positioning**: `halign="end"`, `valign="end"`
- **Margins**: `margin-end="12"`, `margin-bottom="12"`

### Structure Type
- **Container Type**: `GtkBox` (direct container, no revealer wrapper)
- **Layout**: Horizontal orientation
- **Components**: 
  - Zoom Out button (−)
  - Zoom Level Display (100%)
  - Zoom In button (+)
  - Expandable Revealer with preset zoom levels (25%, 50%, 75%, 100%, 150%, 200%, 400%, Fit)

### Visual Appearance

#### Background
```css
background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
```
- **Type**: Purple/violet gradient
- **Colors**: Blue-purple (#667eea) to deep purple (#764ba2)
- **Style**: Vibrant, colorful, eye-catching

#### Border & Frame
```css
border: 2px solid #5568d3;
border-radius: 8px;
padding: 3px;
```
- **Border**: 2px solid blue (#5568d3)
- **Corners**: 8px rounded (more rounded)
- **Padding**: 3px internal spacing

#### Shadow Effect
```css
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
            0 2px 4px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
```
- **Type**: Triple-layer shadow
- **Outer shadows**: Two layers creating depth (4px and 2px blur)
- **Inset shadow**: White highlight on top edge (0.2 opacity)
- **Effect**: Strong 3D floating effect with inner glow

#### Button Styling
```css
.zoom-button {
    background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
    border: 2px solid #5568d3;
    color: #667eea;
    font-size: 18px;
}

.zoom-button:hover {
    background: linear-gradient(to bottom, #e8f0ff 0%, #d5e5ff 100%);
    box-shadow: 0 0 8px rgba(102, 126, 234, 0.5);
}
```
- **Buttons**: White to light gray gradient
- **Hover**: Light blue gradient with glow effect
- **Size**: 28px × 28px
- **Font**: Bold, 18px
- **Color**: Purple (#667eea)

---

## 2. EDIT PALETTES (Tools & Operations)

### Location
- **Tools Palette**: Bottom-center with `margin-end="352"` (left of center)
- **Operations Palette**: Bottom-center with `margin-start="202"` (right of center)
- **Gap Between**: ~180px (5 button widths)

### Structure Type
- **Container Type**: `GtkRevealer` → `GtkFrame` → `GtkBox`
- **Revealer**: Controls show/hide with slide-up animation
- **Frame**: Provides border and structure
- **Layout**: Horizontal orientation

### Visual Appearance

#### Background
```css
background-color: #E8E8E8;
```
- **Type**: Solid color (no gradient)
- **Color**: Light gray (#E8E8E8)
- **Style**: Subtle, neutral, professional

#### Border & Frame
```css
border: 1px solid #B0B0B0;
border-radius: 4px;
```
- **Frame Type**: `GtkFrame` with `shadow-type="out"`
- **Border**: 1px solid medium gray (#B0B0B0)
- **Corners**: 4px rounded (less rounded)
- **Padding**: 6px margin inside container

#### Shadow Effect
- **GTK Native**: `shadow-type="out"` provides 3D raised/embossed effect
- **CSS Border**: Creates definition against background
- **Type**: GTK's built-in frame shadow (subtle 3D relief)
- **Effect**: Modest raised appearance, not floating

#### Button Styling
- **No Custom CSS**: Uses default GTK theme button styling
- **Size**: 36px × 36px
- **Spacing**: 6px between buttons
- **Colors**: System default (typically light gray with blue accents when active)
- **Font**: Standard system font

---

## 3. KEY DIFFERENCES

### Design Philosophy

| Aspect | Zoom Palette | Edit Palettes |
|--------|-------------|---------------|
| **Visual Impact** | High - vibrant, colorful | Low - subtle, neutral |
| **Styling Approach** | Custom CSS with gradients | Native GTK with minimal CSS |
| **Color Scheme** | Purple/violet gradient | Light gray solid |
| **Shadow Type** | CSS box-shadow (multi-layer) | GTK frame shadow (native) |
| **Container** | Direct box | Revealer + Frame wrapper |

### Technical Implementation

| Feature | Zoom Palette | Edit Palettes |
|---------|-------------|---------------|
| **Background** | Gradient CSS | Solid color CSS |
| **Border Width** | 2px | 1px |
| **Border Radius** | 8px (rounder) | 4px (subtle) |
| **Shadow Layers** | 3 (2 outer + 1 inset) | 1 (GTK native) |
| **Button Gradients** | Yes (white→gray) | No (system default) |
| **Hover Effects** | Custom glow animation | System default |
| **Inset Highlight** | Yes (white glow on top) | No |

### Visual Effects Comparison

#### Zoom Palette Effects:
1. **Gradient Background**: Creates depth and visual interest
2. **Multi-layer Shadow**: Strong 3D floating effect
3. **Inset Highlight**: Simulates light reflection on top edge
4. **Hover Glow**: Blue glow effect on interaction
5. **Gradient Buttons**: Subtle depth on each control

**Result**: **Highly visible, distinctive, "floating" appearance**

#### Edit Palettes Effects:
1. **Solid Background**: Clean, minimal appearance
2. **GTK Frame Shadow**: Subtle 3D embossed effect
3. **Single Border**: Clear definition
4. **No Custom Hovers**: Standard system behavior
5. **Flat Buttons**: Clean, modern look

**Result**: **Professional, understated, "anchored" appearance**

---

## 4. POSITIONING & BEHAVIOR

### Zoom Palette
- **Always Visible**: No revealer on main control
- **Fixed Position**: Bottom-right corner
- **Expandable**: Revealer shows preset zoom levels upward
- **Animation**: `slide-down` for revealer (200ms)

### Edit Palettes
- **Toggle Visibility**: Controlled by [E] button
- **Centered Position**: Bottom-center with horizontal offsets
- **Side-by-side**: Two separate palettes with large gap
- **Animation**: `slide-up` for both (200ms)

---

## 5. USE CASE & PURPOSE

### Zoom Palette
- **Purpose**: Frequent zoom control during work
- **Priority**: High visibility and quick access
- **Style Justification**: Colorful to stand out, always accessible
- **User Pattern**: Used constantly throughout workflow

### Edit Palettes
- **Purpose**: Tool selection and operations when editing
- **Priority**: Available when needed, hidden when not
- **Style Justification**: Subtle to not distract from canvas
- **User Pattern**: Toggled on/off as needed for editing mode

---

## 6. SUMMARY

### Zoom Palette = **"Floating Jewel"**
- Vibrant purple gradient background
- Multi-layer shadow with inset highlight
- Strong 3D floating effect
- Custom gradient buttons with glow
- Always visible, high visual priority

### Edit Palettes = **"Professional Toolbar"**
- Neutral light gray background
- Subtle GTK frame shadow
- Modest raised/embossed effect
- Standard system button styling
- Toggle visibility, low visual distraction

### Design Rationale
- **Zoom**: Needs to be visible and accessible at all times → colorful and distinctive
- **Edit**: Should be available but not distracting → neutral and professional
- **Result**: Each palette's appearance matches its functional importance in the workflow
