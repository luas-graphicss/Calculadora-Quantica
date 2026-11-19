from datetime import datetime

from quantum_calculator.application.workbench.read_history import RunDetails
from quantum_calculator.domain.workbench.runs import ArtifactRole, StoredRun
from quantum_calculator.interfaces.api.documents import api_document
from quantum_calculator.interfaces.serialization.encoding.exact_values import JsonObject


def encode_run(run: StoredRun) -> JsonObject:
    return {
        "identifier": run.identifier,
        "origin": run.origin.value,
        "state": run.state.value,
        "parent_identifier": run.parent_identifier,
        "card": {"identifier": run.card_identifier, "title": run.card_title},
        "wall_seconds": run.wall_seconds,
        "package_version": run.package_version,
        "submitted_at": run.submitted_at.isoformat(),
        "started_at": _instant(run.started_at),
        "finished_at": _instant(run.finished_at),
        "verification_status": run.verification_status,
        "failure_category": run.failure_category,
        "headline": run.headline,
        "input_sha256": run.require_artifact(ArtifactRole.INPUT).sha256,
        "canonical_problem_sha256": run.require_artifact(ArtifactRole.PROBLEM).sha256,
    }


def encode_run_document(run: StoredRun) -> JsonObject:
    return {**api_document("run"), "run": encode_run(run)}


def encode_run_list(runs: tuple[StoredRun, ...]) -> JsonObject:
    return {**api_document("run_list"), "runs": [encode_run(run) for run in runs]}


def encode_run_details(details: RunDetails, display_units: tuple[str, ...]) -> JsonObject:
    return {
        **api_document("run_details"),
        "run": encode_run(details.run),
        "input": {"text": details.input_text},
        "problem": details.problem,
        "outcome": details.outcome,
        "display_units": list(display_units),
    }


def _instant(instant: datetime | None) -> str | None:
    return None if instant is None else instant.isoformat()
