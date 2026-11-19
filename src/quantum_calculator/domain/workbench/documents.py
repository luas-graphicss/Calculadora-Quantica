from collections.abc import Mapping, Sequence

type Document = Mapping[str, object]


def member(document: Document, *path: str) -> object | None:
    current: object = document
    for key in path:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def text_member(document: Document, *path: str) -> str | None:
    found = member(document, *path)
    return found if isinstance(found, str) else None


def object_member(document: Document, *path: str) -> Document | None:
    found = member(document, *path)
    return found if isinstance(found, Mapping) else None


def object_members(document: Document, *path: str) -> tuple[Document, ...]:
    found = member(document, *path)
    if isinstance(found, str) or not isinstance(found, Sequence):
        return ()
    return tuple(item for item in found if isinstance(item, Mapping))
