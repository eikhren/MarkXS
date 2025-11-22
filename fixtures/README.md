MARKXS VALIDATION FIXTURES

- valid-basic.xs: Fully conformant sample covering header, metadata, sections, paragraphs, bullets, tables, fences, inline labels, and allowed inline comments.
- invalid-inline-comment-header.xs: Header contains "i#" inline comment; validator should flag and/or strip the inline comment per spec.
- invalid-table-fence.xs: Fenced code delimiter begins inside a table; validator should reject.
- recognition-precedence.xs: Exercises recognition order (tables before comments/bullets/sections, table termination on comment, metadata adjacency, dotted sections, and paragraph fallback).

Snapshots:
- fixtures/expected/*.json hold AST outputs (with loc) from the reference parser for each fixture. Use them to assert shape and diagnostics in CI. Run `python3 check_snapshots.py` to verify.
