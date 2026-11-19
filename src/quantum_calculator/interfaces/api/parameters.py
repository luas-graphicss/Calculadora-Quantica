from typing import Annotated

from fastapi import Header, Path, Query

from quantum_calculator.application.statements.budget import MAX_WALL_SECONDS

_RUN_IDENTIFIER = r"^[0-9a-f]{32}$"

RunIdentifier = Annotated[str, Path(pattern=_RUN_IDENTIFIER)]
TableName = Annotated[str, Path(pattern=r"^[a-z][a-z0-9_]{0,63}$")]
ComparedRun = Annotated[str, Query(pattern=_RUN_IDENTIFIER)]
ParentRun = Annotated[str | None, Query(pattern=_RUN_IDENTIFIER)]
TimeLimit = Annotated[float, Query(gt=0, le=MAX_WALL_SECONDS)]
DisplayUnit = Annotated[str | None, Query(min_length=1, max_length=16)]
IdempotencyKey = Annotated[str, Header(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")]
