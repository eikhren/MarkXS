SPEC: MARKXS ABSTRACT SYNTAX TREE (AST) MODEL v2.0

PURPOSE
- Define a deterministic AST shape derived from XS.md so editors and CLI tools emit identical structure for MarkXS (.xs) documents.
- Keep the AST minimal, lossless for semantics, and stable across implementations.

GENERAL RULES
- All nodes include: type (string) and optional loc {start: {line, column}, end: {line, column}} using 1-based positions.
- Recognition order from XS.md must be applied before node construction (see VALIDATION_GUIDE.md).
- Content inside fenced code blocks is not parsed; it is stored verbatim in FencedCodeBlock.content.
- Inline comments in illegal contexts must be stripped before further parsing; a Diagnostic SHOULD be emitted when this occurs.

ROOT
- Document
  - header: Header
  - metadata: MetadataEntry[]
  - body: Block[] (ordered as they appear)
  - diagnostics?: Diagnostic[]

BLOCK NODES
- Header
  - tag: string (UPPER CASE words)
  - text: string (header text after ": ")
- MetadataEntry
  - key: string
  - value: string
- Section
  - number: int[] (dotted sequence, e.g., [4,2,1])
  - title: string (UPPER CASE words)
  - description?: string (text after ":" if present)
  - body: Block[]
  - rawHeading?: string (optional exact heading text)
  - level: number (derived = length of number)
- Paragraph
  - inline: InlineNode[]
- BulletList
  - items: BulletItem[]
- BulletItem
  - marker: "-" | "*" | "+"
  - inline: InlineNode[]
  - continuation?: string[] (raw wrapped lines indented under the item; implementations MAY normalize these into inline)
- Table
  - header: TableRow
  - align?: TableRow (alignment row if present)
  - rows: TableRow[]
- TableRow
  - cells: string[] (cell text trimmed of leading/trailing cell bars)
- FencedCodeBlock
  - infoString?: string (language tag, unparsed)
  - indent: number (count of leading spaces on fence lines)
  - content: string[] (raw lines between fences)
- WholeLineComment
  - text: string (excluding leading "#")
- BlankLine (optional retention; MAY be omitted if not needed for formatting)

INLINE NODES
- Text
  - value: string
- InlineCode
  - code: string
- InlineLabel
  - identifier: string
  - text?: string (optional trailing text after ":")
- InlineComment
  - text: string (content after "i#"; only present when the context permits inline comments)

DIAGNOSTICS (OPTIONAL BUT RECOMMENDED)
- Diagnostic
  - severity: "error" | "warning" | "info"
  - message: string
  - loc?: {line, column}
  - code?: string (implementation-defined identifier)

SECTION NESTING
- Sections are nested by dotted numbering:
  - A section with number [n] attaches to the Document body when no parent exists.
  - A section with number [a,b,...] is nested under the nearest ancestor whose number prefixes it (e.g., [2,1] nests under [2]).
  - If numbering is invalid (e.g., missing parent), create the Section at the document level and emit a Diagnostic.

RECOGNITION AND CANONICALIZATION NOTES
- Apply block recognition precedence before building nodes to avoid ambiguity (header > metadata > fence > blank > table > section > whole-line comment > bullet > paragraph).
- Table blocks end on the first non-table line (including comments and blanks).
- Bullet lists are contiguous bullet items; a different block type or blank line ends the list.
- Inline parsing:
  - Extract InlineCode using backticks.
  - Extract InlineLabel using IDENTIFIER ":".
  - InlineComment ("i#") is kept only in paragraph or bullet contexts.
  - Remaining text becomes Text segments.

EXAMPLE (TRUNCATED) FOR fixtures/valid-basic.xs
```json
{
  "type": "Document",
  "header": {"type": "Header", "tag": "SPEC", "text": "MarkXS Validator Fixture"},
  "metadata": [
    {"type": "MetadataEntry", "key": "Title", "value": "Basic Valid Sample"},
    {"type": "MetadataEntry", "key": "Version", "value": "2.0"},
    {"type": "MetadataEntry", "key": "Study ID", "value": "MXS-VAL-001"}
  ],
  "body": [
    {
      "type": "Section",
      "number": [1],
      "title": "INTRODUCTION",
      "body": [
        {
          "type": "Paragraph",
          "inline": [
            {"type": "Text", "value": "This paragraph includes a label "},
            {"type": "InlineLabel", "identifier": "Note", "text": " inline guidance and an allowed inline comment "},
            {"type": "InlineComment", "text": "trailing context ignored."}
          ]
        }
      ]
    }
  ]
}
```

INTEGRATION STEPS
- Update editor grammar emitters and CLI validators to produce the above node types and fields.
- Add diagnostics where XS.md rules are violated, using the recognition order and inline comment stripping rules.
- Normalize section nesting via dotted numbers to keep tree structure consistent across tools.
