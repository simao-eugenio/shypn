"""Data-validation and expression exceptions."""

from shypn.exceptions.base import ShypnError


class DataValidationError(ShypnError):
    """Errors in data validation or parsing.

    Raised when input data fails validation checks.
    """
    pass


class ExpressionError(DataValidationError):
    """Invalid mathematical expression.

    Raised when:
    - Rate function syntax is invalid
    - Guard expression cannot be parsed
    - Assignment rule is malformed
    """
    pass


class ParameterError(DataValidationError):
    """Invalid parameter value or configuration.

    Raised when:
    - Parameter value is out of valid range
    - Required parameter is missing
    - Parameter type is incorrect
    """
    pass
