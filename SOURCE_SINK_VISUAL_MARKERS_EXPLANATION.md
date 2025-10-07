# Source/Sink Visual Markers - NOT A BUG!

## What You're Seeing

When you enable **source** or **sink** markers on a transition, visual arrow indicators appear on the transition:

### Source Transition (generates tokens externally)
```
    →|====|
     ^ This arrow appears on the LEFT (or TOP for vertical transitions)
```
- Arrow points INTO the transition from the left
- Indicates tokens are being generated from an external source
- This is INTENTIONAL visual feedback

### Sink Transition (consumes tokens externally)  
```
    |====|→
           ^ This arrow appears on the RIGHT (or BOTTOM for vertical transitions)
```
- Arrow points OUT OF the transition to the right
- Indicates tokens are being consumed by an external sink
- This is INTENTIONAL visual feedback

## These Are NOT Petri Net Arcs!

The arrows you see are **visual markers** to help you identify source/sink transitions at a glance. They are:
- Part of the transition rendering
- Not selectable or deletable
- Only visible when the `Source` or `Sink` checkbox is enabled in properties
- Different from Petri net arcs (which connect places to transitions)

## How to Remove Them

If you don't want these visual markers:
1. Double-click the transition to open properties
2. Uncheck the "Source" or "Sink" checkbox in the Basic Properties tab
3. Click OK

The arrows will disappear when the checkboxes are unchecked.

## Why Do They Appear?

Source and sink transitions behave differently in simulation:
- **Source**: Fires without consuming tokens from input places (generates tokens)
- **Sink**: Fires without producing tokens to output places (consumes tokens)

The visual markers help you quickly identify which transitions have this special behavior without having to open the properties dialog.

## If You're Seeing Unwanted Markers

If markers appear when you haven't checked the source/sink boxes:
1. Open the transition properties
2. Verify the Source/Sink checkboxes are UNCHECKED
3. If they're checked but you didn't check them, this is a bug - please report it

If the checkboxes match the visual markers you see, everything is working correctly!

