from quantum_calculator.application.statements.budget import (
    DEFAULT_WALL_SECONDS,
    MAX_WALL_SECONDS,
)
from quantum_calculator.application.workbench.describe_catalog import (
    DescribedChoice,
    WorkbenchCatalog,
)
from quantum_calculator.domain.rounding import DEFAULT_SIGNIFICANT_DIGITS, MAX_SIGNIFICANT_DIGITS
from quantum_calculator.domain.statements import Notation, SymbolDomain, SymbolRole
from quantum_calculator.domain.workbench.forms import (
    ArrayField,
    CardForm,
    NotationFields,
    QuantityField,
    RequestedFields,
)
from quantum_calculator.interfaces.api.documents import api_document
from quantum_calculator.interfaces.serialization.encoding.catalog_document import (
    encode_catalog_entry,
)
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_workbench_catalog(catalog: WorkbenchCatalog) -> JsonObject:
    return {
        **api_document("workbench_catalog"),
        "version": catalog.version,
        "vocabulary": {
            "notations": [notation.value for notation in Notation],
            "symbol_roles": [role.value for role in SymbolRole],
            "symbol_domains": [domain.value for domain in SymbolDomain],
        },
        "rounding": {
            "default_significant_digits": DEFAULT_SIGNIFICANT_DIGITS,
            "max_significant_digits": MAX_SIGNIFICANT_DIGITS,
        },
        "time_limit": {"default_seconds": DEFAULT_WALL_SECONDS, "max_seconds": MAX_WALL_SECONDS},
        "questions": [
            {
                "identifier": described.question.identifier,
                "question": described.question.question,
                "context": described.question.context,
                "choices": [_encode_choice(choice) for choice in described.choices],
            }
            for described in catalog.questions
        ],
    }


def _encode_choice(choice: DescribedChoice) -> JsonObject:
    return {
        "answer": choice.answer,
        "card": encode_catalog_entry(choice.card),
        "form": _encode_form(choice.form),
    }


def _encode_form(form: CardForm) -> JsonObject:
    return {
        "kind": form.kind.value,
        "confirmations": [
            {"key": item.key, "value": item.value, "statement": item.statement}
            for item in form.confirmations
        ],
        "quantities": [_encode_quantity(item) for item in form.quantities],
        "counts": [
            {"name": item.name, "symbol": item.symbol, "label": item.label} for item in form.counts
        ],
        "notation": None if form.notation is None else _encode_notation(form.notation),
        "arrays": [_encode_array(item) for item in form.arrays],
        "settings": [{"name": item.name, "label": item.label} for item in form.settings],
        "requested": None if form.requested is None else _encode_requested(form.requested),
        "covariance_models": list(form.covariance_models),
    }


def _encode_quantity(field: QuantityField) -> JsonObject:
    return {
        "name": field.name,
        "symbol": field.symbol,
        "label": field.label,
        "dimension": field.dimension,
        "units": list(field.units),
        "constants": [
            {"identifier": constant.identifier, "symbol": constant.symbol, "name": constant.name}
            for constant in field.constants
        ],
    }


def _encode_notation(fields: NotationFields) -> JsonObject:
    return {
        "has_statement": fields.has_statement,
        "has_equations": fields.has_equations,
        "has_conditions": fields.has_conditions,
        "has_candidate": fields.has_candidate,
        "symbols_carry_values": fields.symbols_carry_values,
    }


def _encode_array(field: ArrayField) -> JsonObject:
    return {
        "section": field.section,
        "member": field.member,
        "label": field.label,
        "rank": field.rank,
        "presence": field.presence.value,
        "is_normalizable": field.is_normalizable,
        "has_unit": field.has_unit,
    }


def _encode_requested(fields: RequestedFields) -> JsonObject:
    return {
        "quantity": fields.quantity,
        "label": fields.label,
        "units": list(fields.units),
        "presence": fields.presence.value,
    }
