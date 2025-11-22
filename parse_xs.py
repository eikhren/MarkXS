#!/usr/bin/env python3
import json
import re
import sys
from typing import List, Dict, Any, Optional, Tuple


HEADER_RE = re.compile(r"^([A-Z]+(?: [A-Z]+)*)\: (.+)$")
METADATA_RE = re.compile(r"^\s*([A-Za-z0-9_-]+(?: [A-Za-z0-9_-]+)*): (.*)$")
SECTION_RE = re.compile(r"^(\d+(?:\.\d+)*)\.? ([A-Z](?:[A-Z ]*[A-Z])?)(?:: (.*))?$")
BULLET_RE = re.compile(r"^(\s*)([-*+]) (.+)$")
TABLE_RE = re.compile(r"^\s*\|")
FENCE_RE = re.compile(r"^(\s*)```(.*)$")
COMMENT_RE = re.compile(r"^\s*#")


def make_loc(start_line: int, start_col: int, end_line: Optional[int] = None, end_col: Optional[int] = None) -> Dict[str, Dict[str, int]]:
    return {
        "start": {"line": start_line, "column": start_col},
        "end": {"line": end_line if end_line is not None else start_line, "column": end_col if end_col is not None else start_col},
    }


def strip_illegal_inline_comment(line: str, line_no: int, diagnostics: List[Dict[str, Any]]) -> str:
    """Remove inline comment in contexts where it is not allowed and record a diagnostic."""
    in_code = False
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "`":
            in_code = not in_code
            i += 1
            continue
        if not in_code and line.startswith("i#", i):
            diagnostics.append(
                {
                    "severity": "warning",
                    "message": "Inline comment not allowed in this context; stripped before parsing.",
                    "loc": {"line": line_no, "column": i + 1},
                    "code": "INLINE_COMMENT_ILLEGAL",
                }
            )
            return line[:i].rstrip()
        i += 1
    return line


def strip_inline_comment_for_detection(line: str) -> str:
    """Remove inline comment without emitting diagnostics (used for lookahead checks)."""
    in_code = False
    for i, ch in enumerate(line):
        if ch == "`":
            in_code = not in_code
            continue
        if not in_code and line.startswith("i#", i):
            return line[:i].rstrip()
    return line


def parse_inline(text: str, allow_inline_comment: bool, line_no: int, start_col: int = 1) -> List[Dict[str, Any]]:
    """Parse inline structures: code, labels, inline comments, and text with locations."""
    # First, locate inline comment if allowed.
    comment_pos = None
    in_code = False
    for idx, ch in enumerate(text):
        if ch == "`":
            in_code = not in_code
        if allow_inline_comment and not in_code and text.startswith("i#", idx):
            comment_pos = idx
            break
    if comment_pos is not None:
        prefix = text[:comment_pos]
        nodes = parse_inline_without_comment(prefix, line_no, start_col)
        nodes.append(
            {
                "type": "InlineComment",
                "text": text[comment_pos + 2 :].lstrip(),
                "loc": make_loc(line_no, start_col + comment_pos, line_no, start_col + len(text)),
            }
        )
        return nodes

    return parse_inline_without_comment(text, line_no, start_col)


def parse_inline_without_comment(text: str, line_no: int, start_col: int) -> List[Dict[str, Any]]:
    """Parse inline code and labels, treating the remainder as text, with locations."""
    result: List[Dict[str, Any]] = []
    in_code = False
    code_start = 0
    plain_start = 0
    i = 0
    while i < len(text):
        ch = text[i]
        if ch == "`":
            if in_code:
                # close code
                result.append(
                    {
                        "type": "InlineCode",
                        "code": text[code_start:i],
                        "loc": make_loc(line_no, start_col + code_start, line_no, start_col + i),
                    }
                )
                plain_start = i + 1
                in_code = False
            else:
                if plain_start < i:
                    parse_labels_into(text[plain_start:i], result, line_no, start_col + plain_start)
                code_start = i + 1
                in_code = True
            i += 1
            continue
        i += 1

    if in_code:
        # unmatched backtick, treat as text from opening backtick
        plain_start = code_start - 1
    if plain_start < len(text):
        parse_labels_into(text[plain_start:], result, line_no, start_col + plain_start)
    return result


LABEL_RE = re.compile(r"([A-Za-z0-9_-]+):")


def parse_labels_into(text: str, out: List[Dict[str, Any]], line_no: int, base_col: int) -> None:
    pos = 0
    while True:
        match = LABEL_RE.search(text, pos)
        if not match:
            remaining = text[pos:]
            if remaining:
                out.append(
                    {"type": "Text", "value": remaining, "loc": make_loc(line_no, base_col + pos, line_no, base_col + len(text))}
                )
            return
        if match.start() > pos:
            out.append(
                {
                    "type": "Text",
                    "value": text[pos:match.start()],
                    "loc": make_loc(line_no, base_col + pos, line_no, base_col + match.start()),
                }
            )
        identifier = match.group(1)
        next_match = LABEL_RE.search(text, match.end())
        end = next_match.start() if next_match else len(text)
        trailing = text[match.end() : end]
        label_end_col = base_col + end
        out.append(
            {
                "type": "InlineLabel",
                "identifier": identifier,
                **({"text": trailing} if trailing else {}),
                "loc": make_loc(line_no, base_col + match.start(), line_no, label_end_col),
            }
        )
        pos = end


def parse_document(lines: List[str]) -> Dict[str, Any]:
    diagnostics: List[Dict[str, Any]] = []
    idx = 0
    n = len(lines)
    # Locate first non-blank line as header candidate.
    first_non_blank = None
    for i, ln in enumerate(lines):
        if ln.strip():
            first_non_blank = i
            break
    if first_non_blank is None:
        return {
            "type": "Document",
            "header": None,
            "metadata": [],
            "body": [],
            "diagnostics": [
                {
                    "severity": "error",
                    "message": "Empty document",
                    "code": "EMPTY",
                    "loc": {"line": 1, "column": 1},
                }
            ],
        }

    idx = first_non_blank
    header_line = strip_illegal_inline_comment(lines[idx], idx + 1, diagnostics)
    header = parse_header(header_line, idx + 1, diagnostics)
    idx += 1

    metadata: List[Dict[str, Any]] = []
    while idx < n:
        line = lines[idx]
        if not line.strip():
            idx += 1
            break
        m = METADATA_RE.match(line)
        if not m:
            break
        cleaned_line = strip_illegal_inline_comment(line, idx + 1, diagnostics)
        m2 = METADATA_RE.match(cleaned_line)
        if not m2:
            break
        metadata.append(
            {
                "type": "MetadataEntry",
                "key": m2.group(1),
                "value": m2.group(2),
                "loc": make_loc(idx + 1, 1, idx + 1, len(line) + 1),
            }
        )
        idx += 1

    body: List[Dict[str, Any]] = []
    section_stack: List[Dict[str, Any]] = []

    while idx < n:
        line = lines[idx]
        if not line.strip():
            body.append({"type": "BlankLine", "loc": make_loc(idx + 1, 1, idx + 1, len(line) + 1)})
            idx += 1
            continue

        # Fenced code block
        m_fence = FENCE_RE.match(line)
        if m_fence:
            fence_start_line = idx + 1
            fence_indent = len(m_fence.group(1))
            info = m_fence.group(2).strip() or None
            idx += 1
            content: List[str] = []
            closed = False
            closing_line_text = ""
            while idx < n:
                l2 = lines[idx]
                if l2.startswith(" " * fence_indent + "```") and l2.strip() == "```":
                    closed = True
                    closing_line_text = l2
                    idx += 1
                    break
                content.append(l2)
                idx += 1
            end_line_no = fence_start_line + len(content) + (1 if closed else 0)
            end_col = len(closing_line_text) + 1 if closing_line_text else (len(content[-1]) + 1 if content else 1)
            if not closed:
                diagnostics.append(
                    {
                        "severity": "error",
                        "message": "Unterminated fenced code block",
                        "loc": {"line": fence_start_line + len(content), "column": 1},
                        "code": "FENCE_UNTERMINATED",
                    }
                )
            add_block(
                body,
                section_stack,
                {
                    "type": "FencedCodeBlock",
                    "infoString": info,
                    "indent": fence_indent,
                    "content": content,
                    "loc": make_loc(fence_start_line, 1, end_line_no, end_col),
                },
            )
            continue

        # Table block
        if TABLE_RE.match(line):
            rows: List[str] = []
            table_start_line = idx + 1
            while idx < n and TABLE_RE.match(lines[idx]):
                rows.append(lines[idx])
                idx += 1
            table_node = parse_table(rows, diagnostics, table_start_line)
            add_block(body, section_stack, table_node)
            continue

        # Section heading
        cleaned_probe = strip_inline_comment_for_detection(line)
        if SECTION_RE.match(cleaned_probe):
            cleaned_line = strip_illegal_inline_comment(line, idx + 1, diagnostics)
            m_sec = SECTION_RE.match(cleaned_line)
            if m_sec:
                number = [int(x) for x in m_sec.group(1).split(".")]
                title = m_sec.group(2)
                desc = m_sec.group(3)
                sec_node = {
                    "type": "Section",
                    "number": number,
                    "title": title,
                    "body": [],
                    "level": len(number),
                    "loc": make_loc(idx + 1, 1, idx + 1, len(line.rstrip()) + 1),
                }
                if desc:
                    sec_node["description"] = desc
                place_section(body, section_stack, sec_node, diagnostics, idx + 1)
                idx += 1
                continue

        # Whole-line comment
        if COMMENT_RE.match(line):
            add_block(
                body,
                section_stack,
                {"type": "WholeLineComment", "text": line.lstrip()[1:].lstrip(), "loc": make_loc(idx + 1, 1, idx + 1, len(line) + 1)},
            )
            idx += 1
            continue

        # Bullet list
        m_bullet = BULLET_RE.match(line)
        if m_bullet:
            items: List[Dict[str, Any]] = []
            list_start_line = idx + 1
            while idx < n:
                mb = BULLET_RE.match(lines[idx])
                if not mb:
                    break
                indent = len(mb.group(1))
                marker = mb.group(2)
                text = mb.group(3)
                cont_lines: List[str] = []
                lookahead = idx + 1
                base_indent = indent + 2  # marker + space
                while lookahead < n:
                    la_line = lines[lookahead]
                    if not la_line.strip():
                        break
                    if BULLET_RE.match(la_line):
                        break
                    stripped_la = strip_inline_comment_for_detection(la_line)
                    if FENCE_RE.match(la_line) or TABLE_RE.match(la_line) or SECTION_RE.match(stripped_la):
                        break
                    if len(la_line) - len(la_line.lstrip(" ")) >= base_indent:
                        cont_lines.append(la_line.strip())
                        lookahead += 1
                    else:
                        break
                full_text = " ".join([text] + cont_lines)
                inline_nodes = parse_inline(full_text, allow_inline_comment=True, line_no=idx + 1, start_col=indent + 3)
                last_line_idx = lookahead - 1
                items.append(
                    {
                        "type": "BulletItem",
                        "marker": marker,
                        "inline": inline_nodes,
                        **({"continuation": cont_lines} if cont_lines else {}),
                        "loc": make_loc(idx + 1, indent + 1, last_line_idx + 1, len(lines[last_line_idx].rstrip()) + 1),
                    }
                )
                idx = lookahead
            list_end_line = items[-1]["loc"]["end"]["line"] if items else list_start_line
            list_end_col = items[-1]["loc"]["end"]["column"] if items else 1
            add_block(
                body,
                section_stack,
                {
                    "type": "BulletList",
                    "items": items,
                    "loc": make_loc(list_start_line, 1, list_end_line, list_end_col),
                },
            )
            continue

        # Paragraph (default)
        para_start_idx = idx
        para_lines = []
        while idx < n:
            l = lines[idx]
            if not l.strip():
                break
            stripped = strip_inline_comment_for_detection(l)
            if any([FENCE_RE.match(l), TABLE_RE.match(l), SECTION_RE.match(stripped), COMMENT_RE.match(l), BULLET_RE.match(l)]):
                break
            para_lines.append((idx, l))
            idx += 1
        if para_lines:
            text = " ".join([pl[1].strip() for pl in para_lines])
            inline_nodes = parse_inline(text, allow_inline_comment=True, line_no=para_lines[0][0] + 1, start_col=1)
            last_line_idx = para_lines[-1][0]
            add_block(
                body,
                section_stack,
                {
                    "type": "Paragraph",
                    "inline": inline_nodes,
                    "loc": make_loc(para_lines[0][0] + 1, 1, last_line_idx + 1, len(lines[last_line_idx].rstrip()) + 1),
                },
            )
        else:
            idx += 1

    document = {"type": "Document", "header": header, "metadata": metadata, "body": body}
    if diagnostics:
        document["diagnostics"] = diagnostics
    return document


def add_block(body: List[Dict[str, Any]], section_stack: List[Dict[str, Any]], block: Dict[str, Any]) -> None:
    target = section_stack[-1]["body"] if section_stack else body
    target.append(block)


def place_section(
    body: List[Dict[str, Any]],
    section_stack: List[Dict[str, Any]],
    section: Dict[str, Any],
    diagnostics: List[Dict[str, Any]],
    line_no: int,
) -> None:
    # Pop to the appropriate level
    while section_stack and len(section_stack[-1]["number"]) >= len(section["number"]):
        section_stack.pop()

    parent_number = section["number"][:-1]
    parent = None
    if parent_number:
        for candidate in reversed(section_stack):
            if candidate["number"] == parent_number:
                parent = candidate
                break
        if parent is None:
            diagnostics.append(
                {
                    "severity": "warning",
                    "message": f"Missing parent section {'.'.join(map(str, parent_number))}; attached to document root.",
                    "loc": {"line": line_no, "column": 1},
                    "code": "SECTION_PARENT_MISSING",
                }
            )
    target_body = parent["body"] if parent else body
    target_body.append(section)
    section_stack.append(section)


def parse_table(rows: List[str], diagnostics: List[Dict[str, Any]], start_line: int) -> Dict[str, Any]:
    parsed_rows = []
    for idx, row in enumerate(rows):
        if "```" in row:
            diagnostics.append(
                {
                    "severity": "error",
                    "message": "Fenced code block delimiter inside table is not allowed.",
                    "code": "FENCE_IN_TABLE",
                    "loc": {"line": start_line + idx, "column": row.index("```") + 1},
                }
            )
        cells = [cell.strip() for cell in row.strip().split("|")[1:-1]]
        parsed_rows.append({"type": "TableRow", "cells": cells, "loc": make_loc(start_line + idx, 1, start_line + idx, len(row.rstrip()) + 1)})
    header_row = parsed_rows[0] if parsed_rows else {"type": "TableRow", "cells": []}
    align_row = parsed_rows[1] if len(parsed_rows) > 1 else None
    data_rows = parsed_rows[2:] if len(parsed_rows) > 2 else []
    end_line = start_line + len(rows) - 1 if rows else start_line
    end_col = len(rows[-1].rstrip()) + 1 if rows else 1
    table_node: Dict[str, Any] = {"type": "Table", "header": header_row, "rows": data_rows, "loc": make_loc(start_line, 1, end_line, end_col)}
    if align_row:
        table_node["align"] = align_row
    return table_node


def parse_header(line: str, line_no: int, diagnostics: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    m = HEADER_RE.match(line)
    if not m:
        diagnostics.append(
            {
                "severity": "error",
                "message": "Invalid or missing header line",
                "loc": {"line": line_no, "column": 1},
                "code": "HEADER_INVALID",
            }
        )
        return None
    return {"type": "Header", "tag": m.group(1), "text": m.group(2), "loc": make_loc(line_no, 1, line_no, len(line) + 1)}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: parse_px.py <file.xs>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    document = parse_document(lines)
    json.dump(document, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
