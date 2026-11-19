from qualification.documents import Expectation, ExpectedValue, Observation


def disagreements_with_oracle(expectation: Expectation, observation: Observation) -> list[str]:
    found = _verdict_differences(expectation, observation)
    if expectation["refusal"] is None and expectation["card"] != (observation["card"] or ""):
        found.append(f"card {observation['card']!r}, expected {expectation['card']!r}")
    for name, text in expectation["texts"].items():
        if observation["texts"].get(name) != text:
            found.append(f"{name} {observation['texts'].get(name)!r}, expected {text!r}")
    if expectation["refusal"] is not None and expectation["refusal"] not in observation["refusals"]:
        found.append(
            f"diagnostics {observation['refusals']}, expected to include {expectation['refusal']}"
        )
    return found + _value_differences(expectation["values"], observation)


def differences_from_homologation(
    expectation: Expectation, homologated: Observation, reproduced: Observation
) -> list[str]:
    found = _verdict_differences(expectation, reproduced)
    for attribute in ("card", "texts", "refusals"):
        if homologated[attribute] != reproduced[attribute]:
            found.append(
                f"{attribute} {reproduced[attribute]!r}, homologated {homologated[attribute]!r}"
            )
    return found + _value_differences(expectation["values"], reproduced)


def _verdict_differences(expectation: Expectation, observation: Observation) -> list[str]:
    compared = (
        ("exit code", observation["exit_code"], expectation["exit_code"]),
        ("verification", observation["verification"], expectation["verification"]),
        ("checks not passed", observation["not_passed"], expectation["not_passed"]),
    )
    return [
        f"{subject} {found!r}, expected {expected!r}"
        for subject, found, expected in compared
        if found != expected and (subject != "verification" or expected is not None)
    ]


def _value_differences(values: list[ExpectedValue], observation: Observation) -> list[str]:
    found = []
    for value in values:
        observed = observation["values"].get(value["name"])
        if observed is None:
            found.append(f"{value['name']} is missing from the answers")
            continue
        deviation = deviation_from(value, observed)
        if not deviation <= value["tolerance"]:
            found.append(
                f"{value['name']} = {observed!r} deviates {deviation:.3e} ({value['comparison']}) "
                f"from {value['expected']!r}, above {value['tolerance']:.3e}"
            )
    return found


def deviation_from(value: ExpectedValue, observed: float) -> float:
    difference = abs(observed - value["expected"])
    if value["comparison"] == "relative":
        return difference / abs(value["expected"])
    return difference
