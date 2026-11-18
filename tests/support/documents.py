import copy
import json
from pathlib import Path
from typing import Self


class ProblemDocument:
    def __init__(self, content: dict[str, object]) -> None:
        self._content = content

    @classmethod
    def load(cls, path: Path) -> Self:
        content = json.loads(path.read_text("utf-8"))
        if not isinstance(content, dict):
            raise TypeError(f"{path} does not hold a JSON object")
        return cls(content)

    def with_value(self, pointer: str, value: object) -> Self:
        content = copy.deepcopy(self._content)
        *parents, key = pointer.removeprefix("/").split("/")
        _descend(content, parents)[key] = value
        return type(self)(content)

    def without(self, pointer: str) -> Self:
        content = copy.deepcopy(self._content)
        *parents, key = pointer.removeprefix("/").split("/")
        del _descend(content, parents)[key]
        return type(self)(content)

    def encode(self) -> bytes:
        return json.dumps(self._content, ensure_ascii=False).encode("utf-8")


def _descend(content: dict[str, object], keys: list[str]) -> dict[str, object]:
    for key in keys:
        child = content[key]
        if not isinstance(child, dict):
            raise TypeError(f"{key} is not a JSON object")
        content = child
    return content
