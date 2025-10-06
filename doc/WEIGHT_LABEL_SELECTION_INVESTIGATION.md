# Weight Label Selection Issue

## Problem Report

"In a P-arc->T, and selecting P the last text inserted gets selected (blue line from P to text) altogether"

## Possible Interpretations

### Interpretation 1: Text Rectangle Overlaps Place
The weight label (with its white background rectangle) might be positioned so close to the Place that clicking on the Place also appears to select the text area visually.

### Interpretation 2: Weight Label Not Being Filtered
The weight rendering might be creating clickable geometry that's being picked up by the selection system.

### Interpretation 3: Visual Artifact
The white background rectangle of the weight label might be creating a visual selection artifact when the Place is selected.

## Investigation Needed

Need clarification from user:
1. Is the weight NUMBER (e.g., "3", "5") appearing as a separate selectable object?
2. Does clicking on the Place cause the weight text to also appear selected?
3. Is there a blue line drawn from the Place center to the weight text position?
4. Does this happen with straight arcs, curved arcs, or both?

## Potential Solutions

### Solution 1: Increase Offset Distance
Move weight labels further away from nodes to avoid visual overlap.

### Solution 2: Don't Render Weight on Short Arcs
Skip weight rendering if the arc is too short (nodes are very close).

### Solution 3: Check for Overlap
Before rendering weight, check if it would overlap with source or target geometry.

### Solution 4: Render Order
Ensure weight labels are rendered AFTER selection highlights, not before.

## Awaiting More Information

Need user to clarify the exact behavior to implement the correct fix.
