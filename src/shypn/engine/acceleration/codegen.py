"""Python rate-expression → C expression transpiler.

Converts rate function strings as written in SHYPN model files
(Python arithmetic + function-catalog calls) to C89-compatible
expressions suitable for embedding in a generated ODE RHS function.

Mapping rules
-------------
* ``a ** b``             → ``pow(a, b)``
* ``min(a, b)``          → ``fmin(a, b)``
* ``max(a, b)``          → ``fmax(a, b)``
* ``abs(x)``             → ``fabs(x)``
* ``exp / log / sqrt``   → unchanged (available in ``<math.h>``)
* ``math.exp(x)``        → ``exp(x)``  (attribute access on ``math``)
* Place names            → ``y[i]``  (via ``name_to_index`` mapping)
* ``Temperature``, ``T``, ``pH``, ``R``, ``F``, ``I``
                         → local C variables (declared by caller)
* Function-catalog calls → inline C helper calls (``_sat``, ``_hill``, …)

Unsupported nodes raise ``TranspileError`` so callers can fall back to
the Python eval path gracefully.
"""

import ast
import re
import textwrap
from typing import Dict, Optional, Set


class TranspileError(ValueError):
    """Raised when a rate expression cannot be transpiled to C."""


# ------------------------------------------------------------------
# Scalar constant that maps catalog function names → C helper names
# Helpers are emitted once in the generated C header.
# ------------------------------------------------------------------
CATALOG_TO_C: Dict[str, str] = {
    # Saturation / binding
    "michaelis_menten": "_sat",
    "hill_equation": "_hill",
    "competitive_inhibition": "_comp_inhib",
    "mass_action": "_mass_action",
    # Activation shapes
    "sigmoid": "_sigmoid",
    "tanh_activation": "_tanh_act",
    "relu": "_relu",
    "leaky_relu": "_leaky_relu",
    "softplus": "_softplus",
    # Growth kinetics
    "exponential_growth": "_exp_growth",
    "exponential_decay": "_exp_decay",
    "logistic_growth": "_logistic",
    "gompertz_growth": "_gompertz",
    # Statistics / distributions
    "normal_pdf": "_normal_pdf",
    "exponential_pdf": "_exp_pdf",
    "gamma_pdf": "_gamma_pdf",
    "step": "_step_fn",
    "uniform": "_uniform_fn",
    # Aliases sometimes used
    "hill": "_hill",
    "mm": "_sat",
}

# Built-in Python math functions that map directly to C equivalents.
BUILTIN_TO_C: Dict[str, str] = {
    "exp": "exp",
    "log": "log",
    "log10": "log10",
    "log2": "log2",
    "sqrt": "sqrt",
    "abs": "fabs",
    "fabs": "fabs",
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
    "atan2": "atan2",
    "pow": "pow",
    "floor": "floor",
    "ceil": "ceil",
    "fmin": "fmin",
    "fmax": "fmax",
    "min": "fmin",
    "max": "fmax",
    "hypot": "hypot",
    "tanh": "tanh",
    "sinh": "sinh",
    "cosh": "cosh",
    "erf": "erf",
    "erfc": "erfc",
    "tgamma": "tgamma",
    "lgamma": "lgamma",
}

# Thermodynamic scalar names that are declared as local C variables in the
# generated RHS function (read from the params[] array).
THERMO_LOCALS: Set[str] = {
    "T", "Temperature", "T_celsius",
    "pH", "ph",
    "I", "ionic_strength",
    "R", "R_SI", "F",
}

# Physical constants that can be inlined as literals (no place/param needed).
CONSTANT_VALUES: Dict[str, str] = {
    "R":    "0.008314",   # kJ/(mol·K)
    "R_SI": "8.314",      # J/(mol·K)
    "F":    "96485.0",    # C/mol
}


# ===========================================================================
# C helper function implementations (pasted verbatim into generated header)
# ===========================================================================
C_HELPERS: str = textwrap.dedent(r"""
/* ---- SHYPN inline function-catalog helpers ---- */

static inline double _sat(double s, double vmax, double km) {
    return (km <= 0.0) ? vmax : (vmax * s) / (km + s + 1e-300);
}

static inline double _hill(double s, double vmax, double kd, double n) {
    double kdn = pow(kd, n);
    double sn  = pow(s, n);
    return vmax * sn / (kdn + sn + 1e-300);
}

static inline double _comp_inhib(double s, double inh, double vmax,
                                  double km, double ki) {
    return vmax * s / ((km * (1.0 + inh / ki)) + s + 1e-300);
}

static inline double _mass_action(double r1, double r2, double k) {
    return k * r1 * r2;
}

static inline double _sigmoid(double x, double center, double steepness) {
    return 1.0 / (1.0 + exp(-steepness * (x - center)));
}

static inline double _tanh_act(double x, double center, double steepness) {
    return 0.5 * (1.0 + tanh(steepness * (x - center)));
}

static inline double _relu(double x, double thr) {
    return (x > thr) ? (x - thr) : 0.0;
}

static inline double _leaky_relu(double x, double thr, double alpha) {
    return (x >= thr) ? (x - thr) : alpha * (x - thr);
}

static inline double _softplus(double x, double beta) {
    double bx = beta * x;
    return (bx > 50.0) ? x : log(1.0 + exp(bx)) / beta;
}

static inline double _exp_growth(double x, double rate) {
    return x * exp(rate);
}

static inline double _exp_decay(double x, double half_life) {
    return x * exp(-0.693147180559945309 / half_life);
}

static inline double _logistic(double x, double K, double r) {
    return x * r * (1.0 - x / K);
}

static inline double _gompertz(double x, double K, double r) {
    return x * r * log((K + 1e-300) / (x + 1e-300));
}

static inline double _normal_pdf(double x, double mu, double sigma) {
    double z = (x - mu) / (sigma + 1e-300);
    return exp(-0.5 * z * z) / (sigma * 2.5066282746310002);
}

static inline double _exp_pdf(double x, double rate) {
    return (x >= 0.0) ? rate * exp(-rate * x) : 0.0;
}

static inline double _gamma_pdf(double x, double shape, double scale) {
    if (x <= 0.0) return 0.0;
    double lx = log(x);
    double ll = (shape - 1.0) * lx - x / scale - lgamma(shape)
                - shape * log(scale);
    return exp(ll);
}

static inline double _step_fn(double x, double thr, double lo, double hi) {
    return (x >= thr) ? hi : lo;
}

static inline double _uniform_fn(double x, double lo, double hi) {
    return (x < lo || x > hi) ? 0.0 : 1.0 / (hi - lo + 1e-300);
}
""")


# ===========================================================================
# AST-based transpiler
# ===========================================================================

class _CExprEmitter(ast.NodeVisitor):
    """Walk Python AST and emit C expression string.

    Parameters
    ----------
    name_to_index:
        Maps place *name* (as it appears in rate expressions, e.g.
        ``"GATA1_Protein_nuc"``) to its index in the ODE state vector ``y``.
    thermo_locals:
        Set of thermodynamic variable names declared as local C vars by the
        RHS function (T, pH, etc.).  These are emitted verbatim.
    extra_params:
        Maps extra (non-state) place names to their index in the ``extras``
        array (constants during integration).
    """

    def __init__(
        self,
        name_to_index: Dict[str, int],
        thermo_locals: Set[str],
        extra_params: Dict[str, int],
    ) -> None:
        self._n2i = name_to_index
        self._thermo = thermo_locals
        self._extras = extra_params

    # ---- helpers -----

    def _require(self, node: ast.AST) -> str:
        result = self.visit(node)
        if result is None:
            raise TranspileError(f"Cannot transpile AST node: {ast.dump(node)}")
        return result

    # ---- visitor methods -----

    def visit_Expression(self, node: ast.Expression) -> str:  # type: ignore[override]
        return self._require(node.body)

    def visit_Constant(self, node: ast.Constant) -> str:  # type: ignore[override]
        v = node.value
        if isinstance(v, (int, float)):
            # Emit as C double literal
            s = repr(float(v))
            # Make sure there is a decimal point so C treats it as double
            if "." not in s and "e" not in s.lower():
                s += ".0"
            return s
        raise TranspileError(f"Non-numeric constant: {v!r}")

    # Legacy Python <3.8
    def visit_Num(self, node: ast.Num) -> str:  # type: ignore[override]
        return self.visit_Constant(ast.Constant(value=node.n))  # type: ignore[arg-type]

    def visit_Name(self, node: ast.Name) -> str:  # type: ignore[override]
        name = node.id
        # 1. State-vector place
        if name in self._n2i:
            return f"y[{self._n2i[name]}]"
        # 2. Extra (non-ODE) place
        if name in self._extras:
            return f"extras[{self._extras[name]}]"
        # 3. Thermodynamic local variable
        if name in self._thermo:
            return name
        # 4. Inlined physical constant
        if name in CONSTANT_VALUES:
            return CONSTANT_VALUES[name]
        # 5. pi / e
        if name == "pi":
            return "3.14159265358979323846"
        if name == "e":
            return "2.71828182845904523536"
        # Unknown — warn and emit as-is (may produce a C warning/error)
        return name

    def visit_UnaryOp(self, node: ast.UnaryOp) -> str:  # type: ignore[override]
        operand = self._require(node.operand)
        if isinstance(node.op, ast.USub):
            # Wrap in parens to handle -x**2 correctly
            return f"(-{operand})"
        if isinstance(node.op, ast.UAdd):
            return operand
        raise TranspileError(f"Unsupported unary op: {type(node.op).__name__}")

    def visit_BinOp(self, node: ast.BinOp) -> str:  # type: ignore[override]
        left = self._require(node.left)
        right = self._require(node.right)
        op = node.op
        if isinstance(op, ast.Pow):
            return f"pow({left}, {right})"
        sym = {
            ast.Add: "+",
            ast.Sub: "-",
            ast.Mult: "*",
            ast.Div: "/",
            ast.Mod: "%",
        }.get(type(op))
        if sym is None:
            raise TranspileError(f"Unsupported binary op: {type(op).__name__}")
        return f"({left} {sym} {right})"

    def visit_BoolOp(self, node: ast.BoolOp) -> str:  # type: ignore[override]
        # Python `and` / `or` → C `&&` / `||`
        # In C, these yield 0 or 1 (int), which is fine for arithmetic use
        # in rate expressions like: rate * (A > 0 and B > 0)
        parts = [self._require(v) for v in node.values]
        if isinstance(node.op, ast.And):
            return "(" + " && ".join(parts) + ")"
        if isinstance(node.op, ast.Or):
            return "(" + " || ".join(parts) + ")"
        raise TranspileError(f"Unsupported boolean op: {type(node.op).__name__}")

    def visit_Compare(self, node: ast.Compare) -> str:  # type: ignore[override]
        # Python comparisons → C comparisons.
        # Supports chained comparisons: a < b < c → ((a < b) && (b < c))
        # In C, comparison operators yield 0 or 1, which is valid for
        # arithmetic use in rate expressions like: rate * (X > threshold)
        _OP_MAP = {
            ast.Lt: "<", ast.LtE: "<=",
            ast.Gt: ">", ast.GtE: ">=",
            ast.Eq: "==", ast.NotEq: "!=",
        }
        left = self._require(node.left)
        parts = []
        prev = left
        for op, comparator in zip(node.ops, node.comparators):
            sym = _OP_MAP.get(type(op))
            if sym is None:
                raise TranspileError(
                    f"Unsupported comparison op: {type(op).__name__}"
                )
            right = self._require(comparator)
            parts.append(f"({prev} {sym} {right})")
            prev = right
        if len(parts) == 1:
            return parts[0]
        return "(" + " && ".join(parts) + ")"

    def visit_IfExp(self, node: ast.IfExp) -> str:  # type: ignore[override]
        # Python ternary: a if cond else b  →  C: (cond ? a : b)
        test = self._require(node.test)
        body = self._require(node.body)
        orelse = self._require(node.orelse)
        return f"({test} ? {body} : {orelse})"

    def visit_Call(self, node: ast.Call) -> str:  # type: ignore[override]
        args = [self._require(a) for a in node.args]

        # Attribute call: math.exp(x), np.exp(x), etc.
        if isinstance(node.func, ast.Attribute):
            fn_name = node.func.attr
            c_fn = BUILTIN_TO_C.get(fn_name)
            if c_fn:
                return f"{c_fn}({', '.join(args)})"
            raise TranspileError(
                f"Unsupported attribute function call: "
                f"{ast.unparse(node.func)} — "
                f"attribute functions other than math.*"
                f"/np.* builtins are not supported"
            )

        # Simple name call
        if not isinstance(node.func, ast.Name):
            raise TranspileError(
                f"Unsupported callable: {ast.dump(node.func)}"
            )

        fn_name = node.func.id

        # Builtin math
        c_fn = BUILTIN_TO_C.get(fn_name)
        if c_fn:
            return f"{c_fn}({', '.join(args)})"

        # Function catalog
        c_helper = CATALOG_TO_C.get(fn_name)
        if c_helper:
            return f"{c_helper}({', '.join(args)})"

        raise TranspileError(
            f"Unknown function '{fn_name}' — "
            f"not in builtins or function catalog"
        )

    def visit_Subscript(self, node: ast.Subscript) -> str:  # type: ignore[override]
        raise TranspileError("Subscript expressions are not supported in C codegen")

    def generic_visit(self, node: ast.AST) -> str:  # type: ignore[override]
        raise TranspileError(
            f"Unsupported AST node type: {type(node).__name__} — {ast.dump(node)}"
        )


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

_BRACKET_RE = re.compile(r"\[([^\]]+)\]")


def preprocess_expr(expr: str) -> str:
    """Strip chemistry ``[X]`` notation and normalise whitespace."""
    expr = _BRACKET_RE.sub(r"\1", expr)
    return expr.strip()


def transpile_expression(
    expr: str,
    name_to_index: Dict[str, int],
    extra_params: Optional[Dict[str, int]] = None,
    thermo_locals: Optional[Set[str]] = None,
) -> str:
    """Transpile a Python rate expression to a C expression string.

    Parameters
    ----------
    expr:
        Python arithmetic expression as written in the model.
    name_to_index:
        Map of place name → state-vector index.
    extra_params:
        Map of extra place name → extras-array index.
    thermo_locals:
        Thermodynamic variable names that are local C vars.

    Returns
    -------
    str
        C expression (may contain ``pow()``, ``y[i]``, …).

    Raises
    ------
    TranspileError
        If any part of the expression cannot be represented in C.
    """
    if thermo_locals is None:
        thermo_locals = THERMO_LOCALS
    if extra_params is None:
        extra_params = {}

    cleaned = preprocess_expr(expr)

    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError as exc:
        raise TranspileError(f"Syntax error in expression: {expr!r}") from exc

    emitter = _CExprEmitter(name_to_index, thermo_locals, extra_params)
    return emitter.visit(tree)


def collect_names(expr: str) -> Set[str]:
    """Return all Name nodes referenced in *expr* (best-effort)."""
    cleaned = preprocess_expr(expr)
    try:
        tree = ast.parse(cleaned, mode="eval")
    except SyntaxError:
        return set()
    names: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
    return names
