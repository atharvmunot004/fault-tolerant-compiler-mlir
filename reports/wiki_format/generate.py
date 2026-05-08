#!/usr/bin/env python3
"""
Knowledge Graph → Wikipedia-style HTML Wiki Generator.
Node bodies use the ``latex`` field (LaTeX subset, including ``pycode`` blocks); ``content`` is accepted as a legacy alias.
Usage: python generate.py content.json [output_dir]
"""

import json
import sys
import os
import re
import shutil
import base64
from pathlib import Path
from typing import Optional, Tuple


# ── LaTeX → HTML (minimal subset, no deps; math left for KaTeX auto-render) ───

def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _match_brace_group(s: str, open_at: int) -> Tuple[Optional[str], int]:
    """s[open_at] must be '{'. Returns (inner, index_after_closing) or (None, -1)."""
    if open_at >= len(s) or s[open_at] != "{":
        return None, -1
    depth = 0
    i = open_at
    start = open_at + 1
    while i < len(s):
        if s[i] == "\\":
            i += 2 if i + 1 < len(s) else 1
            continue
        if s[i] == "{":
            depth += 1
        elif s[i] == "}":
            depth -= 1
            if depth == 0:
                return s[start:i], i + 1
        i += 1
    return None, -1


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def protect_math(s: str) -> Tuple[str, list]:
    """Replace math spans with placeholders; return (text_with_placeholders, math_spans)."""
    stored: list[str] = []
    out: list[str] = []
    i, n = 0, len(s)
    while i < n:
        if s.startswith("$$", i):
            j = s.find("$$", i + 2)
            if j == -1:
                out.append(s[i:])
                break
            stored.append(s[i : j + 2])
            out.append(f"\x00MATH{len(stored) - 1}\x00")
            i = j + 2
            continue
        if s.startswith("\\[", i):
            j = s.find("\\]", i + 2)
            if j == -1:
                out.append(s[i:])
                break
            stored.append(s[i : j + 2])
            out.append(f"\x00MATH{len(stored) - 1}\x00")
            i = j + 2
            continue
        if s.startswith("\\(", i):
            j = s.find("\\)", i + 2)
            if j == -1:
                out.append(s[i:])
                break
            stored.append(s[i : j + 2])
            out.append(f"\x00MATH{len(stored) - 1}\x00")
            i = j + 2
            continue
        if s[i] == "$":
            j = s.find("$", i + 1)
            if j == -1:
                out.append(s[i:])
                break
            stored.append(s[i : j + 1])
            out.append(f"\x00MATH{len(stored) - 1}\x00")
            i = j + 1
            continue
        out.append(s[i])
        i += 1
    return "".join(out), stored


def escape_plain_with_links(text: str, nodes: dict) -> str:
    """Escape text and expand wiki links, images, and markdown-style links (in that scan order)."""
    if not text:
        return ""
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        candidates = []
        m_w = re.search(r"\[\[([^\]]+)\]\]", text[i:])
        if m_w:
            candidates.append((m_w.start(), "wiki", m_w))
        m_img = re.search(r"!\[([^\]]*)\]\(([^)]+)\)", text[i:])
        if m_img:
            candidates.append((m_img.start(), "img", m_img))
        m_a = re.search(r"\[([^\]]+)\]\(([^)]+)\)", text[i:])
        if m_a:
            candidates.append((m_a.start(), "md", m_a))
        if not candidates:
            out.append(escape_html(text[i:]))
            break
        pos, kind, m = min(candidates, key=lambda x: x[0])
        pos += i
        out.append(escape_html(text[i:pos]))
        if kind == "wiki":
            inner = m.group(1)
            if "|" in inner:
                nid, lab = inner.split("|", 1)
                nid, lab = nid.strip(), lab.strip()
            else:
                nid = inner.strip()
                lab = nodes.get(nid, {}).get("title", nid)
            out.append(f'<a href="{escape_html(nid)}.html" class="wiki-link">{escape_html(lab)}</a>')
        elif kind == "img":
            out.append(
                f'<img src="{escape_html(m.group(2))}" alt="{escape_html(m.group(1))}" class="inline-img">'
            )
        else:
            out.append(
                f'<a href="{escape_html(m.group(2))}" target="_blank" rel="noopener">{escape_html(m.group(1))}</a>'
            )
        i = pos + len(m.group(0))
    return "".join(out)


def escape_plain_with_links_safe(text: str, nodes: dict) -> str:
    """Like escape_plain_with_links but preserves existing HTML tags in text."""
    if not text:
        return ""
    parts = re.split(r"(<[^>]+>)", text)
    out: list[str] = []
    for p in parts:
        if not p:
            continue
        if p.startswith("<") and p.endswith(">"):
            out.append(p)
        else:
            out.append(escape_plain_with_links(p, nodes))
    return "".join(out)


def _expand_tex_inline(s: str, nodes: dict, math_store: list[str]) -> str:
    """Expand \\textbf, \\textit, \\emph, \\href, \\texttt; recurse; preserve math placeholders."""
    while True:
        candidates = []
        for cmd, tag in (
            ("\\textbf{", "strong"),
            ("\\textit{", "em"),
            ("\\emph{", "em"),
            ("\\texttt{", "code"),
        ):
            p = s.find(cmd)
            if p != -1:
                candidates.append((p, cmd, tag))
        href_p = s.find("\\href{")
        if href_p != -1:
            candidates.append((href_p, "\\href{", "href"))
        if not candidates:
            break
        p, cmd, kind = min(candidates, key=lambda x: x[0])
        if kind == "href":
            br1 = p + len("\\href")
            if br1 >= len(s) or s[br1] != "{":
                s = s[:p] + escape_html(s[p : p + 1]) + s[p + 1 :]
                continue
            url, after_u = _match_brace_group(s, br1)
            if url is None or after_u >= len(s) or s[after_u] != "{":
                s = s[:p] + escape_html(s[p : p + 1]) + s[p + 1 :]
                continue
            link_text, after_t = _match_brace_group(s, after_u)
            if link_text is None:
                s = s[:p] + escape_html(s[p : p + 1]) + s[p + 1 :]
                continue
            inner = _expand_tex_inline(link_text, nodes, math_store)
            repl = f'<a href="{escape_html(url)}" target="_blank" rel="noopener">{inner}</a>'
            s = s[:p] + repl + s[after_t:]
            continue
        open_brace = p + len(cmd) - 1
        inner, end = _match_brace_group(s, open_brace)
        if inner is None:
            s = s[:p] + escape_html(s[p : p + 1]) + s[p + 1 :]
            continue
        expanded_inner = _expand_tex_inline(inner, nodes, math_store)
        if kind == "code":
            repl = f"<code>{expanded_inner}</code>"
        else:
            repl = f"<{kind}>{expanded_inner}</{kind}>"
        s = s[:p] + repl + s[end:]
    return s


def _finalize_segment_html(s: str, nodes: dict, math_store: list[str]) -> str:
    """Escape plain text, wiki/links/images; splice math back in."""
    parts = re.split(r"(\x00MATH\d+\x00)", s)
    out: list[str] = []
    for part in parts:
        mm = re.fullmatch(r"\x00MATH(\d+)\x00", part)
        if mm:
            out.append(math_store[int(mm.group(1))])
        else:
            out.append(escape_plain_with_links_safe(part, nodes))
    return "".join(out)


def _process_mixed_inline(s: str, nodes: dict, math_store: list[str]) -> str:
    return _finalize_segment_html(_expand_tex_inline(s, nodes, math_store), nodes, math_store)


def _process_tabular_block(body: str, nodes: dict, math_store: list[str]) -> str:
    body = body.strip()
    rows_raw = re.split(r"\\\\\s*", body)
    rows: list[list[str]] = []
    for row in rows_raw:
        row = row.strip()
        if not row or row == "\\hline":
            continue
        row = re.sub(r"^\s*\\hline\s*", "", row)
        row = re.sub(r"\s*\\hline\s*$", "", row)
        if not row.strip():
            continue
        cells = [c.strip() for c in row.split("&")]
        rows.append(cells)
    if not rows:
        return ""
    head, *rest = rows
    thead = "<thead><tr>" + "".join(f"<th>{_process_mixed_inline(c, nodes, math_store)}</th>" for c in head) + "</tr></thead>"
    tbody_rows = "".join(
        "<tr>" + "".join(f"<td>{_process_mixed_inline(c, nodes, math_store)}</td>" for c in r) + "</tr>" for r in rest
    )
    return f'<div class="table-wrap"><table>{thead}<tbody>{tbody_rows}</tbody></table></div>'


def _process_pycode_block(body: str) -> str:
    code = body.strip("\n")
    code_html = escape_html(code)
    encoded = base64.b64encode(code.encode("utf-8")).decode("ascii")
    return (
        '<div class="code-runner">'
        f'<pre><code class="lang-python">{code_html}</code></pre>'
        '<div class="code-runner-actions">'
        f'<button type="button" class="run-py-btn" data-code-b64="{encoded}">Run in Browser (Pyodide)</button>'
        "</div>"
        '<pre class="py-output" aria-live="polite"></pre>'
        "</div>"
    )


def _consume_env(s: str, name: str) -> Tuple[Optional[str], str, str]:
    """Find \\begin{name}...\\end{name}; return (inner, before, after) or (None, s, '')."""
    start_tag = f"\\begin{{{name}}}"
    end_tag = f"\\end{{{name}}}"
    i = s.find(start_tag)
    if i == -1:
        return None, s, ""
    j = s.find(end_tag, i + len(start_tag))
    if j == -1:
        return None, s, ""
    inner = s[i + len(start_tag) : j]
    return inner, s[:i], s[j + len(end_tag) :]


def _consume_first_env(s: str, names: list[str]) -> Tuple[Optional[str], Optional[str], str, str]:
    """Return earliest env among names as (name, inner, before, after)."""
    hit_name = None
    hit_idx = -1
    for name in names:
        idx = s.find(f"\\begin{{{name}}}")
        if idx != -1 and (hit_idx == -1 or idx < hit_idx):
            hit_name = name
            hit_idx = idx
    if hit_name is None:
        return None, None, s, ""
    inner, before, after = _consume_env(s, hit_name)
    return hit_name, inner, before, after


def latex_to_html(tex: str, nodes: dict) -> str:
    """Convert a LaTeX subset to HTML; math delimiters preserved for KaTeX."""
    tex = tex.replace("\r\n", "\n").strip()
    tex, math_store = protect_math(tex)
    blocks: list[str] = []

    while True:
        env_name, inner, before, after = _consume_first_env(tex, ["tabular", "pycode"])
        if env_name is None:
            break
        blocks.append(("text", before))
        if env_name == "tabular":
            inner = (inner or "").lstrip()
            if inner.startswith("{"):
                spec, pos = _match_brace_group(inner, 0)
                if spec is not None:
                    inner = inner[pos:].lstrip()
            blocks.append(("tabular", inner))
        elif env_name == "pycode":
            blocks.append(("pycode", inner or ""))
        tex = after
    blocks.append(("text", tex))

    html_parts: list[str] = []
    for kind, chunk in blocks:
        if kind == "tabular":
            html_parts.append(_process_tabular_block(chunk, nodes, math_store))
            continue
        if kind == "pycode":
            html_parts.append(_process_pycode_block(chunk))
            continue
        s = chunk
        while True:
            got_list = None
            for env_name, list_tag in (("itemize", "ul"), ("enumerate", "ol")):
                got = _consume_env(s, env_name)
                if got[0] is not None:
                    got_list = (env_name, list_tag, got)
                    break
            if not got_list:
                break
            _, list_tag, got = got_list
            inner, before, after = got
            if before.strip():
                html_parts.append(_latex_chunk_paragraphs(before, nodes, math_store))
            items = re.split(r"\\item\s*", inner)
            items = [it.strip() for it in items if it.strip()]
            lis = "\n".join(f"  <li>{_process_mixed_inline(it, nodes, math_store)}</li>" for it in items)
            html_parts.append(f"<{list_tag}>\n{lis}\n</{list_tag}>")
            s = after
        if s.strip():
            html_parts.append(_latex_chunk_paragraphs(s, nodes, math_store))

    return "\n\n".join(p for p in html_parts if p.strip())


def _latex_chunk_paragraphs(s: str, nodes: dict, math_store: list[str]) -> str:
    s = s.strip()
    if not s:
        return ""
    out: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        if s.startswith("\\section{", i):
            br = i + len("\\section")
            inner, end = _match_brace_group(s, br)
            if inner is None:
                i += 1
                continue
            title_html = _process_mixed_inline(inner, nodes, math_store)
            hid = _slug(_strip_html_tags(title_html) or "section")
            out.append(f'<h2 id="{escape_html(hid)}">{title_html}</h2>')
            i = end
            continue
        if s.startswith("\\subsection{", i):
            br = i + len("\\subsection")
            inner, end = _match_brace_group(s, br)
            if inner is None:
                i += 1
                continue
            title_html = _process_mixed_inline(inner, nodes, math_store)
            hid = _slug(_strip_html_tags(title_html))
            out.append(f'<h3 id="{escape_html(hid)}">{title_html}</h3>')
            i = end
            continue
        if s.startswith("\\subsubsection{", i):
            br = i + len("\\subsubsection")
            inner, end = _match_brace_group(s, br)
            if inner is None:
                i += 1
                continue
            title_html = _process_mixed_inline(inner, nodes, math_store)
            hid = _slug(_strip_html_tags(title_html))
            out.append(f'<h4 id="{escape_html(hid)}">{title_html}</h4>')
            i = end
            continue
        if s.startswith("\\hrule", i):
            eol = s.find("\n", i)
            if eol == -1:
                out.append("<hr>")
                break
            i = eol + 1
            out.append("<hr>")
            continue
        j = i
        while j < n:
            if s.startswith("\\section{", j) or s.startswith("\\subsection{", j) or s.startswith("\\subsubsection{", j):
                break
            if s.startswith("\\hrule", j):
                break
            j += 1
        para = s[i:j].strip()
        if para:
            if "\n\n" in para:
                for piece in re.split(r"\n\s*\n", para):
                    piece = piece.strip()
                    if piece:
                        out.append(f"<p>{_process_mixed_inline(piece, nodes, math_store)}</p>")
            else:
                out.append(f"<p>{_process_mixed_inline(para, nodes, math_store)}</p>")
        i = j
    return "\n\n".join(out)


def _strip_html_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


# ── CSS / JS Templates ─────────────────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,300;1,400&family=JetBrains+Mono:wght@400;500&family=Outfit:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:        #1f232a;
  --bg2:       #262b33;
  --bg3:       #303641;
  --border:    #465266;
  --accent:    #8ec5ff;
  --accent2:   #b5dbff;
  --accent3:   #9fd3ff;
  --text:      #eef3fb;
  --text-dim:  #c8d6ea;
  --text-faint:#9eaec4;
  --link:      #9ed2ff;
  --link-h:    #d2eaff;
  --nav-h:     56px;
  --max-w:     820px;
  --mono:      'JetBrains Mono', monospace;
  --serif:     'Crimson Pro', Georgia, serif;
  --sans:      'Outfit', system-ui, sans-serif;
}

html { scroll-behavior: smooth; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--serif);
  font-size: 19px;
  line-height: 1.75;
  min-height: 100vh;
}

/* ── NAV ── */
nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 100;
  height: var(--nav-h);
  background: rgba(13,15,20,0.88);
  backdrop-filter: blur(14px);
  border-bottom: 1px solid var(--border);
  display: flex; align-items: center;
  padding: 0 24px; gap: 12px;
}

.nav-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 7px 16px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text-dim);
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.18s;
  letter-spacing: 0.02em;
}
.nav-btn:hover {
  color: var(--accent);
  border-color: var(--accent);
  background: rgba(126,184,247,0.08);
}
.nav-btn svg { width: 14px; height: 14px; }

.nav-breadcrumb {
  flex: 1;
  font-family: var(--sans);
  font-size: 13px;
  color: var(--text-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nav-breadcrumb .crumb { color: var(--text-dim); }
.nav-breadcrumb .sep { margin: 0 6px; }
.nav-breadcrumb .current { color: var(--text); }

.nav-title {
  font-family: var(--sans);
  font-size: 13px;
  font-weight: 600;
  color: var(--accent);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  text-decoration: none;
}

/* ── LAYOUT ── */
main {
  max-width: var(--max-w);
  margin: 0 auto;
  padding: calc(var(--nav-h) + 52px) 32px 80px;
}

/* ── ARTICLE HEADER ── */
.page-header {
  margin-bottom: 40px;
  padding-bottom: 28px;
  border-bottom: 1px solid var(--border);
}
.page-header h1 {
  font-family: var(--serif);
  font-size: 2.6rem;
  font-weight: 300;
  color: #edf2ff;
  line-height: 1.2;
  margin-bottom: 12px;
  letter-spacing: -0.01em;
}
.page-tags {
  display: flex; gap: 8px; flex-wrap: wrap;
}
.tag {
  font-family: var(--sans);
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 3px 10px;
  border-radius: 4px;
  background: var(--bg3);
  border: 1px solid var(--border);
  color: var(--text-dim);
}

/* ── ARTICLE CONTENT ── */
.content h1, .content h2, .content h3, .content h4 {
  font-family: var(--serif);
  font-weight: 400;
  color: #d9e8fb;
  margin: 1.8em 0 0.6em;
  line-height: 1.25;
}
.content h1 { font-size: 2rem; display: none; }  /* title already in header */
.content h2 { font-size: 1.55rem; border-bottom: 1px solid var(--border); padding-bottom: 6px; }
.content h3 { font-size: 1.25rem; }
.content h4 { font-size: 1.05rem; font-weight: 600; font-family: var(--sans); color: var(--text-dim); letter-spacing: 0.03em; text-transform: uppercase; font-size: 0.85rem; }

.content p { margin: 0.9em 0; }

.content a.wiki-link {
  color: var(--link);
  text-decoration: underline;
  text-decoration-color: rgba(126,184,247,0.35);
  text-underline-offset: 3px;
  transition: all 0.15s;
}
.content a.wiki-link:hover {
  color: var(--link-h);
  text-decoration-color: var(--link-h);
}
.content a {
  color: var(--accent3);
  text-decoration: underline;
  text-decoration-color: rgba(52,211,153,0.3);
  text-underline-offset: 3px;
}
.content a:hover { color: #6ee7b7; }

.content strong { font-weight: 600; color: #e8eeff; }
.content em { font-style: italic; color: #d3e3f8; }

.content code {
  font-family: var(--mono);
  font-size: 0.78em;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  color: #c8e3ff;
}

.content pre {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 20px 24px;
  overflow-x: auto;
  margin: 1.4em 0;
}
.content pre code {
  background: none;
  border: none;
  padding: 0;
  font-size: 0.85em;
  color: #d8e9ff;
}

.code-runner { margin: 1.4em 0; }
.code-runner-actions { margin-top: -6px; margin-bottom: 10px; }
.run-py-btn {
  display: inline-flex; align-items: center;
  padding: 7px 12px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 12px;
  cursor: pointer;
}
.run-py-btn:hover { border-color: var(--accent); color: var(--accent); }
.run-py-btn:disabled { opacity: 0.6; cursor: wait; }
.py-output {
  min-height: 44px;
  white-space: pre-wrap;
  background: #0b111a;
  color: #c4f5d1;
}

.content ul, .content ol {
  padding-left: 1.6em;
  margin: 0.8em 0;
}
.content li { margin: 0.3em 0; }

.content hr {
  border: none;
  border-top: 1px solid var(--border);
  margin: 2em 0;
}

.content blockquote {
  border-left: 3px solid var(--accent2);
  padding: 2px 0 2px 20px;
  margin: 1.2em 0;
  color: var(--text-dim);
  font-style: italic;
}

/* ── TABLE ── */
.content .table-wrap {
  overflow-x: auto;
  margin: 1.4em 0;
}
.content table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
  font-family: var(--sans);
}
.content th {
  background: var(--bg3);
  color: var(--accent);
  font-weight: 600;
  text-align: left;
  padding: 10px 16px;
  border: 1px solid var(--border);
  font-size: 0.8em;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.content td {
  padding: 9px 16px;
  border: 1px solid var(--border);
  color: var(--text);
}
.content tr:nth-child(even) td { background: rgba(142,197,255,0.1); }

/* ── IMAGES ── */
.content img, .content .inline-img {
  max-width: 100%;
  border-radius: 10px;
  border: 1px solid var(--border);
  margin: 1.2em 0;
  display: block;
}

/* ── MATH ── */
.math-display {
  overflow-x: auto;
  padding: 16px 0;
  text-align: center;
}

/* ── RELATED NODES SIDEBAR SECTION ── */
.related-section {
  margin-top: 52px;
  padding-top: 28px;
  border-top: 1px solid var(--border);
}
.related-section h3 {
  font-family: var(--sans);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-faint);
  margin-bottom: 16px;
}
.related-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}
.related-card {
  display: block;
  padding: 14px 18px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.18s;
  position: relative;
  overflow: hidden;
}
.related-card::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 3px;
  background: var(--accent);
  transform: scaleY(0);
  transition: transform 0.18s;
  transform-origin: center;
}
.related-card:hover { border-color: var(--accent); background: rgba(126,184,247,0.05); }
.related-card:hover::before { transform: scaleY(1); }
.related-card .rc-title {
  font-family: var(--sans);
  font-size: 14px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 4px;
  transition: color 0.18s;
}
.related-card:hover .rc-title { color: var(--accent); }
.related-card .rc-arrow {
  font-size: 12px;
  color: var(--text-faint);
  font-family: var(--mono);
}

/* ── SEARCH ── */
.search-wrap {
  margin-left: auto;
  position: relative;
}
#search-input {
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 13px;
  padding: 6px 14px 6px 34px;
  width: 180px;
  outline: none;
  transition: all 0.2s;
}
#search-input:focus {
  border-color: var(--accent);
  width: 240px;
  background: var(--bg2);
}
.search-icon {
  position: absolute; left: 10px; top: 50%; transform: translateY(-50%);
  color: var(--text-faint); pointer-events: none;
}
#search-results {
  position: absolute; top: calc(100% + 8px); right: 0;
  width: 280px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  display: none;
  z-index: 200;
  overflow: hidden;
}
#search-results.visible { display: block; }
.sr-item {
  display: block;
  padding: 12px 16px;
  text-decoration: none;
  border-bottom: 1px solid var(--border);
  transition: background 0.15s;
}
.sr-item:last-child { border-bottom: none; }
.sr-item:hover { background: var(--bg3); }
.sr-item-title { font-family: var(--sans); font-size: 14px; color: var(--text); }
.sr-item-tags { font-size: 11px; color: var(--text-faint); font-family: var(--mono); }

/* ── SCROLL TO TOP ── */
#scroll-top {
  position: fixed; bottom: 32px; right: 32px;
  width: 40px; height: 40px;
  background: var(--bg3);
  border: 1px solid var(--border);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  opacity: 0; pointer-events: none;
  transition: all 0.2s;
  color: var(--text-dim);
  text-decoration: none;
  font-size: 18px;
}
#scroll-top.visible { opacity: 1; pointer-events: all; }
#scroll-top:hover { border-color: var(--accent); color: var(--accent); }

/* ── FADE IN ── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}
main { animation: fadeUp 0.45s ease both; }
"""

JS_TEMPLATE = """
// Search
const INDEX = {index_json};
let pyodideReady = null;

function escapePyForExec(src) {
  const normalized = src.replaceAll(String.fromCharCode(13), '');
  const indented = normalized.split('\\n').map(line => `        ${line}`).join('\\n');
  return `import io, contextlib, traceback
__wiki_buf = io.StringIO()
with contextlib.redirect_stdout(__wiki_buf), contextlib.redirect_stderr(__wiki_buf):
    try:
${indented}
    except Exception:
        traceback.print_exc()
__wiki_out = __wiki_buf.getvalue()
`;
}

async function ensurePyodide() {
  if (pyodideReady) return pyodideReady;
  pyodideReady = (async () => {
    if (!window.loadPyodide) {
      await new Promise((resolve, reject) => {
        const s = document.createElement('script');
        s.src = 'https://cdn.jsdelivr.net/pyodide/v0.27.2/full/pyodide.js';
        s.onload = resolve;
        s.onerror = () => reject(new Error('Failed to load pyodide.js'));
        document.head.appendChild(s);
      });
    }
    const py = await window.loadPyodide();
    return py;
  })();
  return pyodideReady;
}

const input = document.getElementById('search-input');
const results = document.getElementById('search-results');

if (input) {
  input.addEventListener('input', () => {
    const q = input.value.trim().toLowerCase();
    if (!q) { results.classList.remove('visible'); return; }
    const hits = INDEX.filter(n =>
      n.title.toLowerCase().includes(q) ||
      (n.tags || []).some(t => t.includes(q))
    ).slice(0, 6);
    if (!hits.length) { results.classList.remove('visible'); return; }
    results.innerHTML = hits.map(n =>
      `<a class="sr-item" href="${n.id}.html">
        <div class="sr-item-title">${n.title}</div>
        <div class="sr-item-tags">${(n.tags||[]).join(' · ')}</div>
      </a>`
    ).join('');
    results.classList.add('visible');
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) results.classList.remove('visible');
  });
}

// Scroll-to-top
const scrollBtn = document.getElementById('scroll-top');
if (scrollBtn) {
  window.addEventListener('scroll', () => {
    scrollBtn.classList.toggle('visible', window.scrollY > 300);
  });
}

// Back: history is unreliable for file:// and some redirects; prefer real back then home
const backBtn = document.getElementById('back-btn');
if (backBtn) {
  backBtn.type = 'button';
  backBtn.addEventListener('click', () => {
    const ref = document.referrer;
    let sameOrigin = false;
    try {
      if (ref) sameOrigin = new URL(ref).origin === window.location.origin;
    } catch (e) {}
    if (ref && sameOrigin && ref !== window.location.href) {
      window.history.back();
    } else {
      window.location.href = 'index.html';
    }
  });
}

// Pyodide runner
document.querySelectorAll('.run-py-btn').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const host = btn.closest('.code-runner');
    const out = host ? host.querySelector('.py-output') : null;
    if (!out) return;
    const code = atob(btn.dataset.codeB64 || '');
    btn.disabled = true;
    out.textContent = 'Running in browser Python...';
    try {
      const py = await ensurePyodide();
      await py.runPythonAsync(escapePyForExec(code));
      const pyOutObj = py.globals.get('__wiki_out');
      const pyOut = pyOutObj ? pyOutObj.toString() : '';
      if (pyOutObj && typeof pyOutObj.destroy === 'function') pyOutObj.destroy();
      out.textContent = pyOut || '(no output)';
    } catch (err) {
      out.textContent = `Error: ${err && err.message ? err.message : String(err)}`;
    } finally {
      btn.disabled = false;
    }
  });
});
"""

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — {site_title}</title>
  <link rel="stylesheet" href="style.css">
  <!-- KaTeX for math rendering -->
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{delimiters: [
      {{left:'$$',right:'$$',display:true}},
      {{left:'\\\\[',right:'\\\\]',display:true}},
      {{left:'\\\\(',right:'\\\\)',display:false}},
      {{left:'$',right:'$',display:false}}
    ]}});"></script>
</head>
<body>

<nav>
  <a href="index.html" class="nav-title">{site_title}</a>
  {back_btn}
  <div class="nav-breadcrumb">
    {breadcrumb}
  </div>
  <div class="search-wrap">
    <svg class="search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
    <input type="text" id="search-input" placeholder="Search nodes…" autocomplete="off">
    <div id="search-results"></div>
  </div>
</nav>

<main>
  <header class="page-header">
    <h1>{title}</h1>
    {tags_html}
  </header>

  <article class="content">
    {content_html}
  </article>

  {related_html}
</main>

<a href="#" id="scroll-top" aria-label="Scroll to top">↑</a>

<script>
{js}
</script>
</body>
</html>
"""


# ── Build ──────────────────────────────────────────────────────────────────────

def build_tags_html(tags: list) -> str:
    if not tags:
        return ""
    tag_els = "".join(f'<span class="tag">{t}</span>' for t in tags)
    return f'<div class="page-tags">{tag_els}</div>'


def build_related_html(node_id: str, data: dict) -> str:
    nodes = data["nodes"]
    edges = data.get("edges", [])
    related = set()
    for e in edges:
        if e["from"] == node_id:
            related.add(e["to"])
        elif e["to"] == node_id:
            related.add(e["from"])

    if not related:
        return ""

    cards = ""
    for rid in sorted(related):
        if rid not in nodes:
            continue
        rtitle = nodes[rid].get("title", rid)
        cards += f"""
        <a href="{rid}.html" class="related-card">
          <div class="rc-title">{rtitle}</div>
          <div class="rc-arrow">→</div>
        </a>"""

    return f"""
  <section class="related-section">
    <h3>Connected Nodes</h3>
    <div class="related-grid">{cards}
    </div>
  </section>"""


def build_search_index(data: dict) -> str:
    index = []
    for nid, node in data["nodes"].items():
        index.append({
            "id": nid,
            "title": node.get("title", nid),
            "tags": node.get("tags", [])
        })
    return json.dumps(index)


def generate(json_path: str, out_dir: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data.get("meta", {})
    site_title = meta.get("title", "Knowledge Graph")
    root_id = data.get("root", next(iter(data["nodes"])))
    nodes = data["nodes"]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # Write CSS
    (out / "style.css").write_text(CSS, encoding="utf-8")

    # Copy images dir if exists
    json_dir = Path(json_path).parent
    img_dir = json_dir / "images"
    if img_dir.exists():
        shutil.copytree(img_dir, out / "images", dirs_exist_ok=True)

    search_index = build_search_index(data)
    js = JS_TEMPLATE.replace("{index_json}", search_index)

    # Generate each node page
    for node_id, node in nodes.items():
        title = node.get("title", node_id)
        latex = node.get("latex", node.get("content", ""))
        tags = node.get("tags", [])

        content_html = latex_to_html(latex, nodes)
        tags_html = build_tags_html(tags)
        related_html = build_related_html(node_id, data)

        is_root = node_id == root_id
        back_btn = '' if is_root else '<button type="button" id="back-btn" class="nav-btn"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg> Back</button>'

        if is_root:
            breadcrumb = f'<span class="current">{title}</span>'
        else:
            root_title = nodes.get(root_id, {}).get("title", "Home")
            breadcrumb = f'<a href="index.html" class="crumb">{root_title}</a><span class="sep">/</span><span class="current">{title}</span>'

        page = PAGE_TEMPLATE.format(
            title=title,
            site_title=site_title,
            back_btn=back_btn,
            breadcrumb=breadcrumb,
            tags_html=tags_html,
            content_html=content_html,
            related_html=related_html,
            js=js,
        )

        fname = "index.html" if node_id == root_id else f"{node_id}.html"
        (out / fname).write_text(page, encoding="utf-8")
        print(f"  ok {fname}")

    print(f"\nBuilt {len(nodes)} pages -> {out_dir}/")
    print(f"   Open: {out_dir}/index.html")


# ── Entry Point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate.py content.json [output_dir]")
        sys.exit(1)

    json_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "wiki_output"

    if not os.path.exists(json_file):
        print(f"Error: {json_file} not found")
        sys.exit(1)

    print(f"\nGenerating wiki from {json_file}...\n")
    generate(json_file, output_dir)
