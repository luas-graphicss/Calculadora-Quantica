import re
import unicodedata

from quantum_calculator.domain.expressions import DerivativeKind, ElementaryFunction

ELEMENTARY_FUNCTIONS = {function.value: function for function in ElementaryFunction}
PI = "pi"
DIFFERENTIAL = "d"
PRIME = "'"
DERIVATIVE_OPERATORS = {"diff": DerivativeKind.ORDINARY, "partial": DerivativeKind.PARTIAL}
OPERATOR_BY_DERIVATIVE_KIND = {kind: name for name, kind in DERIVATIVE_OPERATORS.items()}
INTEGRAL_OPERATOR = "integral"
RESERVED_NAMES = frozenset(
    {*ELEMENTARY_FUNCTIONS, *DERIVATIVE_OPERATORS, PI, DIFFERENTIAL, INTEGRAL_OPERATOR}
)
NAME_EXPECTATION = "letras com dígitos ou um subscrito opcionais, como x, x1, y_0 ou omega_0"

_SMALL_LETTERS = (
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
)
_CAPITAL_LETTERS = ("Gamma", "Delta", "Theta", "Lambda", "Xi", "Sigma", "Phi", "Psi", "Omega")
_UNICODE_SPELLINGS = {"lambda": "lamda"}
_NAME = re.compile(r"(?P<base>[^\W\d_]+)(?P<digits>\d*)(?:_(?P<subscript>[^\W_]+))?")


def _greek_letter(case: str, name: str) -> str:
    spelling = _UNICODE_SPELLINGS.get(name.lower(), name.lower())
    return unicodedata.lookup(f"GREEK {case} LETTER {spelling.upper()}")


GREEK_LETTERS = {
    **{name: _greek_letter("SMALL", name) for name in _SMALL_LETTERS},
    **{name: _greek_letter("CAPITAL", name) for name in _CAPITAL_LETTERS},
}
GREEK_NAMES = {letter: name for name, letter in GREEK_LETTERS.items()}
_SPELLINGS = {**GREEK_LETTERS, unicodedata.lookup("GREEK SMALL LETTER PI"): PI}


def canonical_symbol_name(raw: str) -> str | None:
    match = _NAME.fullmatch(unicodedata.normalize("NFC", raw))
    if match is None:
        return None
    base = _SPELLINGS.get(match["base"], match["base"])
    subscript = "" if match["subscript"] is None else f"_{match['subscript']}"
    return f"{base}{match['digits']}{subscript}"


def symbol_parts(name: str) -> tuple[str, str, str | None]:
    match = _NAME.fullmatch(name)
    if match is None:
        raise ValueError(f"{name!r} is not a canonical symbol name")
    return match["base"], match["digits"], match["subscript"]
