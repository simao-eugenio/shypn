"""KGML (KEGG Markup Language) XML parser.

This module parses KGML XML data from the KEGG API into structured
KEGGPathway objects.

KGML Format Documentation:
https://www.kegg.jp/kegg/xml/docs/
"""

import xml.etree.ElementTree as ET
from typing import Optional
from .models import (
    KEGGPathway,
    KEGGEntry,
    KEGGReaction,
    KEGGRelation,
    KEGGGraphics,
    KEGGSubstrate,
    KEGGProduct,
    KEGGRelationSubtype
)


class KGMLParser:
    """Parser for KGML XML format.
    
    Converts KGML XML from KEGG API into KEGGPathway objects.
    """
    
    def __init__(self):
        """Initialize KGML parser."""
        pass
    
    def parse(self, kgml_xml: str) -> KEGGPathway:
        """Parse KGML XML string into KEGGPathway object.
        
        Args:
            kgml_xml: KGML XML string from KEGG API
            
        Returns:
            KEGGPathway object with all pathway data
            
        Raises:
            ET.ParseError: If XML is malformed
            ValueError: If required attributes are missing
        """
        root = ET.fromstring(kgml_xml)
        
        # Extract pathway attributes
        pathway_attrs = root.attrib
        pathway = KEGGPathway(
            name=pathway_attrs.get('name', ''),
            org=pathway_attrs.get('org', ''),
            number=pathway_attrs.get('number', ''),
            title=pathway_attrs.get('title', ''),
            image=pathway_attrs.get('image', ''),
            link=pathway_attrs.get('link', '')
        )
        
        # Parse entries
        for entry_elem in root.findall('entry'):
            entry = self._parse_entry(entry_elem)
            if entry:
                pathway.entries[entry.id] = entry
        
        # Parse reactions
        for reaction_elem in root.findall('reaction'):
            reaction = self._parse_reaction(reaction_elem)
            if reaction:
                pathway.reactions.append(reaction)
        
        # Parse relations
        for relation_elem in root.findall('relation'):
            relation = self._parse_relation(relation_elem)
            if relation:
                pathway.relations.append(relation)
        
        return pathway
    
    def _parse_entry(self, elem: ET.Element) -> Optional[KEGGEntry]:
        """Parse an entry element.
        
        Args:
            elem: XML element for entry
            
        Returns:
            KEGGEntry object or None if parsing fails
        """
        try:
            attrs = elem.attrib
            entry = KEGGEntry(
                id=attrs['id'],
                name=attrs['name'],
                type=attrs['type'],
                reaction=attrs.get('reaction'),
                link=attrs.get('link')
            )
            
            # Parse graphics sub-element
            graphics_elem = elem.find('graphics')
            if graphics_elem is not None:
                entry.graphics = self._parse_graphics(graphics_elem)
            
            # Parse components for group entries
            for component_elem in elem.findall('component'):
                component_id = component_elem.attrib.get('id')
                if component_id:
                    entry.components.append(component_id)
            
            return entry
            
        except KeyError as e:
            print(f"Warning: Missing required entry attribute: {e}")
            return None
    
    def _parse_graphics(self, elem: ET.Element) -> KEGGGraphics:
        """Parse a graphics element.
        
        Args:
            elem: XML element for graphics
            
        Returns:
            KEGGGraphics object
        """
        attrs = elem.attrib
        return KEGGGraphics(
            name=attrs.get('name', ''),
            x=float(attrs.get('x', 0)),
            y=float(attrs.get('y', 0)),
            width=float(attrs.get('width', 46)),
            height=float(attrs.get('height', 17)),
            fgcolor=attrs.get('fgcolor', '#000000'),
            bgcolor=attrs.get('bgcolor', '#FFFFFF'),
            type=attrs.get('type', 'rectangle')
        )
    
    def _parse_reaction(self, elem: ET.Element) -> Optional[KEGGReaction]:
        """Parse a reaction element.
        
        Args:
            elem: XML element for reaction
            
        Returns:
            KEGGReaction object or None if parsing fails
        """
        try:
            attrs = elem.attrib
            reaction = KEGGReaction(
                id=attrs['id'],
                name=attrs['name'],
                type=attrs['type']
            )
            
            # Parse substrates
            for substrate_elem in elem.findall('substrate'):
                substrate_attrs = substrate_elem.attrib
                substrate = KEGGSubstrate(
                    id=substrate_attrs['id'],
                    name=substrate_attrs['name']
                )
                reaction.substrates.append(substrate)
            
            # Parse products
            for product_elem in elem.findall('product'):
                product_attrs = product_elem.attrib
                product = KEGGProduct(
                    id=product_attrs['id'],
                    name=product_attrs['name']
                )
                reaction.products.append(product)
            
            return reaction
            
        except KeyError as e:
            print(f"Warning: Missing required reaction attribute: {e}")
            return None
    
    def _parse_relation(self, elem: ET.Element) -> Optional[KEGGRelation]:
        """Parse a relation element.
        
        Args:
            elem: XML element for relation
            
        Returns:
            KEGGRelation object or None if parsing fails
        """
        try:
            attrs = elem.attrib
            relation = KEGGRelation(
                entry1=attrs['entry1'],
                entry2=attrs['entry2'],
                type=attrs['type']
            )
            
            # Parse subtypes
            for subtype_elem in elem.findall('subtype'):
                subtype_attrs = subtype_elem.attrib
                subtype = KEGGRelationSubtype(
                    name=subtype_attrs['name'],
                    value=subtype_attrs.get('value', '')
                )
                relation.subtypes.append(subtype)
            
            return relation
            
        except KeyError as e:
            print(f"Warning: Missing required relation attribute: {e}")
            return None


# Convenience function for standalone use
def parse_kgml(kgml_xml: str) -> KEGGPathway:
    """Parse KGML XML string (convenience function).
    
    Args:
        kgml_xml: KGML XML string from KEGG API
        
    Returns:
        KEGGPathway object
    """
    parser = KGMLParser()
    return parser.parse(kgml_xml)
