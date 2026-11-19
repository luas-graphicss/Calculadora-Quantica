from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from quantum_calculator.interfaces.serialization.decoding.json_document import MAX_DOCUMENT_BYTES
from support.api import RUNS, read_run, signed_in_api, solved, submit
from support.processes import wait_until
from support.sessions import LONG_CALCULATION, TIME_LIMIT, calculation_processes

_CATALOG = "/api/v1/catalog"
_VALIDATIONS = "/api/v1/validations"
_COMPARISONS = "/api/v1/comparisons"
_WIDTH_OF_ONE_NANOMETRE = b'"value": 1,\n      "unit": "nm"'
_WIDTH_OF_TWO_NANOMETRES = b'"value": 2,\n      "unit": "nm"'


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with signed_in_api(tmp_path / "profile") as opened:
        yield opened


@pytest.fixture
def well(reference_cases: Path) -> bytes:
    return (reference_cases / "electron_box_1nm.json").read_bytes()


def test_the_catalog_is_organised_by_physical_question_with_a_form_per_card(
    client: TestClient,
) -> None:
    catalog = client.get(_CATALOG).json()

    questions = catalog["questions"]
    closed_form = questions[0]["choices"][0]
    assert (catalog["document"], catalog["api_version"]) == ("workbench_catalog", "1.0")
    assert all(question["question"].endswith("?") for question in questions)
    assert closed_form["card"]["identifier"] == "quantum.infinite_square_well.energy_level"
    assert [field["name"] for field in closed_form["form"]["quantities"]] == ["mass", "width"]
    assert closed_form["form"]["requested"]["units"] == ["J", "eV", "meV", "keV", "MeV"]


def test_validation_shows_the_interpretation_and_the_plan_without_recording_a_run(
    client: TestClient, well: bytes
) -> None:
    response = client.post(_VALIDATIONS, content=well)

    interpretation = response.json()
    assert response.status_code == 200
    assert interpretation["document"] == "validation"
    assert interpretation["plan"]["method"] == "closed_form.infinite_square_well_energy"
    assert client.get(RUNS).json()["runs"] == []


def test_an_invalid_input_is_answered_with_the_diagnostic_and_where_it_applies(
    client: TestClient, reference_cases: Path
) -> None:
    source = (reference_cases / "rejected" / "width_in_seconds.json").read_bytes()

    validated = client.post(_VALIDATIONS, content=source)
    submitted = client.post(RUNS, content=source, headers={"Idempotency-Key": "refused-key-1"})

    (diagnostic,) = validated.json()["diagnostics"]
    assert (validated.status_code, submitted.status_code) == (422, 422)
    assert submitted.json() == validated.json()
    assert diagnostic["code"] == "dimension_mismatch"
    assert diagnostic["pointer"] == "/parameters/width/unit"
    assert client.get(RUNS).json()["runs"] == []


def test_a_document_above_the_size_limit_is_refused_as_an_invalid_input(
    client: TestClient,
) -> None:
    response = client.post(_VALIDATIONS, content=b" " * (MAX_DOCUMENT_BYTES + 1024))

    assert response.status_code == 422
    assert response.json()["category"] == "invalid_input"


def test_a_transport_repetition_of_a_submission_returns_the_same_run(
    client: TestClient, well: bytes
) -> None:
    first = client.post(RUNS, content=well, headers={"Idempotency-Key": "well-submission-1"})
    repeated = client.post(RUNS, content=well, headers={"Idempotency-Key": "well-submission-1"})

    assert (first.status_code, repeated.status_code) == (202, 200)
    assert repeated.json()["run"]["identifier"] == first.json()["run"]["identifier"]
    assert len(client.get(RUNS).json()["runs"]) == 1


def test_reusing_a_key_for_another_input_is_a_conflict(client: TestClient, well: bytes) -> None:
    solved(client, well, "well-submission-1")
    wider = well.replace(_WIDTH_OF_ONE_NANOMETRE, _WIDTH_OF_TWO_NANOMETRES)

    response = client.post(RUNS, content=wider, headers={"Idempotency-Key": "well-submission-1"})

    assert (response.status_code, response.json()["code"]) == (409, "idempotency_conflict")
    assert len(client.get(RUNS).json()["runs"]) == 1


def test_a_submission_without_an_idempotency_key_is_not_accepted(
    client: TestClient, well: bytes
) -> None:
    response = client.post(RUNS, content=well)

    assert (response.status_code, response.json()["code"]) == (400, "invalid_request")
    assert client.get(RUNS).json()["runs"] == []


def test_a_finished_run_keeps_its_input_its_answer_and_its_evidence(
    client: TestClient, well: bytes
) -> None:
    details = solved(client, well, "well-submission-1")

    run = details["run"]
    assert (run["state"], run["verification_status"]) == ("succeeded", "passed")
    assert run["headline"] == "E = 0.3760301621 eV"
    assert details["input"]["text"] == well.decode()
    assert details["problem"]["plan"]["nature"] == "exact"
    assert details["outcome"]["verification"]["status"] == "passed"
    assert details["display_units"] == ["J", "eV", "meV", "keV", "MeV"]


def test_changing_the_display_unit_converts_the_stored_answer_and_starts_no_run(
    client: TestClient, well: bytes
) -> None:
    identifier = solved(client, well, "well-submission-1")["run"]["identifier"]

    shown = client.get(f"{RUNS}/{identifier}/answers", params={"unit": "meV"}).json()
    refused = client.get(f"{RUNS}/{identifier}/answers", params={"unit": "nm"})

    (energy,) = shown["answers"]
    assert (energy["value"], energy["unit"]) == ("376.0301621", "meV")
    assert (refused.status_code, refused.json()["code"]) == (422, "display_unit_refused")
    assert len(client.get(RUNS).json()["runs"]) == 1


def test_widening_the_well_adds_a_linked_run_and_the_comparison_shows_a_quarter(
    client: TestClient, well: bytes
) -> None:
    wider = well.replace(_WIDTH_OF_ONE_NANOMETRE, _WIDTH_OF_TWO_NANOMETRES)
    narrow = solved(client, well, "well-1nm-key")["run"]

    wide = solved(client, wider, "well-2nm-key", parent=narrow["identifier"])["run"]

    compared = {"base": narrow["identifier"], "other": wide["identifier"]}
    comparison = client.get(_COMPARISONS, params=compared).json()
    (energy,) = comparison["answers"]
    listed = [run["identifier"] for run in client.get(RUNS).json()["runs"]]
    assert wide["parent_identifier"] == narrow["identifier"]
    assert comparison["input_differences"] == [
        {"pointer": "/parameters/width/value", "base": "1", "other": "2"}
    ]
    assert (energy["base"]["value"], energy["other"]["value"]) == ("0.3760301621", "0.09400754053")
    assert energy["ratio"] == "0.25"
    assert comparison["version_divergences"] == []
    assert listed == [wide["identifier"], narrow["identifier"]]


def test_a_spectrum_is_served_as_tables_with_units_and_as_csv(
    client: TestClient, numerical_cases: Path
) -> None:
    source = (numerical_cases / "electron_box_1nm_discrete.json").read_bytes()
    details = solved(client, source, "spectrum-key-1")
    identifier = details["run"]["identifier"]

    table = client.get(f"{RUNS}/{identifier}/tables/eigenfunctions").json()
    exported = client.get(f"{RUNS}/{identifier}/tables/eigenfunctions/csv")

    listed = details["outcome"]["result"]["tables"][0]
    described = [
        (column["symbol"], column["unit"], len(column["values"])) for column in table["columns"]
    ]
    header, first_row, *_ = exported.text.splitlines()
    assert (listed["name"], listed["rows"]) == ("eigenfunctions", 513)
    assert "values" not in listed["columns"][0]
    assert described[:2] == [("x", "m", 513), ("psi_1(x)", "m^-1/2", 513)]
    assert header == "x [m],psi_1(x) [m^-1/2],psi_2(x) [m^-1/2],psi_3(x) [m^-1/2]"
    assert first_row == "0.0,0.0,0.0,0.0"
    assert exported.headers["content-type"] == "text/csv; charset=utf-8"
    assert exported.headers["content-disposition"] == 'attachment; filename="eigenfunctions.csv"'


def test_unknown_runs_unknown_tables_and_malformed_identifiers_are_told_apart(
    client: TestClient, well: bytes
) -> None:
    identifier = solved(client, well, "well-submission-1")["run"]["identifier"]

    absent_run = client.get(f"{RUNS}/{'0' * 32}")
    absent_table = client.get(f"{RUNS}/{identifier}/tables/eigenfunctions")
    malformed = client.get(f"{RUNS}/not-a-run")

    assert (absent_run.status_code, absent_run.json()["code"]) == (404, "run_not_found")
    assert (absent_table.status_code, absent_table.json()["code"]) == (404, "table_not_found")
    assert (malformed.status_code, malformed.json()["code"]) == (400, "invalid_request")


def test_a_wrong_candidate_is_recorded_as_calculated_and_not_verified(
    client: TestClient, symbolic_cases: Path
) -> None:
    source = (symbolic_cases / "decay_candidate_wrong_initial_value.json").read_bytes()

    details = solved(client, source, "candidate-review-1")

    checks = details["outcome"]["verification"]["checks"]
    failed = [check for check in checks if check["status"] == "failed"]
    assert (details["run"]["state"], details["run"]["verification_status"]) == (
        "succeeded",
        "failed",
    )
    assert [check["identifier"] for check in failed] == ["initial_condition"]
    assert failed[0]["statement"] == (
        "A função informada assume o valor declarado no ponto da condição inicial."
    )


def test_cancelling_a_long_calculation_ends_the_run_without_a_result(client: TestClient) -> None:
    identifier = submit(client, LONG_CALCULATION, "long-calculation-1", time_limit=TIME_LIMIT)[
        "identifier"
    ]
    wait_until(lambda: read_run(client, identifier)["run"]["state"] == "running")

    exported = client.get(f"{RUNS}/{identifier}/package")
    cancelled = client.post(f"{RUNS}/{identifier}/cancellation").json()["run"]

    details = read_run(client, identifier)
    assert (exported.status_code, exported.json()["code"]) == (409, "run_still_active")
    assert cancelled["state"] == "cancelled"
    assert (details["run"]["state"], details["run"]["headline"]) == ("cancelled", None)
    assert (details["run"]["verification_status"], details["outcome"]) == (None, None)
    wait_until(lambda: not calculation_processes())


def test_cancelling_a_finished_run_changes_nothing(client: TestClient, well: bytes) -> None:
    finished = solved(client, well, "well-submission-1")["run"]

    response = client.post(f"{RUNS}/{finished['identifier']}/cancellation")

    assert response.status_code == 200
    assert response.json()["run"] == finished
