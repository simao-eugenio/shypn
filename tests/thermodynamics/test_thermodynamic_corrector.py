"""Tests for thermodynamic corrections.

This module tests the ThermodynamicCorrector class for pH, temperature,
and ionic strength corrections to Gibbs free energy.
"""

import pytest
import math

from shypn.thermodynamics import ThermodynamicCorrector


class TestThermodynamicCorrectorInit:
    """Test corrector initialization and constants."""
    
    def test_constants(self):
        """Test that corrector has correct physical constants."""
        corrector = ThermodynamicCorrector()
        
        # Gas constant (kJ/(mol·K))
        assert abs(corrector.R - 0.008314) < 1e-6
        
        # Standard conditions
        assert corrector.STANDARD_PH == 7.0
        assert corrector.STANDARD_TEMPERATURE == 298.15
        assert corrector.STANDARD_IONIC_STRENGTH == 0.1
        
        # Debye-Hückel parameters
        assert abs(corrector.DEBYE_HUCKEL_A - 0.509) < 0.01
        assert abs(corrector.DEBYE_HUCKEL_B - 0.33) < 0.01


class TestPHCorrection:
    """Test pH corrections."""
    
    def test_no_correction_same_ph(self):
        """Test that no correction occurs at same pH."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5  # kJ/mol
        corrected = corrector.correct_ph(
            delta_g,
            n_protons=-1,
            ph_actual=7.0,
            ph_standard=7.0
        )
        
        assert corrected == delta_g
    
    def test_no_correction_no_protons(self):
        """Test that no correction occurs when n_protons=0."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5  # kJ/mol
        corrected = corrector.correct_ph(
            delta_g,
            n_protons=0,
            ph_actual=6.0,
            ph_standard=7.0
        )
        
        assert corrected == delta_g
    
    def test_proton_producing_reaction_acidic(self):
        """Test pH correction for proton-producing reaction at lower pH.
        
        Example: ATP hydrolysis produces H+
        At lower pH (more H+), equilibrium shifts left, less favorable.
        """
        corrector = ThermodynamicCorrector()
        
        delta_g_ph7 = -30.5  # kJ/mol at pH 7
        n_protons = -1  # Produces 1 proton
        
        # At pH 6 (10x more H+)
        delta_g_ph6 = corrector.correct_ph(
            delta_g_ph7,
            n_protons=n_protons,
            ph_actual=6.0,
            ph_standard=7.0,
            temperature=298.15
        )
        
        # Should be LESS favorable (less negative)
        # ΔG = -30.5 + (-1) * 5.708 * (-1) = -30.5 + 5.708 ≈ -24.8
        assert delta_g_ph6 > delta_g_ph7
        assert abs(delta_g_ph6 - (-30.5 + 5.708)) < 0.1
    
    def test_proton_producing_reaction_basic(self):
        """Test pH correction for proton-producing reaction at higher pH.
        
        At higher pH (less H+), equilibrium shifts right, more favorable.
        """
        corrector = ThermodynamicCorrector()
        
        delta_g_ph7 = -30.5  # kJ/mol at pH 7
        n_protons = -1  # Produces 1 proton
        
        # At pH 8 (10x less H+)
        delta_g_ph8 = corrector.correct_ph(
            delta_g_ph7,
            n_protons=n_protons,
            ph_actual=8.0,
            ph_standard=7.0,
            temperature=298.15
        )
        
        # Should be MORE favorable (more negative)
        # ΔG = -30.5 + (-1) * 5.708 * 1 = -30.5 - 5.708 ≈ -36.2
        assert delta_g_ph8 < delta_g_ph7
        assert abs(delta_g_ph8 - (-30.5 - 5.708)) < 0.1
    
    def test_proton_consuming_reaction(self):
        """Test pH correction for proton-consuming reaction.
        
        Example: Reaction that consumes H+
        At lower pH (more H+), more favorable.
        """
        corrector = ThermodynamicCorrector()
        
        delta_g_ph7 = -20.0  # kJ/mol at pH 7
        n_protons = 1  # Consumes 1 proton
        
        # At pH 6 (more H+ available)
        delta_g_ph6 = corrector.correct_ph(
            delta_g_ph7,
            n_protons=n_protons,
            ph_actual=6.0,
            ph_standard=7.0
        )
        
        # Should be MORE favorable (more negative)
        # ΔG = -20.0 + 1 * 5.708 * (-1) = -20.0 - 5.708 ≈ -25.7
        assert delta_g_ph6 < delta_g_ph7
        assert abs(delta_g_ph6 - (-20.0 - 5.708)) < 0.1
    
    def test_multiple_protons(self):
        """Test correction with multiple proton transfer."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -50.0
        n_protons = -2  # Produces 2 protons
        
        corrected = corrector.correct_ph(
            delta_g,
            n_protons=n_protons,
            ph_actual=6.0,
            ph_standard=7.0
        )
        
        # Correction should be 2x larger
        # ΔG = -50.0 + (-2) * 5.708 * (-1) = -50.0 + 11.416 ≈ -38.6
        expected = delta_g + (-n_protons) * 5.708
        assert abs(corrected - expected) < 0.2
    
    def test_temperature_dependence(self):
        """Test that pH correction depends on temperature."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.0
        n_protons = -1
        
        # At 298.15 K (25°C)
        dg_25c = corrector.correct_ph(
            delta_g, n_protons, ph_actual=6.0, ph_standard=7.0, temperature=298.15
        )
        
        # At 310.15 K (37°C, body temperature)
        dg_37c = corrector.correct_ph(
            delta_g, n_protons, ph_actual=6.0, ph_standard=7.0, temperature=310.15
        )
        
        # Higher temperature → larger RT → larger correction
        assert abs(dg_37c - delta_g) > abs(dg_25c - delta_g)


class TestTemperatureCorrection:
    """Test temperature corrections using van 't Hoff equation."""
    
    def test_no_correction_same_temperature(self):
        """Test no correction at same temperature."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        delta_h = -45.0
        
        corrected = corrector.correct_temperature(
            delta_g, delta_h, temperature_actual=298.15, temperature_standard=298.15
        )
        
        assert corrected == delta_g
    
    def test_no_correction_missing_enthalpy(self):
        """Test that correction returns original value when ΔH° is None."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        corrected = corrector.correct_temperature(
            delta_g, delta_h_standard=None, temperature_actual=310.15
        )
        
        assert corrected == delta_g
    
    def test_exothermic_reaction_higher_temp(self):
        """Test exothermic reaction becomes less favorable at higher T.
        
        For exothermic reactions (ΔH° < 0):
        - Higher T → less favorable (ΔG becomes less negative)
        - Lower T → more favorable (ΔG becomes more negative)
        """
        corrector = ThermodynamicCorrector()
        
        delta_g_25c = -30.5  # kJ/mol at 25°C
        delta_h = -45.0  # Exothermic
        
        # At 37°C (310.15 K)
        delta_g_37c = corrector.correct_temperature(
            delta_g_25c, delta_h, temperature_actual=310.15
        )
        
        # Should be less favorable (less negative)
        assert delta_g_37c > delta_g_25c
    
    def test_endothermic_reaction_higher_temp(self):
        """Test endothermic reaction becomes more favorable at higher T.
        
        For endothermic reactions (ΔH° > 0):
        - Higher T → more favorable (ΔG becomes more negative)
        - Lower T → less favorable (ΔG becomes less negative)
        """
        corrector = ThermodynamicCorrector()
        
        delta_g_25c = -10.0  # kJ/mol at 25°C
        delta_h = +30.0  # Endothermic
        
        # At 37°C (310.15 K)
        delta_g_37c = corrector.correct_temperature(
            delta_g_25c, delta_h, temperature_actual=310.15
        )
        
        # Should be more favorable (more negative)
        assert delta_g_37c < delta_g_25c
    
    def test_thermodynamic_consistency(self):
        """Test that ΔG = ΔH - TΔS is satisfied."""
        corrector = ThermodynamicCorrector()
        
        delta_g_std = -30.5  # kJ/mol at 298.15 K
        delta_h_std = -45.0  # kJ/mol
        T_std = 298.15
        
        # Calculate ΔS from standard conditions
        delta_s = (delta_h_std - delta_g_std) / T_std
        
        # Test at different temperature
        T_new = 310.15
        delta_g_new = corrector.correct_temperature(
            delta_g_std, delta_h_std, T_new, T_std
        )
        
        # Verify ΔG = ΔH - TΔS
        expected_dg = delta_h_std - T_new * delta_s
        assert abs(delta_g_new - expected_dg) < 0.01


class TestTemperatureCorrectionKEq:
    """Test K_eq temperature corrections."""
    
    def test_keq_no_correction_same_temp(self):
        """Test no K_eq correction at same temperature."""
        corrector = ThermodynamicCorrector()
        
        k_eq = 1000.0
        delta_h = -45.0
        
        corrected = corrector.correct_temperature_k_eq(
            k_eq, delta_h, temperature_actual=298.15
        )
        
        assert corrected == k_eq
    
    def test_keq_exothermic_higher_temp(self):
        """Test that K_eq decreases for exothermic reaction at higher T."""
        corrector = ThermodynamicCorrector()
        
        k_eq_25c = 1000.0
        delta_h = -45.0  # Exothermic
        
        # At 37°C
        k_eq_37c = corrector.correct_temperature_k_eq(
            k_eq_25c, delta_h, temperature_actual=310.15
        )
        
        # K_eq should decrease (less favorable)
        assert k_eq_37c < k_eq_25c
    
    def test_keq_endothermic_higher_temp(self):
        """Test that K_eq increases for endothermic reaction at higher T."""
        corrector = ThermodynamicCorrector()
        
        k_eq_25c = 100.0
        delta_h = +30.0  # Endothermic
        
        # At 37°C
        k_eq_37c = corrector.correct_temperature_k_eq(
            k_eq_25c, delta_h, temperature_actual=310.15
        )
        
        # K_eq should increase (more favorable)
        assert k_eq_37c > k_eq_25c
    
    def test_keq_consistency_with_delta_g(self):
        """Test that K_eq and ΔG corrections are consistent."""
        corrector = ThermodynamicCorrector()
        
        # Standard conditions
        delta_g_std = -17.1  # kJ/mol (K_eq ≈ 1000)
        delta_h_std = -45.0
        T_std = 298.15
        T_new = 310.15
        
        # K_eq from ΔG: K = exp(-ΔG/RT)
        R = corrector.R
        k_eq_std = math.exp(-delta_g_std / (R * T_std))
        
        # Correct both
        delta_g_new = corrector.correct_temperature(
            delta_g_std, delta_h_std, T_new, T_std
        )
        k_eq_new = corrector.correct_temperature_k_eq(
            k_eq_std, delta_h_std, T_new, T_std
        )
        
        # Calculate K_eq from corrected ΔG
        k_eq_from_dg = math.exp(-delta_g_new / (R * T_new))
        
        # Should match (within numerical precision)
        relative_error = abs(k_eq_new - k_eq_from_dg) / k_eq_from_dg
        assert relative_error < 0.01


class TestIonicStrengthCorrection:
    """Test ionic strength corrections using Debye-Hückel theory."""
    
    def test_no_correction_same_ionic_strength(self):
        """Test no correction at same ionic strength."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        corrected = corrector.correct_ionic_strength(
            delta_g,
            charge_reactants=4,
            charge_products=4,
            ionic_strength_actual=0.1
        )
        
        assert corrected == delta_g
    
    def test_no_correction_no_charge_change(self):
        """Test minimal correction when charge doesn't change."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        corrected = corrector.correct_ionic_strength(
            delta_g,
            charge_reactants=4,  # Same squared charges
            charge_products=4,
            ionic_strength_actual=0.15,
            ionic_strength_standard=0.1
        )
        
        # Should be very close to original
        assert abs(corrected - delta_g) < 0.5
    
    def test_charged_reaction_higher_ionic_strength(self):
        """Test that higher ionic strength affects charged reactions."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        # Reaction with charge change (e.g., ATP^4- + H2O → ADP^3- + Pi^2-)
        corrected = corrector.correct_ionic_strength(
            delta_g,
            charge_reactants=16,  # 4^2
            charge_products=13,   # 3^2 + 2^2
            ionic_strength_actual=0.15,
            ionic_strength_standard=0.1
        )
        
        # There should be some correction
        assert corrected != delta_g
    
    def test_activity_coefficient_zero_ionic_strength(self):
        """Test activity coefficient is zero at zero ionic strength."""
        corrector = ThermodynamicCorrector()
        
        log_gamma = corrector._activity_coefficient(
            delta_charge_squared=4,
            ionic_strength=0.0
        )
        
        assert log_gamma == 0.0
    
    def test_activity_coefficient_increases_with_ionic_strength(self):
        """Test that activity coefficient magnitude increases with I."""
        corrector = ThermodynamicCorrector()
        
        delta_z2 = 4
        
        log_gamma_01 = corrector._activity_coefficient(delta_z2, 0.1)
        log_gamma_02 = corrector._activity_coefficient(delta_z2, 0.2)
        
        # Higher ionic strength → more screening → larger effect
        assert abs(log_gamma_02) > abs(log_gamma_01)


class TestApplyAllCorrections:
    """Test combined corrections."""
    
    def test_all_corrections_applied(self):
        """Test that all corrections can be applied together."""
        corrector = ThermodynamicCorrector()
        
        delta_g_std = -30.5  # kJ/mol at pH 7, 298.15 K, 0.1 M
        
        corrected = corrector.apply_all_corrections(
            delta_g_std,
            n_protons=-1,
            delta_h_standard=-45.0,
            charge_reactants=16,
            charge_products=13,
            ph_actual=6.5,
            temperature_actual=310.15,
            ionic_strength_actual=0.15
        )
        
        # Should be different from original
        assert corrected != delta_g_std
    
    def test_no_corrections_at_standard_conditions(self):
        """Test that standard conditions give no correction."""
        corrector = ThermodynamicCorrector()
        
        delta_g_std = -30.5
        
        corrected = corrector.apply_all_corrections(
            delta_g_std,
            n_protons=0,
            delta_h_standard=-45.0,
            charge_reactants=0,
            charge_products=0,
            ph_actual=7.0,
            temperature_actual=298.15,
            ionic_strength_actual=0.1
        )
        
        assert corrected == delta_g_std
    
    def test_physiological_conditions(self):
        """Test correction for physiological conditions (pH 7.4, 37°C, 0.15 M).
        
        This is a realistic example of ATP hydrolysis under
        physiological conditions.
        """
        corrector = ThermodynamicCorrector()
        
        # ATP hydrolysis standard conditions (pH 7, 25°C, 0.1 M)
        delta_g_std = -30.5  # kJ/mol
        delta_h = -20.0  # kJ/mol (exothermic)
        n_protons = -1  # Produces H+
        
        # Physiological conditions
        corrected = corrector.apply_all_corrections(
            delta_g_std,
            n_protons=n_protons,
            delta_h_standard=delta_h,
            charge_reactants=16,  # ATP^4-
            charge_products=13,   # ADP^3- + Pi^2-
            ph_actual=7.4,
            temperature_actual=310.15,  # 37°C
            ionic_strength_actual=0.15
        )
        
        # Should be somewhat different
        # pH 7.4 → slightly more favorable (produces H+ at higher pH)
        # 37°C → slightly less favorable (exothermic)
        # Higher ionic strength → small effect
        assert corrected != delta_g_std


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_large_ph_change(self):
        """Test correction with large pH change."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        # From pH 7 to pH 4 (1000x H+ increase)
        corrected = corrector.correct_ph(
            delta_g,
            n_protons=-1,
            ph_actual=4.0,
            ph_standard=7.0
        )
        
        # Should have large correction: 3 pH units × 5.7 ≈ 17 kJ/mol
        assert abs(corrected - delta_g) > 15
    
    def test_extreme_temperature(self):
        """Test correction at extreme temperature."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        delta_h = -45.0
        
        # At 350 K (77°C)
        corrected = corrector.correct_temperature(
            delta_g, delta_h, temperature_actual=350.0
        )
        
        # Should be different (change is ~52K, exothermic so less favorable)
        assert abs(corrected - delta_g) > 2
        assert corrected > delta_g  # Less favorable at higher T for exothermic
    
    def test_high_ionic_strength(self):
        """Test correction at high ionic strength (near validity limit)."""
        corrector = ThermodynamicCorrector()
        
        delta_g = -30.5
        
        # At 0.5 M (upper limit of Debye-Hückel validity)
        corrected = corrector.correct_ionic_strength(
            delta_g,
            charge_reactants=16,
            charge_products=9,
            ionic_strength_actual=0.5,
            ionic_strength_standard=0.1
        )
        
        # Should have noticeable correction
        assert corrected != delta_g


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
