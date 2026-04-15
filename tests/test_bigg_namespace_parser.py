"""Unit tests for BiGG namespace parser."""

import unittest

from shypn.importer.bigg.bigg_namespace_parser import BiGGNamespaceParser


class TestBiGGNamespaceParser(unittest.TestCase):
    """Test cases for BiGGNamespaceParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = BiGGNamespaceParser()
    
    def test_parse_species_id_with_compartment(self):
        """Test parsing species ID with compartment."""
        test_cases = [
            ('M_atp_c', ('atp', 'c')),
            ('M_nadh_m', ('nadh', 'm')),
            ('M_glc_D_e', ('glc_D', 'e')),
            ('M_h2o_p', ('h2o', 'p')),
        ]
        
        for species_id, expected in test_cases:
            with self.subTest(species_id=species_id):
                result = self.parser.parse_species_id(species_id)
                self.assertEqual(result, expected)
    
    def test_parse_species_id_without_prefix(self):
        """Test parsing species ID without M_ prefix."""
        result = self.parser.parse_species_id('atp_c')
        self.assertEqual(result, ('atp', 'c'))
    
    def test_parse_species_id_no_compartment(self):
        """Test parsing species ID without compartment."""
        result = self.parser.parse_species_id('M_h2o')
        self.assertEqual(result, ('h2o', None))
    
    def test_parse_species_id_invalid_compartment(self):
        """Test parsing with invalid compartment code."""
        # 'xy' is not a valid single-letter compartment
        result = self.parser.parse_species_id('M_test_xy')
        # Should return the whole thing without compartment
        self.assertEqual(result[1], None)
    
    def test_parse_reaction_id_reversible(self):
        """Test parsing reversible reaction ID."""
        test_cases = [
            ('R_ATPS4r', ('ATPS4', True)),
            ('R_PGIr', ('PGI', True)),
        ]
        
        for reaction_id, expected in test_cases:
            with self.subTest(reaction_id=reaction_id):
                result = self.parser.parse_reaction_id(reaction_id)
                self.assertEqual(result, expected)
    
    def test_parse_reaction_id_irreversible(self):
        """Test parsing irreversible reaction ID."""
        test_cases = [
            ('R_PFK', ('PFK', False)),
            ('R_BIOMASS', ('BIOMASS', False)),
        ]
        
        for reaction_id, expected in test_cases:
            with self.subTest(reaction_id=reaction_id):
                result = self.parser.parse_reaction_id(reaction_id)
                self.assertEqual(result, expected)
    
    def test_parse_reaction_id_without_prefix(self):
        """Test parsing reaction ID without R_ prefix."""
        result = self.parser.parse_reaction_id('ATPS4r')
        self.assertEqual(result, ('ATPS4', True))
    
    def test_get_compartment_name(self):
        """Test compartment name lookup."""
        test_cases = [
            ('c', 'cytosol'),
            ('e', 'extracellular'),
            ('m', 'mitochondrion'),
            ('p', 'periplasm'),
            ('n', 'nucleus'),
        ]
        
        for code, expected in test_cases:
            with self.subTest(code=code):
                result = self.parser.get_compartment_name(code)
                self.assertEqual(result, expected)
    
    def test_get_compartment_name_invalid(self):
        """Test compartment name with invalid code."""
        # Should return the code itself
        result = self.parser.get_compartment_name('z')
        self.assertEqual(result, 'z')
    
    def test_format_metabolite_display_name(self):
        """Test metabolite display name formatting."""
        test_cases = [
            (('atp', 'c'), 'ATP [cytosol]'),
            (('nadh', 'm'), 'NADH [mitochondrion]'),
            (('glc_D', 'e'), 'GLC_D [extracellular]'),
            (('h2o', None), 'H2O'),
        ]
        
        for (metabolite, compartment), expected in test_cases:
            with self.subTest(metabolite=metabolite, compartment=compartment):
                result = self.parser.format_metabolite_display_name(metabolite, compartment)
                self.assertEqual(result, expected)
    
    def test_is_energy_metabolite_positive(self):
        """Test energy metabolite detection (positive cases)."""
        energy_metabolites = [
            'atp', 'adp', 'amp',
            'gtp', 'gdp', 'gmp',
            'nad', 'nadh', 'nadp', 'nadph',
            'fad', 'fadh2',
            'coa', 'accoa',
            'pi', 'ppi',
        ]
        
        for metabolite in energy_metabolites:
            with self.subTest(metabolite=metabolite):
                result = self.parser.is_energy_metabolite(metabolite)
                self.assertTrue(result, f"{metabolite} should be classified as energy")
    
    def test_is_energy_metabolite_negative(self):
        """Test energy metabolite detection (negative cases)."""
        non_energy_metabolites = [
            'glucose', 'glc', 'pyruvate', 'pyr',
            'lactate', 'lac', 'citrate', 'cit',
        ]
        
        for metabolite in non_energy_metabolites:
            with self.subTest(metabolite=metabolite):
                result = self.parser.is_energy_metabolite(metabolite)
                self.assertFalse(result, f"{metabolite} should not be classified as energy")
    
    def test_is_energy_metabolite_case_insensitive(self):
        """Test that energy metabolite detection is case-insensitive."""
        test_cases = ['ATP', 'Atp', 'atp', 'ATp']
        
        for metabolite in test_cases:
            with self.subTest(metabolite=metabolite):
                result = self.parser.is_energy_metabolite(metabolite)
                self.assertTrue(result)


if __name__ == '__main__':
    unittest.main()
