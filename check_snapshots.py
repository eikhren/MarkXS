#!/usr/bin/env python3
"""
Snapshot verifier for MarkXS fixtures.

Compares parser output against fixtures/expected/*.json.
Exit code is non-zero on any mismatch or missing snapshot.
"""
import json
import subprocess
import sys
from pathlib import Path
from typing import List


ROOT = Path(__file__).parent
FIXTURES = ROOT / "fixtures"
EXPECTED = FIXTURES / "expected"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_json(obj) -> str:
    return json.dumps(obj, indent=2, sort_keys=True)


def compare_snapshot(fixture: Path, expected: Path) -> List[str]:
    errors: List[str] = []
    if not expected.exists():
        errors.append(f"Expected snapshot missing: {expected}")
        return errors

    proc = subprocess.run(
        ["python3", str(ROOT / "parse_px.py"), str(fixture)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        errors.append(f"Parser failed for {fixture}: {proc.stderr.strip()}")
        return errors

    actual = json.loads(proc.stdout)
    expected_json = load_json(expected)

    if actual != expected_json:
        actual_str = canonical_json(actual)
        expected_str = canonical_json(expected_json)
        errors.append(f"Mismatch for {fixture} vs {expected}")
        errors.append("--- actual ---")
        errors.append(actual_str)
        errors.append("--- expected ---")
        errors.append(expected_str)
    return errors


def main() -> int:
    failures: List[str] = []
    for fixture in sorted(FIXTURES.glob("*.xs")):
        expected = EXPECTED / f"{fixture.stem}.json"
        failures.extend(compare_snapshot(fixture, expected))

    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    print("All snapshots match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
