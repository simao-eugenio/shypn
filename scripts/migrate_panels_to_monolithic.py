#!/usr/bin/env python3
"""
Phase 2: Panel Content Migration Script
Extracts panel content from old .ui files and embeds into main_window.ui containers
"""

import xml.etree.ElementTree as ET
import sys
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
UI_DIR = REPO_ROOT / "ui"
PANELS_DIR = UI_DIR / "panels"
MAIN_WINDOW_PATH = UI_DIR / "main" / "main_window.ui"

# Panel mappings: old_ui_file -> (container_id, content_object_id)
PANEL_MAPPINGS = {
    "left_panel.ui": ("files_panel_container", "left_panel_content"),
    "right_panel.ui": ("analyses_panel_container", "right_panel_content"),
    "pathway_panel.ui": ("pathways_panel_container", "pathway_panel_content"),
    "topology_panel.ui": ("topology_panel_container", "topology_content"),
}

def extract_panel_content(panel_ui_path, content_id):
    """Extract the content GtkBox from a panel .ui file.
    
    Skips the panel header (float button, title) since those aren't needed in monolithic mode.
    Extracts only the functional content widgets PLUS any referenced objects (like GtkAdjustment).
    Renames certain IDs to avoid conflicts.
    
    Args:
        panel_ui_path: Path to the old panel .ui file
        content_id: ID of the content object to extract (e.g., "left_panel_content")
        
    Returns:
        Tuple: (list of child elements, list of referenced objects) or (None, None) if not found
    """
    try:
        tree = ET.parse(panel_ui_path)
        root = tree.getroot()
        
        # Determine panel prefix from content_id
        panel_name = content_id.replace('_panel_content', '').replace('_content', '')
        
        # First, collect all top-level objects (adjustments, list stores, etc.)
        referenced_objects = []
        for obj in root.findall('./object'):
            obj_id = obj.get('id')
            # Collect non-window objects that might be referenced
            if obj.get('class') != 'GtkWindow' and obj_id != content_id:
                # Rename the ID to avoid conflicts
                if obj_id:
                    new_id = f"{panel_name}_{obj_id}"
                    print(f"    Including referenced object: {obj_id} -> {new_id}")
                    obj.set('id', new_id)
                    
                    # Also update any references to this ID in the tree
                    # This is tricky - we'll need to update references after extraction
                    
                referenced_objects.append(obj)
        
        # Find the content object by ID
        for obj in root.iter('object'):
            if obj.get('id') == content_id:
                print(f"  Found content object: {content_id}")
                
                # Extract children, but skip the panel header
                functional_children = []
                skipped_header = False
                skip_next_separator = False
                
                for child in obj:
                    if child.tag == 'child':
                        # Check if this child contains a panel header to skip
                        header_obj = child.find(".//object[@id='panel_header']")
                        float_button_obj = child.find(".//object[@id='float_button']")
                        
                        if header_obj is not None or float_button_obj is not None:
                            print(f"    Skipping panel header/float button")
                            skipped_header = True
                            skip_next_separator = True
                            continue
                        
                        # Skip the separator right after header (only the first one)
                        if skip_next_separator:
                            separator = child.find(".//object[@class='GtkSeparator']")
                            if separator is not None:
                                print(f"    Skipping separator after header")
                                skip_next_separator = False
                                continue
                        
                        # Update references to renamed objects in this child
                        for prop in child.iter('property'):
                            if prop.text in [obj.get('id').replace(f"{panel_name}_", '') for obj in referenced_objects if obj.get('id')]:
                                old_ref = prop.text
                                new_ref = f"{panel_name}_{old_ref}"
                                print(f"    Updating reference: {old_ref} -> {new_ref}")
                                prop.text = new_ref
                        
                        # Rename potentially conflicting IDs in widgets
                        for descendant in child.iter('object'):
                            obj_id = descendant.get('id')
                            if obj_id:
                                # List of IDs that might conflict with main window
                                conflict_ids = ['status_bar', 'panel_header', 'float_button']
                                if obj_id in conflict_ids:
                                    new_id = f"{panel_name}_{obj_id}"
                                    print(f"    Renaming '{obj_id}' -> '{new_id}'")
                                    descendant.set('id', new_id)
                        
                        functional_children.append(child)
                
                print(f"  Extracted {len(functional_children)} functional widgets{' (skipped header)' if skipped_header else ''}")
                return functional_children, referenced_objects
        
        print(f"  WARNING: Content object '{content_id}' not found in {panel_ui_path}")
        return None, None
        
    except Exception as e:
        print(f"  ERROR reading {panel_ui_path}: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def embed_content_in_container(main_tree, container_id, content_elements, referenced_objects):
    """Embed extracted content into a container in main_window.ui.
    Also adds referenced objects at the interface root level.
    
    Args:
        main_tree: ElementTree of main_window.ui
        container_id: ID of the container to populate
        content_elements: List of XML elements to insert into container
        referenced_objects: List of referenced objects to add at root level
        
    Returns:
        True if successful, False otherwise
    """
    root = main_tree.getroot()
    
    # First, add referenced objects at the root level (before main window)
    if referenced_objects:
        # The root IS the <interface> element
        # Find the GtkApplicationWindow
        main_window = root.find('./object[@class="GtkApplicationWindow"]')
        if main_window is not None:
            # Insert referenced objects BEFORE the main window
            window_index = list(root).index(main_window)
            for i, obj in enumerate(referenced_objects):
                root.insert(window_index + i, obj)
            print(f"  Added {len(referenced_objects)} referenced objects at interface root")
        else:
            print(f"  WARNING: Could not find GtkApplicationWindow to insert objects before")
    
    # Now find the container and add content
    for obj in root.iter('object'):
        if obj.get('id') == container_id:
            print(f"  Found container: {container_id}")
            
            # Check if container already has content
            existing_children = [child for child in obj if child.tag == 'child']
            if existing_children:
                print(f"  WARNING: Container already has {len(existing_children)} children, replacing...")
                for child in existing_children:
                    obj.remove(child)
            
            # Add the new content
            for element in content_elements:
                obj.append(element)
            
            print(f"  Embedded {len(content_elements)} elements into {container_id}")
            return True
    
    print(f"  ERROR: Container '{container_id}' not found in main_window.ui")
    return False

def migrate_panels():
    """Main migration function."""
    print("=" * 70)
    print("Phase 2: Panel Content Migration")
    print("=" * 70)
    
    # Load main_window.ui
    print(f"\nLoading main_window.ui from: {MAIN_WINDOW_PATH}")
    try:
        main_tree = ET.parse(MAIN_WINDOW_PATH)
        print("  ✓ Loaded successfully")
    except Exception as e:
        print(f"  ✗ ERROR: {e}")
        return False
    
    # Process each panel
    success_count = 0
    for panel_file, (container_id, content_id) in PANEL_MAPPINGS.items():
        print(f"\n--- Processing {panel_file} ---")
        panel_path = PANELS_DIR / panel_file
        
        if not panel_path.exists():
            print(f"  ✗ File not found: {panel_path}")
            continue
        
        # Extract content from old panel (returns tuple: content_elements, referenced_objects)
        result = extract_panel_content(panel_path, content_id)
        if result is None or result[0] is None:
            print(f"  ✗ Failed to extract content from {panel_file}")
            continue
        
        content_elements, referenced_objects = result
        
        # Embed content into main_window.ui container
        if embed_content_in_container(main_tree, container_id, content_elements, referenced_objects):
            success_count += 1
            print(f"  ✓ Successfully migrated {panel_file}")
        else:
            print(f"  ✗ Failed to embed content into {container_id}")
    
    # Save updated main_window.ui
    if success_count > 0:
        backup_path = MAIN_WINDOW_PATH.with_suffix('.ui.pre_migration')
        print(f"\n--- Saving Results ---")
        print(f"Backing up to: {backup_path}")
        main_tree.write(backup_path, encoding='UTF-8', xml_declaration=True)
        
        print(f"Writing updated main_window.ui")
        main_tree.write(MAIN_WINDOW_PATH, encoding='UTF-8', xml_declaration=True)
        
        print(f"\n✓ Migration complete! {success_count}/{len(PANEL_MAPPINGS)} panels migrated")
        return True
    else:
        print(f"\n✗ Migration failed - no panels were migrated")
        return False

if __name__ == "__main__":
    success = migrate_panels()
    sys.exit(0 if success else 1)
