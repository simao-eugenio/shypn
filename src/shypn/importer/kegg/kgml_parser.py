"""KGML (KEGG Markup Language) XML parser.

This module parses KGML XML files and converts them into structured
Python objects representing pathway elements.

KGML Specification: https://www.kegg.jp/kegg/xml/
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
    """Parser for KGML (KEGG Markup Language) XML files."""
    
    def parse(self, kgml_xml: str) -> Optional[KEGGPathway]:
        """Parse KGML XML string into KEGGPathway object.
        
        Args:
            kgml_xml: KGML XML content as string
            
        Returns:
            KEGGPathway object or None on error
            
        Example:
            >>> parser = KGMLParser()
            >>> pathway = parser.parse(kgml_xml_string)
            >>> print(pathway.title)
            'Glycolysis / Gluconeogenesis'
        """
        try:
            root = ET.fromstring(kgml_xml)
            return self._parse_pathway(root)
        except ET.ParseError as e:
            return None
        except Exception as e:
            return None
    
    def parse_file(self, filepath: str) -> Optional[KEGGPathway]:
        """Parse KGML XML file.
        
        Args:
            filepath: Path to KGML XML file
            
        Returns:
            KEGGPathway object or None on error
        """
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            return self._parse_pathway(root)
        except Exception as e:
            return None
    
    def _parse_pathway(self, root: ET.Element) -> KEGGPathway:
        """Parse pathway root element.
        
        Args:
            root: XML root element (<pathway>)
            
        Returns:
            KEGGPathway object
        """
        pathway = KEGGPathway(
            number=root.attrib.get('number', ''),
            name=root.attrib.get('name', ''),
            org=root.attrib.get('org', ''),
            title=root.attrib.get('title', ''),
            image=root.attrib.get('image', ''),
            link=root.attrib.get('link', '')
        )
        
        # Parse entries
        for entry_elem in root.findall('entry'):
            entry = self._parse_entry(entry_elem)
            pathway.entries[entry.id] = entry
        
        # Parse reactions
        for reaction_elem in root.findall('reaction'):
            reaction = self._parse_reaction(reaction_elem)
            pathway.reactions.append(reaction)
        
        # Parse relations
        for relation_elem in root.findall('relation'):
            relation = self._parse_relation(relation_elem)
            pathway.relations.append(relation)
        
        
        return pathway
    
    def _parse_entry(self, elem: ET.Element) -> KEGGEntry:
        """Parse entry element.
        
        Args:
            elem: <entry> XML element
            
        Returns:
            KEGGEntry object
        """
        entry = KEGGEntry(
            id=elem.attrib.get('id', ''),
            name=elem.attrib.get('name', ''),
            type=elem.attrib.get('type', ''),
            reaction=elem.attrib.get('reaction'),
            link=elem.attrib.get('link')
        )
        
        # Parse graphics sub-element
        graphics_elem = elem.find('graphics')
        if graphics_elem is not None:
            entry.graphics = self._parse_graphics(graphics_elem)
        
        # Parse components for groups
        if entry.type == 'group':
            for component_elem in elem.findall('component'):
                component_id = component_elem.attrib.get('id', '')
                if component_id:
                    entry.components.append(component_id)
        
        return entry
    
    def _parse_graphics(self, elem: ET.Element) -> KEGGGraphics:
        """Parse graphics element.
        
        Args:
            elem: <graphics> XML element
            
        Returns:
            KEGGGraphics object
        """
        return KEGGGraphics(
            name=elem.attrib.get('name', ''),
            x=float(elem.attrib.get('x', 0)),
            y=float(elem.attrib.get('y', 0)),
            width=float(elem.attrib.get('width', 46)),
            height=float(elem.attrib.get('height', 17)),
            fgcolor=elem.attrib.get('fgcolor', '#000000'),
            bgcolor=elem.attrib.get('bgcolor', '#FFFFFF'),
            type=elem.attrib.get('type', 'rectangle')
        )
    
    def _parse_reaction(self, elem: ET.Element) -> KEGGReaction:
        """Parse reaction element.
        
        Args:
            elem: <reaction> XML element
            
        Returns:
            KEGGReaction object
        """
        reaction = KEGGReaction(
            id=elem.attrib.get('id', ''),
            name=elem.attrib.get('name', ''),
            type=elem.attrib.get('type', 'irreversible')
        )
        
        # Parse substrates
        for substrate_elem in elem.findall('substrate'):
            substrate = KEGGSubstrate(
                id=substrate_elem.attrib.get('id', ''),
                name=substrate_elem.attrib.get('name', '')
            )
            reaction.substrates.append(substrate)
        
        # Parse products
        for product_elem in elem.findall('product'):
            product = KEGGProduct(
                id=product_elem.attrib.get('id', ''),
                name=product_elem.attrib.get('name', '')
            )
            reaction.products.append(product)
        
        return reaction
    
    def _parse_relation(self, elem: ET.Element) -> KEGGRelation:
        """Parse relation element.
        
        Args:
            elem: <relation> XML element
            
        Returns:
            KEGGRelation object
        """
        relation = KEGGRelation(
            entry1=elem.attrib.get('entry1', ''),
            entry2=elem.attrib.get('entry2', ''),
            type=elem.attrib.get('type', '')
        )
        
        # Parse subtypes
        for subtype_elem in elem.findall('subtype'):
            subtype = KEGGRelationSubtype(
                name=subtype_elem.attrib.get('name', ''),
                value=subtype_elem.attrib.get('value', '')
            )
            relation.subtypes.append(subtype)
        
        return relation


# Convenience function
def parse_kgml(kgml_xml: str) -> Optional[KEGGPathway]:
    """Quick function to parse KGML XML.
    
    Args:
        kgml_xml: KGML XML string
        
    Returns:
        KEGGPathway object or None
        
    Example:
        >>> from shypn.importer.kegg.kgml_parser import parse_kgml
        >>> pathway = parse_kgml(kgml_xml_string)
    """
    parser = KGMLParser()
    return parser.parse(kgml_xml)
