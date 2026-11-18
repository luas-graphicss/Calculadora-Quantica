from quantum_calculator.domain.cards import CatalogEntry, CatalogListing
from quantum_calculator.interfaces.serialization.encoding.common_sections import document_header
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_catalog(listing: CatalogListing) -> JsonObject:
    return {
        **document_header("catalog"),
        "version": listing.version,
        "cards": [_encode_entry(entry) for entry in listing.entries],
    }


def _encode_entry(entry: CatalogEntry) -> JsonObject:
    return {
        "identifier": entry.identifier,
        "version": entry.version,
        "area": entry.area,
        "problem_type": entry.problem_type,
        "title": entry.title,
        "domain": list(entry.domain),
        "method": {
            "identifier": entry.method.identifier,
            "nature": entry.method.nature.value,
            "justification": entry.method.justification,
        },
        "limitations": list(entry.limitations),
        "example": entry.example,
    }
