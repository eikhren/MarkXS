SPEC: MARKXS (MARKXPRESSIVESYNTAX) - ABSTRACT SYNTAX SPECIFICATION v2.0

1. PURPOSE AND NORMS
MarkXS defines a minimal, deterministic abstract syntax for study materials so editors and CLI tools behave identically.
All normative terms follow RFC 2119:
- MUST and MUST NOT indicate absolute requirements.
- SHOULD and SHOULD NOT indicate strong recommendations; deviations must be documented.
- MAY indicates optional behavior.
MarkXS exists to guarantee unambiguous authoring, uniform highlighting scopes, and fully aligned parsing.

2. DOCUMENT IDENTITY
2.1 File Association
- Files ending with ".xs" MUST be treated as MarkXS.
- Files without the extension MAY be treated as MarkXS only when the first non-blank line satisfies the required header form.

2.2 Header Line
- The first non-blank line MUST be the header and MUST start at column 1.
- Form: HEADER_TAG ":" SPACE HEADER_TEXT.
- HEADER_TAG consists of one or more UPPER CASE words separated by single spaces and contains no punctuation.
- HEADER_TEXT is free form text.
- Recommended scopes: HEADER_TAG uses entity.name.section.header.xs; HEADER_TEXT uses string.unquoted.header-text.xs.
- Example: SPEC: MarkXS Production Study Specification

3. ABSTRACT SYNTAX OVERVIEW
- Block kinds: Header, MetadataLine, SectionHeading, Paragraph, BulletItem (forming a BulletList), TableRow, FencedCodeBlock, WholeLineComment, BlankLine.
- Recognition precedence outside fenced code:
  1) Header (first non-blank line only).
  2) MetadataLine (only immediately after the header).
  3) Fenced code fences (start or end).
  4) Blank lines (whitespace only).
  5) Table rows (optional indentation followed by "|").
  6) Section headings.
  7) Whole-line comments.
  8) Bullet items using "-", "*", or "+".
  9) Paragraph lines (fallback for non-empty lines).
- Content inside fenced code blocks is raw and bypasses all other rules.
- A bullet list is a contiguous sequence of BulletItem lines with no intervening blank lines or other block types.

4. METADATA BLOCK
- An optional metadata block MAY follow the header.
- Form: optional spaces, KEY ":" SPACE VALUE.
- KEY accepts letters, digits, underscores, and hyphens; multi-word keys use single spaces.
- VALUE is free form text.
- The block begins at the first non-blank line after the header when that line matches the metadata form.
- The block ends at the first blank line or the first line that does not match the metadata form; no other content may appear before termination.
- Recommended scopes: keys use support.type.property-name.metadata.xs; values use string.unquoted.metadata-value.xs.
- Example:
  Title: MarkXS Conformance Tests
  Version: 2.0
  Study ID: MXS-2025-02

5. SECTION HEADINGS
- Section headings MUST start at column 1.
- Form: NUMBER "." SPACE TITLE, where NUMBER is a positive integer or dotted sequence (e.g., 4.2.1) and TITLE is one or more UPPER CASE words separated by single spaces.
- An optional description MAY follow the title as ":" SPACE DESCRIPTION.
- Subsections MUST use dotted numeric prefixes aligned to their parent section numbering.
- Recommended scopes: numbers use constant.numeric.section-number.xs; titles use entity.name.section.title.xs; optional descriptions use string.unquoted.section-description.xs.
- Example: 4.2 PARAGRAPH RULES: Wrapping and indentation

6. PARAGRAPHS AND BULLET LISTS
6.1 Paragraphs
- A paragraph is a contiguous set of non-empty lines that do not match header, metadata, section, table, fenced code, or bullet item forms.
- Paragraphs are separated by at least one blank line.
- Lines may wrap; multiple physical lines represent one logical paragraph.
- Recommended scope: markup.paragraph.xs; inline structures retain their own scopes.

6.2 Bullet Lists
- A bullet item begins with optional spaces, one of "-", "*", or "+", a single space, and item text.
- Wrapped lines MUST indent to the start of the text portion or deeper.
- Consecutive bullet items without intervening blank lines form a single bullet list.
- Recommended scopes: bullet markers use punctuation.definition.list-item.xs; bullet text uses markup.list.item.xs.

7. TABLES
- A table block is one or more consecutive lines that begin, after optional indentation, with "|".
- Cells are separated by "|" characters.
- The first row is the header row; the second row MAY define alignment; remaining rows are data.
- Fenced code blocks MUST NOT begin inside table blocks.
- Whole-line comments are not table rows and terminate the table block.
- Recommended scopes: rows use markup.table.row.xs; headers use markup.table.header.xs; cells use markup.table.cell.xs.

8. FENCED CODE BLOCKS
- Opening delimiter: optional spaces followed by "```" optionally followed by a language tag.
- Closing delimiter: matching indentation and bare "```" with no trailing text.
- Language tags MAY be provided and SHOULD use constant.language.fenced-code.language-tag.xs.
- Content between fences is raw: inline structures, bullets, tables, and headings are not interpreted.
- Recommended scope: markup.raw.block.code.xs.

9. INLINE STRUCTURES
9.1 Inline Code
- Inline code uses single backticks: `CODE`.
- Backticks inside code MUST be escaped or avoided.
- Scope: markup.inline.raw.code.xs.

9.2 Emphasis
- "*" and "_" characters are preserved but carry no intrinsic MarkXS scope.
- Downstream tools MAY interpret emphasis.

9.3 Inline Labels
- Form: IDENTIFIER ":" optionally followed by text.
- IDENTIFIER contains letters, digits, underscores, or hyphens with no spaces; multi-word concepts MUST be encoded without spaces.
- May appear anywhere in paragraphs or bullet items.
- Scope: entity.other.attribute-name.inline-label.xs for the token up to ":".

10. COMMENTS
10.1 Whole-Line Comments
- Begin with optional spaces followed by "#".
- Treated as comments outside fenced code blocks and ignored by parsers.
- Scope: comment.line.number-sign.xs.

10.2 Inline Comments
- Introduced by "i#" within paragraph or bullet text and extend to end of line.
- MUST NOT appear in headers, metadata lines, section headings, or fenced code blocks.
- If an inline comment appears in an illegal context, tools MUST remove the region from "i#" to end of line before further parsing or validation.
- Scope: comment.line.inline.xs.

11. BLANK LINES
- Contain only whitespace.
- Separate paragraphs, bullet lists, metadata blocks, and body content.
- MAY be ignored at the beginning or end of a file.

12. TOOLING PARITY
- Editors MUST follow MarkXS structure and apply recommended scopes.
- CLI tools MUST use identical recognition rules and SHOULD report violations referencing MarkXS constructs.

13. CONFORMANCE CHECKLIST
- File identity: ".xs" extension or valid header present at column 1.
- Header and metadata: header uses required form; metadata keys/values follow defined rules and appear immediately after the header.
- Structure: section numbering and formatting follow this specification.
- Text blocks: paragraphs and bullet lists obey wrapping and indentation rules.
- Inline structures: inline code, labels, and emphasis follow allowed forms.
- Comments: whole-line comments start with "#"; inline comments appear only in allowed contexts.
- Code fences: delimiters match; content treated as raw.
- Tables: rows start with "|"; header row present; no fenced code blocks inside tables.
- Consistency: all MUST requirements satisfied; deviations from SHOULD rules documented.

End of Specification.
