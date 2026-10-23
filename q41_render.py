#!/usr/bin/env python3
"""Render the Q41 audit markdown into a standalone HTML page.

Kept separate from the audit itself so the report can be re-rendered without
re-running a 25-minute chain scan. Deliberately a small hand-rolled converter:
the only input is our own report, and pulling in a markdown library to render one
document we wrote ourselves is not worth the dependency.
"""

import re
import sys

CSS = """
body{max-width:60rem;margin:2rem auto;padding:0 1rem;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;color:#1a1a1a}
h1,h2,h3{line-height:1.25;margin-top:2rem}
table{border-collapse:collapse;width:100%;margin:1rem 0;font-size:.86rem;display:block;overflow-x:auto}
th,td{border:1px solid #ddd;padding:.4rem .5rem;text-align:left;vertical-align:top}
th{background:#f6f6f6}
code{background:#f2f2f2;padding:.1em .3em;border-radius:3px;font-size:.9em}
pre{background:#f6f6f6;padding:1rem;overflow-x:auto;border-radius:4px;font-size:.85rem}
a{color:#0b5fff}
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
<style>__CSS__</style></head><body>
__BODY__
</body></html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text: str) -> str:
    """Links, code spans and bold, in that order.

    Applied to paragraph text and to table cells alike. The first version only
    did paragraphs, so every `**KEPT**` and every backticked value in the rule
    table rendered as literal punctuation.

    Code spans are swapped out for placeholders *before* the emphasis regexes
    run. Without that, `(sqrtPriceX96 / 2**96) ** 2` is a code span whose
    contents match the bold pattern, and the published page showed
    `(sqrtPriceX96 / 296) 2` - a corrupted formula on a page whose whole point
    is arithmetic. The structure checks all passed; only reading the rendered
    text caught it.
    """
    codes: list[str] = []

    def stash(m):
        codes.append(m.group(1))
        return "\x00%d\x00" % (len(codes) - 1)

    text = re.sub(r"`([^`]+)`", stash, text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    # Single-asterisk emphasis, after bold so `**x**` is not consumed as two
    # italics. Skipped inside already-emitted tags by requiring a non-space
    # first character, which is enough for the emphasis in this report.
    text = re.sub(r"(?<!\*)\*([^*\s][^*]*?)\*(?!\*)", r"<em>\1</em>", text)
    # Restore code spans last, so nothing inside them was reinterpreted.
    for i, c in enumerate(codes):
        text = text.replace("\x00%d\x00" % i, "<code>%s</code>" % c)
    return text


def render(md: str) -> str:
    out: list[str] = []
    intable = False
    incode = False
    para: list[str] = []
    inlist = False
    li_buf: list[str] = []
    list_tag = "ul"

    def closeli():
        """Emit the pending list item.

        A list item can wrap onto continuation lines, and inline markup can span
        that wrap: the report has a bullet containing "*token\n  contract*". The
        first version emitted each bullet line as its own <li> and pushed the
        continuation into a paragraph, which left the emphasis markers literal.
        """
        if li_buf:
            out.append("<li>%s</li>" % inline(" ".join(x.strip() for x in li_buf)))
            li_buf.clear()

    def closelist():
        nonlocal inlist
        closeli()
        if inlist:
            out.append("</%s>" % list_tag)
            inlist = False

    def flush():
        """Inline formatting is applied per *paragraph*, not per line.

        Doing it per line leaves a bold span that wraps across a newline
        unrendered: the report has "**no scale adjustment\nis applied**", and a
        line-based pass emits a literal `**`. Paragraphs are joined first.
        """
        closelist()
        if not para:
            return
        text = " ".join(x.strip() for x in para)
        out.append("<p>%s</p>" % inline(text))
        para.clear()

    for line in md.split("\n"):
        if line.startswith("```"):
            flush()
            out.append("</pre>" if incode else "<pre>")
            incode = not incode
            continue
        if incode:
            out.append(esc(line))
            continue
        if re.match(r"^\|", line):
            flush()
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if all(re.match(r"^:?-{2,}:?$", c) for c in cells):
                continue
            if not intable:
                out.append("<table>")
                intable = True
                out.append("<tr>" + "".join("<th>%s</th>" % inline(c) for c in cells) + "</tr>")
                continue
            out.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in cells) + "</tr>")
            continue
        if intable:
            flush()
            out.append("</table>")
            intable = False
        if not line.strip():
            flush()
            continue
        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            want = "ul"
            item = bullet.group(1)
        else:
            numbered = re.match(r"^\s*\d+\.\s+(.*)$", line)
            want = "ol" if numbered else None
            item = numbered.group(1) if numbered else None
        if want:
            # Emit any pending paragraph, and the previous item, but do NOT go
            # through flush(): that calls closelist() and would split a run of
            # consecutive items into one list element per item.
            if para:
                out.append("<p>%s</p>" % inline(" ".join(x.strip() for x in para)))
                para.clear()
            closeli()
            if inlist and list_tag != want:
                out.append("</%s>" % list_tag)
                inlist = False
            if not inlist:
                out.append("<%s>" % want)
                inlist = True
                list_tag = want
            li_buf.append(item)
            continue
        # A non-blank line inside a list is a continuation of the current item,
        # unless it is a heading or a table row (both handled below).
        if inlist and not line.lstrip().startswith("#") and not re.match(r"^\|", line):
            li_buf.append(line)
            continue
        h = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h:
            flush()
            n = len(h.group(1))
            out.append("<h%d>%s</h%d>" % (n, h.group(2), n))
            continue
        para.append(line)
    flush()
    if intable:
        out.append("</table>")
    if incode:
        out.append("</pre>")
    return "\n".join(out)


def main() -> int:
    src, dst = sys.argv[1], sys.argv[2]
    title = "FlapJax Receipt Relay Q41 - independent 14-day buyback audit"
    md = open(src).read()
    html = (PAGE.replace("__TITLE__", title)
                .replace("__CSS__", CSS)
                .replace("__BODY__", render(md)))
    open(dst, "w").write(html)
    print("wrote %s (%d bytes)" % (dst, len(html)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
