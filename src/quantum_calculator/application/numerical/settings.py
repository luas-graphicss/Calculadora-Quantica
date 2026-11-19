from fractions import Fraction

from quantum_calculator.application.numerical.request import ValidationRequest, pointer_to
from quantum_calculator.domain.diagnostics import DiagnosticCode, quote_user_text
from quantum_calculator.domain.numerical.problems import ResolutionSetting
from quantum_calculator.domain.numerical.spec import SettingInput

_SECTION = "numerics"


class SettingsReader:
    def __init__(self, request: ValidationRequest) -> None:
        self._request = request
        self._given = {setting.name: setting for setting in request.spec.numerics or ()}
        self._read: dict[str, ResolutionSetting] = {}

    @property
    def resolution(self) -> tuple[ResolutionSetting, ...]:
        return tuple(self._read.values())

    def count(self, name: str, label: str, minimum: int, maximum: int) -> int | None:
        expected = f"inteiro entre {minimum} e {maximum}"
        setting = self._require(name, label, expected)
        if setting is None:
            return None
        value = setting.number.value
        if value.denominator != 1 or value < minimum:
            self.refuse(
                name,
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                f"{label.capitalize()} deve ser um inteiro a partir de {minimum}; a entrada traz "
                f"{quote_user_text(setting.number.literal)}.",
                expected,
            )
            return None
        if value > maximum:
            self.refuse(
                name,
                DiagnosticCode.RESOURCE_LIMIT_EXCEEDED,
                f"{label.capitalize()} pede {quote_user_text(setting.number.literal)}, acima do "
                f"perfil homologado, que vai até {maximum}. Nada foi alocado.",
                expected,
            )
            return None
        return value.numerator

    def within(
        self, name: str, label: str, minimum: Fraction, maximum: Fraction
    ) -> Fraction | None:
        expected = f"número maior que {_shown(minimum)} e até {_shown(maximum)}"
        setting = self._require(name, label, expected)
        if setting is None:
            return None
        if not minimum < setting.number.value <= maximum:
            self.refuse(
                name,
                DiagnosticCode.NUMBER_OUT_OF_RANGE,
                f"{label.capitalize()} está fora da faixa homologada; a entrada traz "
                f"{quote_user_text(setting.number.literal)}.",
                expected,
            )
            return None
        return setting.number.value

    def real(self, name: str, label: str) -> Fraction | None:
        setting = self._require(name, label, "número finito")
        return None if setting is None else setting.number.value

    def refuse(self, name: str, code: DiagnosticCode, message: str, expected: str) -> None:
        self._request.refuse(code, pointer_to(_SECTION, name), message, expected)

    def reject_unknown(self) -> None:
        known = ", ".join(self._read)
        for name in self._given:
            if name not in self._read:
                self.refuse(
                    name,
                    DiagnosticCode.UNEXPECTED_FIELD,
                    f"A ficha não usa o ajuste numérico {quote_user_text(name)}.",
                    f"um destes ajustes: {known}",
                )

    def _require(self, name: str, label: str, expected: str) -> SettingInput | None:
        setting = self._given.get(name)
        literal = "ausente" if setting is None else setting.number.literal
        self._read[name] = ResolutionSetting(name, label, literal)
        if setting is None and self._request.spec.numerics is not None:
            self.refuse(
                name,
                DiagnosticCode.MISSING_FIELD,
                f"Falta o ajuste numérico {name} ({label}): ele não é escolhido em silêncio.",
                expected,
            )
        return setting


def _shown(value: Fraction) -> str:
    return f"{float(value):g}"
