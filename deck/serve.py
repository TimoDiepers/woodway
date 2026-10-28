"""Serve the built deck locally, with the speaker notes editable in the page.

    uv run python deck/serve.py            # http://localhost:8765

The deck as built (deck/dist), plus one thing the hosted deck does not have: a save endpoint for the notes. In the
page, E (or "Bearbeiten" in the notes drawer, N) switches to editing: the notes and the texts on the slides become
editable and are saved as you type, straight into the slide sources (deck/src/slides/*.html), with a rebuild; the
change persists and goes into git like any other edit. Cmd+Z undoes as usual (and saves the undone state). Listens on
127.0.0.1 only. The hosted deck is static: no endpoint, so no edit button, and nobody can change anything there.
"""
from __future__ import annotations

import json
import re
import sys
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

DECK = Path(__file__).resolve().parent
sys.path.insert(0, str(DECK))
import build  # noqa: E402

SLIDES = DECK / "src"
LOCK = threading.Lock()
NOTES = re.compile(r'(<aside class="notes"[^>]*>)(.*?)(\n  </aside>)', re.S)


def tidy(html: str) -> str:
    """The editor's HTML as the sources write it: one paragraph per line, indented under the aside."""
    html = re.sub(r"<div>(.*?)</div>", r"<p>\1</p>", html.strip(), flags=re.S)   # a line break typed as <div>
    html = re.sub(r"<br\s*/?>\s*(?=</p>)", "", html)
    paras = [p.strip() for p in re.findall(r"<p[^>]*>.*?</p>", html, re.S)] or [f"<p>{html}</p>"]
    paras = [p for p in paras if re.sub(r"<[^>]+>|&nbsp;|\s", "", p)]   # empty paragraphs go
    return "".join("\n    " + re.sub(r"\s*\n\s*", " ", p) for p in paras)


def save_text(src: str, k: int, old: str, html: str) -> None:   # old: what the text read (text_of)
    """Text k of a slide (edit_targets): replaced, where it still reads *old* (the page's numbering may be a save
    behind: the text at k first, else the one that reads *old*)."""
    from edit_targets import targets, text_of
    path, a, b, text = _section(src)
    sec = text[a:b]
    ts = targets(sec)
    hit = [t for t in ([ts[k]] if k < len(ts) else []) + ts if text_of(sec[t[1]:t[2]]) == text_of(old)]
    if not hit:
        raise ValueError("Text in der Quelle nicht gefunden (inzwischen anders geändert?)")
    _, i, j = hit[0]
    html = re.sub(r"\s*\n\s*", " ", html.strip())
    path.write_text(text[:a] + sec[:i] + html + sec[j:] + text[b:], encoding="utf-8")


def save_formula(src: str, k: int, old: str, tex: str) -> None:
    """Formula k of a slide (edit_targets.formulas), where it still reads *old*: its source replaced by *tex*."""
    import html as H
    from edit_targets import formulas
    path, a, b, text = _section(src)
    sec = text[a:b]
    fs = formulas(sec)
    hit = [f for f in ([fs[k]] if k < len(fs) else []) + fs if H.unescape(sec[f[0]:f[1]]) == old]
    if not hit:
        raise ValueError("Formel in der Quelle nicht gefunden (inzwischen anders geändert?)")
    i, j = hit[0]
    tex = tex.replace("<", "&lt;")   # a < in the source would start a tag
    path.write_text(text[:a] + sec[:i] + tex + sec[j:] + text[b:], encoding="utf-8")


def _section(src: str):
    from edit_targets import sections
    file, k = src.rsplit(":", 1)
    path = (SLIDES / file).resolve()
    if path.parent != (SLIDES / "slides").resolve() or path.suffix != ".html":
        raise ValueError(f"not a slide file: {src}")
    text = path.read_text(encoding="utf-8")
    a, b = sections(text)[int(k)]
    return path, a, b, text


def save_notes(src: str, html: str) -> None:
    path, a, b, text = _section(src)
    section = text[a:b]
    m = NOTES.search(section)
    if not m:
        raise ValueError(f"no notes in {src}")
    section = section[:m.start(2)] + tidy(html) + section[m.end(2):]
    path.write_text(text[:a] + section + text[b:], encoding="utf-8")


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/__notes":   # the page asks whether it may edit
            return self._json(200, {"edit": True})
        return super().do_GET()

    def do_POST(self):
        if self.path != "/__notes":
            return self._json(404, {"error": "not found"})
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            items = body.get("items") or [body]   # several at once, or one: the notes of a slide, or a text on it
            with LOCK:   # one save (and build) at a time
                for it in items:
                    if "tk" in it:
                        save_formula(it["src"], int(it["tk"]), it["old"], it["tex"])
                    elif "e" in it:
                        save_text(it["src"], int(it["e"]), it["old"], it["html"])
                    else:
                        save_notes(it["src"], it["html"])
                build.main()
            self._json(200, {"ok": True, "saved": len(items)})
        except Exception as e:   # noqa: BLE001 - shown in the page
            self._json(400, {"error": str(e)})

    def _json(self, code: int, obj: dict) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):   # quiet, except for saves
        if self.command == "POST":
            super().log_message(fmt, *args)


def main() -> None:
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    build.main()
    server = ThreadingHTTPServer(("127.0.0.1", port), partial(Handler, directory=str(build.DIST)))
    print(f"Deck mit bearbeitbaren Notizen: http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
