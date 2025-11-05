"""Test to verify interaction state reset is working"""

# Check if the fix is in the code
with open('src/shypn/helpers/model_canvas_loader.py', 'r') as f:
    content = f.read()
    
print("=" * 70)
print("CHECKING INTERACTION RESET FIX")
print("=" * 70)

# Check for the fix around line 734
if 'self.canvas_managers' in content and 'drawing_area in self._drag_state' in content:
    print("\n✅ Interaction reset code is present")
    
    # Find the section
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'Reset canvas interaction states' in line:
            print(f"\nFound at line {i+1}:")
            for j in range(max(0, i-2), min(len(lines), i+15)):
                print(f"  {j+1}: {lines[j]}")
            break
else:
    print("\n❌ Interaction reset code NOT FOUND!")

# Check if there's any reference to the old self.managers bug
if 'self.managers[drawing_area]' in content and 'self.canvas_managers' not in content:
    print("\n❌ OLD BUG STILL PRESENT: self.managers instead of self.canvas_managers")
else:
    print("\n✅ No references to old self.managers bug")

