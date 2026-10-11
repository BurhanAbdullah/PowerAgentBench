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
        }
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
