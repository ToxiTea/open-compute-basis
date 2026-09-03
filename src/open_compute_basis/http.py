from __future__ import annotations

import time
from typing import Any

import httpx

from .logging_utils import configure_logging

log = configure_logging()


class FetchError(RuntimeError):
    pass


def fetch_json(
    url: str,
    *,
    timeout: float = 20.0,
    retries: int = 3,
    backoff: float = 1.5,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
) -> Any:
    last_exc: Exception | None = None
    for attempt in range(retries):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                response = client.get(url, params=params)
            if response.status_code == 429:
                wait = _retry_after(response, backoff * (attempt + 1))
                log.warning("rate limited; sleeping %s s", wait)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            last_exc = exc
            if attempt + 1 == retries:
                break
            time.sleep(backoff * (attempt + 1))
    raise FetchError(f"failed to fetch {url}: {last_exc}")


def _retry_after(response: httpx.Response, fallback: float) -> float:
    header = response.headers.get("Retry-After")
    if header:
        try:
            return max(float(header), 0.5)
        except ValueError:
            pass
    body = response.text or ""
    for token in body.replace(",", " ").split():
        if token.isdigit():
            return max(float(token), 0.5)
    return fallback
