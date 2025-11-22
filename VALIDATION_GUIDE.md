MARKXS VALIDATOR ALIGNMENT GUIDE

GOAL
- Align editor grammars and CLI validators to the MarkXS abstract syntax in XS.md, using identical recognition order and block rules.

RECOGNITION ORDER (APPLIED OUTSIDE FENCED CODE)
1) Header: only the first non-blank line; form HEADER_TAG ":" SPACE HEADER_TEXT with uppercase TAG.
2) MetadataLine: only immediately after the header while lines match KEY ":" SPACE VALUE.
3) Fence start/end: optional indent + "```" optionally + language tag; closing fence must match indent and have no trailing text.
4) BlankLine: whitespace only.
5) TableRow: optional indent + "|" as first non-space character.
6) SectionHeading: NUMBER ("." dotted ok) + "." + SPACE + UPPER CASE TITLE (+ optional ":" SPACE description).
7) WholeLineComment: optional spaces + "#".
8) BulletItem: optional spaces + ["-","*","+"] + SPACE + text.
9) ParagraphLine: any other non-empty line.
Content inside fences bypasses all other rules.

ALGORITHMIC NOTES
- Track firstNonBlankLineSeen and headerSeen to allow exactly one header candidate.
- Metadata mode begins only after a valid header and ends on the first blank line or non-metadata line.
- Table blocks are consecutive TableRow lines; a non-TableRow (including a comment) or blank line ends the table.
- Bullet lists are consecutive BulletItem lines with no blank lines or foreign block kinds between them.
- Section dotted numbers must be strictly numeric segments (e.g., 2.1.3), not arbitrary tokens.

INLINE COMMENT HANDLING
- Inline comments use "i#" and are allowed only in paragraph or bullet text outside fences.
- If "i#" appears in a header, metadata line, section heading, or fenced code, remove the substring from "i#" to end-of-line before further parsing/validation and flag the violation.

SCOPES (RECOMMENDED)
- Header tag: entity.name.section.header.xs; header text: string.unquoted.header-text.xs.
- Metadata key: support.type.property-name.metadata.xs; value: string.unquoted.metadata-value.xs.
- Section number: constant.numeric.section-number.xs; title: entity.name.section.title.xs; description: string.unquoted.section-description.xs.
- Paragraph: markup.paragraph.xs; bullet marker: punctuation.definition.list-item.xs; bullet text: markup.list.item.xs.
- Table row/header/cell: markup.table.row.xs / markup.table.header.xs / markup.table.cell.xs.
- Fence language tag: constant.language.fenced-code.language-tag.xs; fence body: markup.raw.block.code.xs.
- Inline code: markup.inline.raw.code.xs; inline label: entity.other.attribute-name.inline-label.xs.
- Comments: comment.line.number-sign.xs (whole-line); comment.line.inline.xs (inline).

FIXTURE USAGE
- Fixtures live in fixtures/*.xs with expectations noted in fixtures/README.md.
- A validator should run each file, classify lines per the order above, and assert pass/fail conditions described in the README.

CLI/EDITOR CHECKLIST
- Enforce header placement and metadata adjacency.
- Honor fence raw regions and indentation-matched closing fences.
- Apply table detection before section/comments/bullets as per order.
- Reject inline comments in forbidden contexts.
- Report violations referencing the MarkXS construct name used in XS.md/this guide.

TOOLS
- A reference parser `parse_px.py` is included. Run `python3 parse_px.py fixtures/valid-basic.xs` to emit a JSON AST following AST.md.
- Snapshots in `fixtures/expected/*.json` are generated from the reference parser with `loc` fields; wire these into CI to pin AST shape and diagnostics (use `python3 check_snapshots.py`).
