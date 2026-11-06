#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
# How to run: python submission/validate_artifacts.py submission/award_candidate
# Self-check: python submission/validate_artifacts.py submission --self-check
"""Independently validate the supplied participant README's CSV contract."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parent.parent
DATA: Final = ROOT / "handover 2" / "01_participant_dataset"
GROUPS: Final = ("G1", "G2")


@dataclass(frozen=True, slots=True)
class InvalidSubmission(ValueError):
    reason: str

    def __str__(self) -> str:
        return self.reason


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise InvalidSubmission(reason)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        require(headers is not None, f"Missing header: {path}")
        return list(headers or []), list(reader)


@dataclass(frozen=True, slots=True)
class Inputs:
    composition: list[dict[str, str]]
    forecast: list[dict[str, str]]
    sites: list[dict[str, str]]
    timestamps: list[str]


def validate(inputs: Inputs) -> dict[str, str | int | float]:
    site_caps = {row["site_id"]: Decimal(row["capacity_kw"]) for row in inputs.sites}
    assignments = inputs.composition
    require(Counter(row["site_id"] for row in assignments) == Counter(site_caps.keys()),
            "Each supplied site must be assigned exactly once")
    require({row["group"] for row in assignments} == set(GROUPS), "Composition groups must be G1/G2")
    capacities = {g: sum((site_caps[row["site_id"]] for row in assignments if row["group"] == g),
                        Decimal(0)) for g in GROUPS}
    require(all(cap >= Decimal(20000) for cap in capacities.values()), "Each group needs >= 20000 kW")
    expected_times = {datetime.fromisoformat(t) for t in inputs.timestamps}
    expected = {(g, t) for g in GROUPS for t in expected_times}
    require(len(inputs.forecast) == len(expected), "Wrong forecast row count")
    actual = []
    values = []
    over_capacity = 0
    for row in inputs.forecast:
        timestamp = datetime.fromisoformat(row["ts"])
        require(timestamp.utcoffset() == timedelta(hours=9), "Timestamp must include KST +09:00")
        group = row["group"]
        require(group in GROUPS, "Forecast group must be G1/G2")
        actual.append((group, timestamp))
        value = float(row["forecast_kwh"])
        require(math.isfinite(value) and value >= 0, "Forecast values must be finite and nonnegative")
        values.append(value)
        over_capacity += value > float(capacities[group])
    require(len(set(actual)) == len(actual), "Duplicate forecast group/timestamp")
    require(set(actual) == expected, "Forecast timestamps differ from supplied SMP")
    return {"status": "PASS", "sites": len(assignments), "forecast_rows": len(actual),
            "hours_per_group": len(expected_times), "G1_capacity_kw": float(capacities["G1"]),
            "G2_capacity_kw": float(capacities["G2"]), "annual_gwh": sum(values) / 1e6,
            "zero_rows": values.count(0), "max_forecast_kwh": max(values),
            "rows_above_own_capacity": over_capacity,
            "first_ts": min(expected_times).isoformat(), "last_ts": max(expected_times).isoformat()}


def self_check(inputs: Inputs) -> list[str]:
    cases = []
    bad_composition = inputs.composition[:-1] + [inputs.composition[0]]
    cases.append(("duplicate_site", Inputs(bad_composition, inputs.forecast, inputs.sites, inputs.timestamps)))
    all_g1 = [dict(row, group="G1") for row in inputs.composition]
    cases.append(("invalid_groups", Inputs(all_g1, inputs.forecast, inputs.sites, inputs.timestamps)))
    unbalanced = [dict(row, group="G2" if i == 0 else "G1") for i, row in enumerate(inputs.composition)]
    cases.append(("capacity_below_minimum", Inputs(unbalanced, inputs.forecast, inputs.sites, inputs.timestamps)))
    for name, replacement in (
        ("duplicate_timestamp", inputs.forecast[1]),
        ("wrong_timestamp", dict(inputs.forecast[0], ts="2030-01-01 01:00:00+09:00")),
        ("naive_timestamp", dict(inputs.forecast[0], ts="2025-06-01 01:00:00")),
        ("negative", dict(inputs.forecast[0], forecast_kwh="-1")),
        ("infinite", dict(inputs.forecast[0], forecast_kwh="inf")),
        ("nan", dict(inputs.forecast[0], forecast_kwh="nan")),
    ):
        changed = [replacement] + inputs.forecast[1:]
        cases.append((name, Inputs(inputs.composition, changed, inputs.sites, inputs.timestamps)))
    passed = []
    for name, invalid in cases:
        try:
            validate(invalid)
        except InvalidSubmission:
            passed.append(name)
        else:
            raise InvalidSubmission(f"Self-check failed to reject {name}")
    return passed


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "submission" / "award_candidate"
    c_headers, composition = read_csv(folder / "composition.csv")
    f_headers, forecast = read_csv(folder / "forecast.csv")
    require(c_headers == ["site_id", "group"], "Wrong composition header")
    require(f_headers == ["group", "ts", "forecast_kwh"], "Wrong forecast header")
    _, sites = read_csv(DATA / "sites.csv")
    _, smp = read_csv(DATA / "smp.csv")
    inputs = Inputs(composition, forecast, sites, [row["ts"] for row in smp])
    report = validate(inputs)
    for filename in ("composition.csv", "forecast.csv"):
        report[f"{filename}_sha256"] = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
    if "--self-check" in sys.argv:
        report["self_checks_passed"] = ", ".join(self_check(inputs))
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
