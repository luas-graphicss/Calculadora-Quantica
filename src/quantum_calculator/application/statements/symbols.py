from enum import StrEnum

from quantum_calculator.application.statements.unit_expressions import (
    UNIT_EXPRESSION_FORM,
    UnitExpressionError,
    dimension_of_unit,
)
from quantum_calculator.domain.diagnostics import (
    Diagnostic,
    DiagnosticCode,
    json_pointer,
    quote_user_text,
)
from quantum_calculator.domain.dimensions import Dimension
from quantum_calculator.domain.ports import UnitRegistry
from quantum_calculator.domain.statements import (
    BoundSymbol,
    SymbolDeclaration,
    SymbolDomain,
    SymbolRole,
)
from quantum_calculator.notation.vocabulary import (
    NAME_EXPECTATION,
    RESERVED_NAMES,
    canonical_symbol_name,
)

_SECTION = "symbols"
_VARIABLE_ARGUMENT = 'o nome de um símbolo declarado com o papel "variable"'


class SymbolBinder:
    def __init__(self, units: UnitRegistry) -> None:
        self._units = units

    def bind(
        self, declarations: tuple[SymbolDeclaration, ...], diagnostics: list[Diagnostic]
    ) -> dict[str, BoundSymbol]:
        bound: dict[str, BoundSymbol] = {}
        for declaration in declarations:
            symbol = self._bind(declaration, bound, diagnostics)
            if symbol is not None:
                bound[symbol.name] = symbol
        for declaration in declarations:
            _check_argument(declaration, bound, diagnostics)
        return bound

    def _bind(
        self,
        declaration: SymbolDeclaration,
        bound: dict[str, BoundSymbol],
        diagnostics: list[Diagnostic],
    ) -> BoundSymbol | None:
        name = _canonical_name(declaration, bound, diagnostics)
        role = _option(SymbolRole, declaration.role, declaration.name, "role", diagnostics)
        domain = _option(SymbolDomain, declaration.domain, declaration.name, "domain", diagnostics)
        dimension = self._dimension(declaration, diagnostics)
        argument = _argument_name(declaration, role, diagnostics)
        if name is None or role is None or domain is None or dimension is None:
            return None
        if role is SymbolRole.FUNCTION and argument is None:
            return None
        return BoundSymbol(name, role, domain, dimension, declaration.unit, argument)

    def _dimension(
        self, declaration: SymbolDeclaration, diagnostics: list[Diagnostic]
    ) -> Dimension | None:
        try:
            return dimension_of_unit(declaration.unit, self._units)
        except UnitExpressionError as error:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCode.UNKNOWN_UNIT,
                    json_pointer(_SECTION, declaration.name, "unit"),
                    f"A unidade {quote_user_text(declaration.unit)} não foi aceita: {error}.",
                    UNIT_EXPRESSION_FORM,
                )
            )
            return None


def _canonical_name(
    declaration: SymbolDeclaration, bound: dict[str, BoundSymbol], diagnostics: list[Diagnostic]
) -> str | None:
    pointer = json_pointer(_SECTION, declaration.name)
    name = canonical_symbol_name(declaration.name)
    if name is None:
        code = DiagnosticCode.INVALID_SYMBOL_NAME
        message = f"{quote_user_text(declaration.name)} não é um nome de símbolo válido."
        expected = NAME_EXPECTATION
    elif name in RESERVED_NAMES:
        code = DiagnosticCode.RESERVED_NAME
        message = f"{quote_user_text(name)} é um nome reservado da notação."
        expected = f"um nome diferente de {', '.join(sorted(RESERVED_NAMES))}"
    elif name in bound:
        code = DiagnosticCode.DUPLICATE_FIELD
        message = f"O símbolo {quote_user_text(name)} foi declarado mais de uma vez."
        expected = "cada símbolo declarado uma única vez, em uma só grafia"
    else:
        return name
    diagnostics.append(Diagnostic(code, pointer, message, expected))
    return None


def _option[Option: StrEnum](
    options: type[Option], value: str, symbol: str, field: str, diagnostics: list[Diagnostic]
) -> Option | None:
    for option in options:
        if option.value == value:
            return option
    diagnostics.append(
        Diagnostic(
            DiagnosticCode.UNKNOWN_OPTION,
            json_pointer(_SECTION, symbol, field),
            f"{quote_user_text(value)} não é uma opção de {field}.",
            f"uma destas opções: {', '.join(option.value for option in options)}",
        )
    )
    return None


def _argument_name(
    declaration: SymbolDeclaration, role: SymbolRole | None, diagnostics: list[Diagnostic]
) -> str | None:
    pointer = json_pointer(_SECTION, declaration.name, "argument")
    if role is SymbolRole.FUNCTION and declaration.argument is None:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.MISSING_FIELD,
                pointer,
                f"A função {quote_user_text(declaration.name)} não diz de qual variável depende.",
                _VARIABLE_ARGUMENT,
            )
        )
    if role is not None and role is not SymbolRole.FUNCTION and declaration.argument is not None:
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.UNEXPECTED_FIELD,
                pointer,
                f'Só um símbolo com o papel "function" tem argumento; '
                f"{quote_user_text(declaration.name)} foi declarado como {role.value}.",
                'nenhum campo "argument" neste símbolo',
            )
        )
    if role is not SymbolRole.FUNCTION or declaration.argument is None:
        return None
    return canonical_symbol_name(declaration.argument) or declaration.argument


def _check_argument(
    declaration: SymbolDeclaration, bound: dict[str, BoundSymbol], diagnostics: list[Diagnostic]
) -> None:
    name = canonical_symbol_name(declaration.name)
    function = None if name is None else bound.get(name)
    if function is None or function.argument is None:
        return
    argument = bound.get(function.argument)
    if argument is None or argument.role is not SymbolRole.VARIABLE:
        del bound[function.name]
        diagnostics.append(
            Diagnostic(
                DiagnosticCode.NOT_A_VARIABLE,
                json_pointer(_SECTION, declaration.name, "argument"),
                f"O argumento {quote_user_text(function.argument)} da função "
                f"{quote_user_text(function.name)} não é uma variável declarada.",
                _VARIABLE_ARGUMENT,
            )
        )
