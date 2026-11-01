#!/usr/bin/env python3
"""Serve the site with a local text editor: python3 scripts/local_preview.py.

The editor is injected into responses; it is never added to the published HTML.
Saves patch source ranges, preserve other code, and keep backups in /tmp.
"""

import argparse
import ast
import hashlib
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import secrets
import tempfile
import threading
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
BLOCKS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "figcaption"}


def revision(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class HTMLFields(HTMLParser):
    """Locate editable inner HTML without reserialising the document."""

    def __init__(self, source):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.lines = [0] + [m.end() for m in re.finditer("\n", source)]
        self.stack = []
        self.fields = {}
        self.block_count = 0
        self.feed(source)

    def source_offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        attrs = dict(attrs)
        parents = [item["tag"] for item in self.stack]
        editable = (
            tag in BLOCKS and "body" in parents
            and not any(t in parents for t in ("nav", "script", "style"))
            and "post-meta" not in attrs.get("class", "").split()
        )
        if editable:
            for item in self.stack:
                item["has_block"] = True
        start = self.source_offset() + len(self.get_starttag_text())
        key = f"html-{self.block_count}"
        if tag in BLOCKS:
            self.block_count += 1
        self.stack.append({"tag": tag, "id": key, "start": start, "editable": editable, "has_block": False})

    def handle_startendtag(self, tag, attrs):
        if tag not in VOID:
            self.handle_starttag(tag, attrs)
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]["tag"] != tag:
            return
        item = self.stack.pop()
        end = self.source_offset()
        value = self.source[item["start"]:end]
        # Do not save MathJax's rendered output or complex embedded content.
        if (item["editable"] and not item["has_block"]
                and not re.search(r"<\s*(?:img|svg|math|video|table)\b|\$[^$]+\$|\\\(", value)):
            self.fields[item["id"]] = {
                "start": item["start"], "end": end, "value": value,
            }


# Parse the data object only; never execute JavaScript received from the browser.
TOKEN = re.compile(r'''\s+|//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_$][\w$]*|[{}\[\]:,]''')


def content_fields(source):
    start = re.search(r"\bconst\s+siteContent\s*=\s*", source)
    if not start:
        raise ValueError("Cannot find siteContent in content.js")
    pos = start.end()
    fields = {}

    def token():
        nonlocal pos
        while True:
            match = TOKEN.match(source, pos)
            if not match:
                raise ValueError("Unsupported content.js syntax")
            pos = match.end()
            value = match.group()
            if not (value.isspace() or value.startswith(("//", "/*"))):
                return value, match.start(), match.end()

    def parse(path, first=None):
        value, begin, end = first or token()
        if value in ("{", "["):
            is_object = value == "{"
            close = "}" if is_object else "]"
            result = {} if is_object else []
            entry = token()
            while entry[0] != close:
                key = entry[0] if is_object else str(len(result))
                if is_object:
                    if key.startswith(('"', "'")):
                        key = ast.literal_eval(key)
                    if token()[0] != ":":
                        raise ValueError("Invalid content.js property")
                    entry = token()
                parsed = parse(f"{path}.{key}" if path else key, entry)
                if is_object:
                    result[key] = parsed
                else:
                    result.append(parsed)
                entry = token()
                if entry[0] == close:
                    break
                if entry[0] != ",":
                    raise ValueError("Invalid content.js separator")
                entry = token()
            return result
        if value.startswith(('"', "'")):
            decoded = ast.literal_eval(value)
            fields[path] = {"start": begin, "end": end, "value": decoded}
            return decoded
        raise ValueError("The local editor supports string content only")

    data = parse("")
    return data, fields


class InlineHTML(HTMLParser):
    """Allow text and ordinary inline formatting, never executable markup."""

    allowed = {"a", "em", "strong", "b", "i", "br", "code", "sub", "sup", "span"}

    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.allowed:
            raise ValueError("Only text, links and inline formatting can be saved")
        for key, value in attrs:
            if key not in {"href", "target", "rel", "title"} or (tag != "a" and key != "title"):
                raise ValueError("Unsupported formatting; paste plain text")
            if key == "href":
                if any(ord(char) < 32 for char in value) or urlsplit(value.strip()).scheme.lower() not in {"", "http", "https", "mailto"}:
                    raise ValueError("Unsupported link URL")
        if tag != "br":
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag != "br":
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack.pop() != tag:
            raise ValueError("Unbalanced inline formatting")

    def handle_comment(self, data):
        raise ValueError("Comments cannot be inserted through the text editor")

    def handle_decl(self, data):
        raise ValueError("Document declarations cannot be inserted")


def validate_inline(value):
    parser = InlineHTML()
    parser.feed(value)
    parser.close()
    if parser.stack:
        raise ValueError("Unclosed inline formatting")


def patch_source(source, fields, edits, content=False):
    replacements = []
    seen = set()
    for edit in edits:
        key, value = edit["id"], edit["value"]
        if key not in fields or key in seen or not isinstance(value, str) or len(value) > 100_000:
            raise ValueError("Invalid or duplicate edit")
        seen.add(key)
        field = fields[key]
        if content:
            # These are the only data fields rendered as HTML intentionally.
            if key in {"personal.currentPosition", "personal.researchFocus"}:
                validate_inline(value)
            elif "<" in value or ">" in value:
                raise ValueError("Please use plain text in this field")
            if key.startswith("social.") or key.endswith((".link", ".date")):
                raise ValueError("This field is not editable on the page")
            replacement = json.dumps(value, ensure_ascii=False)
        else:
            validate_inline(value)
            original = field["value"]
            leading = re.match(r"\s*", original).group()
            trailing = re.search(r"\s*$", original).group() if original.strip() else ""
            replacement = leading + value.strip() + trailing
        replacements.append((field["start"], field["end"], replacement))
    for begin, end, value in sorted(replacements, reverse=True):
        source = source[:begin] + value + source[end:]
    return source


class EditorServer(ThreadingHTTPServer):
    def __init__(self, address, root=ROOT):
        self.root = Path(root).resolve()
        self.token = secrets.token_urlsafe(32)
        self.write_lock = threading.Lock()
        self.backups = Path(tempfile.mkdtemp(prefix="ben-website-backups-"))
        super().__init__(address, EditorHandler)


class EditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(args[2].root), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def reply(self, status, body, mime="application/json; charset=utf-8"):
        payload = json.dumps(body).encode() if isinstance(body, dict) else body
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(payload)

    def local_host(self):
        return self.headers.get("Host") in {
            f"localhost:{self.server.server_port}", f"127.0.0.1:{self.server.server_port}",
        }

    def site_path(self, name):
        path = (self.server.root / name.lstrip("/")).resolve()
        if not path.is_relative_to(self.server.root) or any(part.startswith(".") for part in path.relative_to(self.server.root).parts):
            raise ValueError("Invalid website path")
        return path

    def do_GET(self):
        if not self.local_host():
            return self.reply(403, {"error": "Use localhost to open the editor"})
        name = unquote(urlsplit(self.path).path)
        if name == "/__local-editor/editor.js":
            return self.reply(200, Path(__file__).with_name("local_editor.js").read_bytes(), "text/javascript; charset=utf-8")
        try:
            path = self.site_path(name)
            if path.is_dir():
                path /= "index.html"
            if not path.is_file():
                return self.reply(404, {"error": "Page not found"})
            if path.suffix != ".html":
                return super().do_HEAD() if self.command == "HEAD" else super().do_GET()
            source = path.read_text(encoding="utf-8")
            fields = HTMLFields(source).fields
            config = {"token": self.server.token, "file": str(path.relative_to(self.server.root)), "revision": revision(source)}
            if path == self.server.root / "index.html":
                content = (self.server.root / "content.js").read_text(encoding="utf-8")
                data, _ = content_fields(content)
                config["content"] = {"data": data, "revision": revision(content)}
            for key, field in sorted(fields.items(), key=lambda pair: pair[1]["start"], reverse=True):
                pos = field["start"] - 1
                source = source[:pos] + f' data-local-field="{key}"' + source[pos:]
            config_json = json.dumps(config, ensure_ascii=False).replace("<", "\\u003c")
            injected = f'<script id="local-editor-config" type="application/json">{config_json}</script><script src="/__local-editor/editor.js"></script>'
            source = source.replace("</body>", injected + "\n</body>")
            self.reply(200, source.encode("utf-8"), "text/html; charset=utf-8")
        except (ValueError, OSError) as exc:
            self.reply(400, {"error": str(exc)})

    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        if (not self.local_host() or self.path != "/__local-editor/save"
                or self.headers.get("X-Local-Editor") != self.server.token
                or self.headers.get("Origin") != f"http://{self.headers.get('Host')}"
                or self.headers.get("Content-Type") != "application/json"):
            return self.reply(403, {"error": "Open the local preview to save changes"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 1_000_000:
                raise ValueError("Invalid save size")
            body = json.loads(self.rfile.read(length))
            path = self.site_path(body["file"])
            is_content = path == self.server.root / "content.js"
            if not is_content and path.suffix != ".html":
                raise ValueError("Only website text files can be edited")
            with self.server.write_lock:
                source = path.read_text(encoding="utf-8")
                if body["revision"] != revision(source):
                    return self.reply(409, {"error": "This file changed since you opened it. Copy your edits, then refresh before saving."})
                fields = content_fields(source)[1] if is_content else HTMLFields(source).fields
                updated = patch_source(source, fields, body["edits"], is_content)
                # Keep the original and replace atomically, including on save failures.
                backup = self.server.backups / f"{secrets.token_hex(8)}-{path.name}"
                backup.write_text(source, encoding="utf-8")
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
                    temp = Path(handle.name)
                    handle.write(updated)
                try:
                    temp.chmod(path.stat().st_mode)
                    temp.replace(path)
                finally:
                    temp.unlink(missing_ok=True)
            self.reply(200, {"revision": revision(updated), "file": body["file"]})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            self.reply(400, {"error": str(exc)})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--directory", type=Path, default=ROOT)
    args = parser.parse_args()
    server = EditorServer(("127.0.0.1", args.port), args.directory)
    print(f"Local editor: http://localhost:{server.server_port}/", flush=True)
    print(f"Backups: {server.backups}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
