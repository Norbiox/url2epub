import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import httpx
import trafilatura
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse
from readability import Document
from starlette.background import BackgroundTask

# Optional: when unset, the service is unauthenticated (fine inside a private docker network).
TOKEN = os.environ.get("API_TOKEN") or None
DEFAULT_LANG = os.environ.get("DEFAULT_LANG", "en")
USER_AGENT = os.environ.get(
    "USER_AGENT",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
)

app = FastAPI(title="url2epub")


def slugify(text: str, max_len: int = 80) -> str:
    text = unicodedata.normalize("NFKD", text.translate(str.maketrans("łŁøØđĐß", "lLoOdDs")))
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^\w\s-]", "", text).strip()
    return re.sub(r"[\s_-]+", "-", text)[:max_len].strip("-") or "article"


def html_to_epub(html: str, url: str, out_dir: Path) -> Path:
    meta = trafilatura.extract_metadata(html, default_url=url)
    doc = Document(html, url=url)  # url= makes links and images absolute
    title = (meta.title if meta and meta.title else None) or doc.short_title() or url
    author = meta.author if meta and meta.author else (meta.sitename if meta else None)
    lang_m = re.search(r"<html[^>]*\slang=[\"']?([\w-]+)", html[:5000], re.I)
    lang = lang_m.group(1) if lang_m else DEFAULT_LANG

    body = doc.summary(html_partial=True) + f'\n<p>Źródło: <a href="{url}">{url}</a></p>'
    src = out_dir / "article.html"
    src.write_text(body, encoding="utf-8")
    out = out_dir / f"{slugify(title)}.epub"

    cmd = [
        "pandoc", str(src), "-f", "html", "-t", "epub3", "-o", str(out),
        "--metadata", f"title={title}", "--metadata", f"lang={lang}",
        "--epub-title-page=false", "--split-level=1",
        "--request-header", f"User-Agent:{USER_AGENT}",
    ]
    if author:
        cmd += ["--metadata", f"author={author}"]
    if meta and meta.date:
        cmd += ["--metadata", f"date={meta.date}"]
    subprocess.run(cmd, check=True, capture_output=True, timeout=120)
    return out


def fetch(url: str) -> str:
    try:
        r = httpx.get(url, headers={"User-Agent": USER_AGENT}, follow_redirects=True, timeout=30)
        r.raise_for_status()
    except httpx.HTTPError as e:
        raise HTTPException(502, f"fetch failed: {e}")
    return r.text


def extract_url(text: str) -> str:
    # Share sheets often send "Title https://..." instead of a bare URL.
    m = re.search(r"https?://\S+", text or "")
    if not m:
        raise HTTPException(400, "no URL found")
    return m.group(0)


@app.get("/epub")
def epub(url: str, token: str | None = Query(None), x_token: str | None = Header(None)):
    if TOKEN and (x_token or token) != TOKEN:
        raise HTTPException(401, "bad token")
    url = extract_url(url)
    tmp = tempfile.TemporaryDirectory()
    try:
        path = html_to_epub(fetch(url), url, Path(tmp.name))
    except subprocess.CalledProcessError as e:
        tmp.cleanup()
        raise HTTPException(500, f"pandoc failed: {e.stderr.decode(errors='replace')[-500:]}")
    except Exception:
        tmp.cleanup()
        raise
    return FileResponse(path, media_type="application/epub+zip", filename=path.name,
                        background=BackgroundTask(tmp.cleanup))


@app.get("/health", response_class=PlainTextResponse)
def health():
    return "ok"
