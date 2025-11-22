# MarkXS Reference Parser and Fixtures

This repository holds the MarkXS specification documents, a small reference parser that emits JSON ASTs, and fixtures with pinned outputs for validation work.

## Contents
- `XS.md` — normative MarkXS syntax rules.
- `AST.md` — canonical AST shape produced by parsers.
- `VALIDATION_GUIDE.md` — recognition order and alignment guidance for tooling.
- `parse_xs.py` — reference parser that reads a `.xs` file and prints the AST as JSON.
- `fixtures/` — sample `.xs` files plus `fixtures/expected/*.json` snapshots.
- `check_snapshots.py` — compares parser output against the expected snapshots to guard AST stability.

## Requirements
- Python 3.8+ (no external dependencies).

## Usage
Run the parser directly:
```bash
python3 parse_xs.py fixtures/valid-basic.xs > /tmp/out.json
```

Compare all fixtures against their snapshots:
```bash
python3 check_snapshots.py
```

Generate a new snapshot for a fixture by overwriting the corresponding file under `fixtures/expected/`, for example:
```bash
python3 parse_xs.py fixtures/recognition-precedence.xs > fixtures/expected/recognition-precedence.json
```

## Notes
- Location fields are 1-based and retained in snapshots to make diffs stable.
- Inline comments are stripped and reported when they appear in forbidden contexts, matching the behaviors described in `XS.md` and `VALIDATION_GUIDE.md`.
