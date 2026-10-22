from __future__ import annotations

import json
from pathlib import Path

import pytest

from poweragentbench.benchmark_utils import load_solution, validate_action_values


ACTIONSPACE = {
    "action_index": {
        "tap_T1_up": {
            "min_value": 0.0,
            "max_value": 2.0,
            "step": 1.0,
        },
        "phase_shift_T9": {
            "min_value": -2.0,
            "max_value": 2.0,
            "step": 2.0,
        },
        "shed_load_L20": {
            "min_value": 0.0,
            "max_value": 5.0,
            "step": 2.5,
        },
    }
}


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (True, "numeric"),
        (False, "numeric"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
        (10**400, "finite"),
    ],
    ids=["true", "false", "nan", "positive-infinity", "negative-infinity", "huge-integer"],
)
def test_load_solution_rejects_invalid_numeric_values(
    tmp_path: Path, value: object, message: str
) -> None:
    path = tmp_path / "solution.json"
    path.write_text(
        json.dumps({"actions": [{"id": "tap_T1_up", "value": value}]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=message):
        load_solution(path)


@pytest.mark.parametrize(
    ("value", "message"),
    [
        (True, "numeric"),
        (False, "numeric"),
        (float("nan"), "finite"),
        (float("inf"), "finite"),
        (float("-inf"), "finite"),
        (10**400, "finite"),
    ],
    ids=["true", "false", "nan", "positive-infinity", "negative-infinity", "huge-integer"],
)
def test_validate_action_values_rejects_invalid_numeric_values(
    value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_action_values({"tap_T1_up": value}, ACTIONSPACE)


@pytest.mark.parametrize(
    ("action_id", "value", "expected"),
    [
        ("tap_T1_up", 0, 0.0),
        ("tap_T1_up", 1, 1.0),
        ("tap_T1_up", 1.0, 1.0),
        ("phase_shift_T9", -2, -2.0),
        ("shed_load_L20", 2.5, 2.5),
    ],
    ids=["zero", "integer", "float", "permitted-negative", "permitted-fraction"],
)
def test_load_solution_accepts_numeric_values_and_validates_defaults(
    tmp_path: Path, action_id: str, value: int | float, expected: float
) -> None:
    path = tmp_path / "solution.json"
    path.write_text(
        json.dumps({"actions": [{"id": action_id, "value": value}]}),
        encoding="utf-8",
    )

    loaded = load_solution(path)
    assert loaded == {action_id: expected}

    validated = validate_action_values(loaded, ACTIONSPACE)
    assert validated[action_id] == expected
    assert all(
        validated[other_id] == 0.0
        for other_id in ACTIONSPACE["action_index"]
        if other_id != action_id
    )
