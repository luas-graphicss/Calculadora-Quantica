from quantum_calculator.domain.diagnostics import Diagnostic, DiagnosticCode, quote_user_text
from quantum_calculator.domain.dimensions import ENERGY, LENGTH, MASS, TIME, Dimension
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.units import Unit

_DIMENSION_LABELS = {MASS: "massa", LENGTH: "comprimento", TIME: "tempo", ENERGY: "energia"}


def describe_dimension(dimension: Dimension) -> str:
    return _DIMENSION_LABELS.get(dimension, dimension.base_si_unit())


class UnitResolver:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units

    def resolve(
        self,
        symbol: str,
        dimension: Dimension,
        subject: str,
        pointer: str,
        diagnostics: list[Diagnostic],
    ) -> Unit | None:
        unit = self._units.find(symbol)
        if unit is None:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.UNKNOWN_UNIT,
                    pointer,
                    f"A unidade {quote_user_text(symbol)} não consta do registro de unidades.",
                    self._expectation(dimension),
                )
            )
            return None
        if unit.dimension != dimension:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.DIMENSION_MISMATCH,
                    pointer,
                    f"A unidade {quote_user_text(symbol)} mede "
                    f"{describe_dimension(unit.dimension)}, mas {subject} exige "
                    f"{describe_dimension(dimension)}.",
                    self._expectation(dimension),
                )
            )
            return None
        return unit

    def _expectation(self, dimension: Dimension) -> str:
        symbols = ", ".join(self._units.symbols_for(dimension))
        return f"unidade de {describe_dimension(dimension)}: {symbols}"
