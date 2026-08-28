"""image search providers, plus the download/decode side

both providers are keyless. duckduckgo gives whole-web results, openverse is the
CC-licensed fallback for when ddg starts rate limiting us
"""

import io
import re
import threading
from urllib.parse import urlparse

import requests
from PIL import Image

TIMEOUT = 12
MAX_BYTES = 25 * 1024 * 1024

# a lot of hosts throw a fit if the request doesnt look like a browser
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

PROVIDER_LABELS = {
    "auto": "Auto",
    "duckduckgo": "DuckDuckGo",
    "openverse": "Openverse",
}
PROVIDER_HINTS = {
    "auto": "DuckDuckGo, then Openverse if it rate-limits. Recommended.",
    "duckduckgo": "Whole-web image results. Unofficial endpoint.",
    "openverse": "Openly licensed images only. Slower, always available.",
}


class SearchError(Exception):
    """anything that stops us getting an image, message is meant to be shown to the user"""


# --------------------------------------------------------------- DuckDuckGo

_DDG_ENDPOINT = "https://duckduckgo.com/i.js"
_DDG_SIZES = {
    "icon": "size:Small",
    "small": "size:Small",
    "medium": "size:Medium",
    "large": "size:Large",
    "xlarge": "size:Large",
    "huge": "size:Wallpaper",
}
_ddg_lock = threading.Lock()
_ddg_session: requests.Session | None = None


def _ddg_get_session() -> requests.Session:
    global _ddg_session
    with _ddg_lock:
        if _ddg_session is None:
            session = requests.Session()
            session.headers.update({
                "User-Agent": UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            })
            _ddg_session = session
        return _ddg_session


def _ddg_token(session: requests.Session, query: str) -> str:
    """ddg signs every image request with a per-query vqd token, gotta scrape it first"""
    resp = session.get(
        "https://duckduckgo.com/",
        params={"q": query, "iax": "images", "ia": "images"},
        timeout=TIMEOUT,
    )
    match = re.search(r"vqd=[\"']?([\w-]+)", resp.text)
    if not match:
        raise SearchError("DuckDuckGo did not return a search token.")
    return match.group(1)


def _search_duckduckgo(query, size, safe, count):
    session = _ddg_get_session()
    try:
        vqd = _ddg_token(session, query)
        resp = session.get(
            _DDG_ENDPOINT,
            params={
                "l": "us-en",
                "o": "json",
                "q": query,
                "vqd": vqd,
                "f": f",,,{_DDG_SIZES.get(size, '')},",
                "p": "1" if safe in ("medium", "high") else "-1",
            },
            headers={
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Referer": "https://duckduckgo.com/",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise SearchError(f"DuckDuckGo network error: {exc}") from exc

    if resp.status_code == 403:
        raise SearchError("DuckDuckGo refused the request (rate limited).")
    if resp.status_code != 200:
        raise SearchError(f"DuckDuckGo returned HTTP {resp.status_code}.")

    try:
        items = resp.json().get("results") or []
    except ValueError as exc:
        raise SearchError("DuckDuckGo returned a malformed response.") from exc

    return [
        {"url": item.get("image", ""), "thumbnail": item.get("thumbnail", "")}
        for item in items[:count]
        if item.get("image")
    ]


# ----------------------------------------------------------------- Openverse

_OPENVERSE_ENDPOINT = "https://api.openverse.org/v1/images/"
_OPENVERSE_SIZES = {
    "icon": "small",
    "small": "small",
    "medium": "medium",
    "large": "large",
    "xlarge": "large",
    "huge": "large",
}


def _search_openverse(query, size, safe, count):
    # wikimedia is rate limiting openverse's fetchers right now (429 direct, 424 through
    # their thumbnail proxy) so those results are just dead weight for us
    params = {
        "q": query,
        "page_size": max(1, min(count, 20)),
        "excluded_source": "wikimedia",
    }
    if size in _OPENVERSE_SIZES:
        params["size"] = _OPENVERSE_SIZES[size]
    if safe in ("medium", "high"):
        params["mature"] = "false"

    try:
        resp = requests.get(
            _OPENVERSE_ENDPOINT,
            params=params,
            headers={"User-Agent": "QuickImage/1.0"},
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise SearchError(f"Openverse network error: {exc}") from exc

    if resp.status_code == 429:
        raise SearchError("Openverse rate limit reached, try again in a minute.")
    if resp.status_code != 200:
        raise SearchError(f"Openverse returned HTTP {resp.status_code}.")

    items = resp.json().get("results") or []
    return [
        {"url": item.get("url", ""), "thumbnail": item.get("thumbnail", "")}
        for item in items[:count]
        if item.get("url")
    ]


# -------------------------------------------------------------------- facade


def find_images(query: str, provider: str = "auto", size: str = "large",
                safe: str = "off", count: int = 5) -> list[dict]:
    """give back up to `count` results, best match first

    auto goes duckduckgo first (real web images) and falls back to openverse if
    ddg decides to rate limit us
    """
    chain = ["duckduckgo", "openverse"] if provider == "auto" else [provider]

    errors = []
    for name in chain:
        try:
            if name == "duckduckgo":
                results = _search_duckduckgo(query, size, safe, count)
            elif name == "openverse":
                results = _search_openverse(query, size, safe, count)
            else:
                raise SearchError(f"Unknown provider {name!r}.")
        except SearchError as exc:
            errors.append(str(exc))
            continue
        if results:
            return results
        errors.append(f"{name}: no results for {query!r}.")

    raise SearchError(" ".join(errors) or f"No image results for {query!r}.")


# ------------------------------------------------------------------ download


# wikimedia bounces generic browser UAs with a 429, their policy wants a descriptive
# one instead. openverse results are mostly wikimedia + flickr anyway
WIKI_UA = "QuickImage/1.0 (desktop clipboard tool; python-requests)"


def _download_headers(url: str) -> dict:
    host = urlparse(url).netloc.lower()
    if host.endswith("wikimedia.org") or host.endswith("wikipedia.org"):
        return {"User-Agent": WIKI_UA}
    return {"User-Agent": UA}


def download_image(url: str) -> Image.Image:
    resp = requests.get(url, timeout=TIMEOUT, headers=_download_headers(url), stream=True)
    resp.raise_for_status()

    data = bytearray()
    for chunk in resp.iter_content(64 * 1024):
        data.extend(chunk)
        if len(data) > MAX_BYTES:
            raise SearchError("Image is larger than 25 MB.")

    image = Image.open(io.BytesIO(data))
    image.load()
    return image


def fetch_first_usable(results: list[dict]) -> tuple[Image.Image, str]:
    """walk the results til one actually downloads and decodes

    the top hit is real often hotlink-protected or just a dead link, so falling
    through to the next one matters way more than youd think
    """
    errors = []
    for result in results:
        for url in (result["url"], result.get("thumbnail")):
            if not url:
                continue
            try:
                return download_image(url), url
            except SearchError:
                raise
            except Exception as exc:
                errors.append(f"{url[:60]}: {exc}")
    detail = errors[0] if errors else "no candidates"
    raise SearchError(f"Every result failed to download ({detail}).")


def downscale(image: Image.Image, max_pixels: int) -> Image.Image:
    if not max_pixels or max(image.size) <= max_pixels:
        return image
    scale = max_pixels / max(image.size)
    new_size = (max(1, int(image.width * scale)), max(1, int(image.height * scale)))
    return image.resize(new_size, Image.LANCZOS)
