import re
import secrets

_slug_re = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = _slug_re.sub("-", text).strip("-")
    return text or "item"


def unique_slug(base_text: str, exists_fn, max_len: int = 160) -> str:
    """Builds a slug from `base_text` and appends a short random suffix if
    it collides. `exists_fn(candidate) -> bool` is supplied by the caller
    (e.g. `lambda s: Trek.query.filter_by(slug=s).first() is not None`)
    so this module has no direct DB/model dependency."""
    base = slugify(base_text)[:max_len]
    candidate = base
    while exists_fn(candidate):
        suffix = secrets.token_hex(3)  # 6 hex chars
        candidate = f"{base[: max_len - len(suffix) - 1]}-{suffix}"
    return candidate
