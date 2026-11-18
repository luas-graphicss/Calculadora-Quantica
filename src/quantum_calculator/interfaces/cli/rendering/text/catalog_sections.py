from quantum_calculator.domain.cards import CatalogEntry, CatalogListing
from quantum_calculator.interfaces.cli.rendering.text.formatting import section


def catalog_lines(listing: CatalogListing) -> list[str]:
    lines = [f"Catálogo {listing.version}: {len(listing.entries)} fichas homologadas"]
    for entry in listing.entries:
        lines += section(f"{entry.identifier} {entry.version}", _entry_lines(entry))
    return lines


def _entry_lines(entry: CatalogEntry) -> list[str]:
    method = entry.method
    return [
        entry.title,
        f"área: {entry.area}; tipo: {entry.problem_type}",
        f"método: {method.identifier} ({method.nature.value})",
        *(f"domínio: {item}" for item in entry.domain),
        *(f"limitação: {item}" for item in entry.limitations),
        f"exemplo: {entry.example}",
    ]
