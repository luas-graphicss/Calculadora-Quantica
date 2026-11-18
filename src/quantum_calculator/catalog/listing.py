from quantum_calculator.catalog.card_catalog import HOMOLOGATED_CARDS
from quantum_calculator.catalog.statement_catalog import HOMOLOGATED_STATEMENT_CARDS
from quantum_calculator.domain.cards import CatalogEntry, CatalogListing

CATALOG_VERSION = "1.1.0"


def catalog_entries() -> tuple[CatalogEntry, ...]:
    return (*HOMOLOGATED_CARDS, *HOMOLOGATED_STATEMENT_CARDS)


def catalog_listing() -> CatalogListing:
    return CatalogListing(version=CATALOG_VERSION, entries=catalog_entries())
