"""Thermodynamic calculation exceptions."""

from shypn.exceptions.base import ShypnError


class ThermodynamicsError(ShypnError):
    """Errors in thermodynamic calculations.

    Raised when thermodynamic analysis or validation fails.
    """
    pass


class CompoundNotFoundError(ThermodynamicsError):
    """Compound not found in database.

    Raised when requested compound ID is not in the database.
    """
    pass


class ThermodynamicConstraintError(ThermodynamicsError):
    """Thermodynamic constraint violated.

    Raised when:
    - Gibbs free energy constraint violated
    - Entropy production is negative
    - Energy conservation violated
    """
    pass
