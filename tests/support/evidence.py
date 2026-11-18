ENVIRONMENT_SECTION = "\nAmbiente\n"


def scientific_content(document: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in document.items() if key != "environment"}


def before_environment(report: str) -> str:
    if ENVIRONMENT_SECTION not in report:
        raise ValueError("the report has no environment section")
    return report.split(ENVIRONMENT_SECTION)[0]
