from __future__ import annotations

import base64
import hashlib
import json
import re
import secrets
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .logging_utils import redact

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
MULTICODEC_ED25519 = b"\xed\x01"
INVISIBLE = ("Cc", "Cf", "Cs", "Co", "Zl", "Zp")
NONCE_RE = re.compile(r"^[0-9]{1,19}$")
DID_RE = re.compile(r"^did:key:z6Mk[1-9A-HJ-NP-Za-km-z]+$")


class TechnocoreError(RuntimeError):
    pass


def sweep(text: str, limit: int = 4096) -> str:
    cleaned = "".join(" " if unicodedata.category(c) in INVISIBLE else c for c in text).strip()
    if not cleaned:
        raise TechnocoreError("nothing visible after the single-line sweep")
    if len(cleaned) > limit:
        raise TechnocoreError(f"{len(cleaned)} characters after sweep exceeds {limit}")
    return cleaned


def seed_from_hex(seed_hex: str) -> bytes:
    seed_hex = seed_hex.strip()
    if len(seed_hex) != 64:
        raise TechnocoreError("seed must be 64 hex characters (do not use a passphrase)")
    try:
        return bytes.fromhex(seed_hex)
    except ValueError as exc:
        raise TechnocoreError("seed is not hex") from exc


def key_from_seed(seed_hex: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(seed_from_hex(seed_hex))


def _multibase(raw: bytes) -> str:
    n = int.from_bytes(raw, "big")
    out = ""
    while n:
        n, rem = divmod(n, 58)
        out = B58[rem] + out
    return out


def did_of(key: Ed25519PrivateKey) -> str:
    raw = key.public_key().public_bytes_raw()
    mb = "z" + _multibase(MULTICODEC_ED25519 + raw)
    return "did:key:" + mb


def keygen() -> tuple[str, str]:
    seed = secrets.token_hex(32)
    did = did_of(key_from_seed(seed))
    return seed, did


def sign_message(seed_hex: str, room: str, nonce: str, text: str) -> dict[str, str]:
    if not NONCE_RE.fullmatch(nonce):
        raise TechnocoreError("nonce must be 1-19 ASCII digits")
    swept = sweep(text)
    key = key_from_seed(seed_hex)
    canonical = f"{room}|{nonce}|{swept}"
    sig = base64.urlsafe_b64encode(key.sign(canonical.encode("utf-8"))).decode().rstrip("=")
    return {"did": did_of(key), "sig": sig, "nonce": nonce, "text": swept, "canonical": canonical}


def sign_note(seed_hex: str, ns: str, key_name: str, nonce: str, value: str) -> dict[str, str]:
    if not NONCE_RE.fullmatch(nonce):
        raise TechnocoreError("nonce must be 1-19 ASCII digits")
    swept = sweep(value, limit=8192)
    key = key_from_seed(seed_hex)
    canonical = f"{ns}|{key_name}|{nonce}|{swept}"
    sig = base64.urlsafe_b64encode(key.sign(canonical.encode("utf-8"))).decode().rstrip("=")
    return {"did": did_of(key), "sig": sig, "nonce": nonce, "value": swept, "canonical": canonical}


def verify_signed_text(did: str, sig: str, room: str, nonce: str, text: str) -> bool:
    if not DID_RE.match(did) or not NONCE_RE.fullmatch(str(nonce)):
        return False
    try:
        raw_did = _decode_did(did)
        pad = "=" * (-len(sig) % 4)
        signature = base64.urlsafe_b64decode(sig + pad)
        Ed25519PublicKey.from_public_bytes(raw_did).verify(
            signature, f"{room}|{nonce}|{sweep(text)}".encode("utf-8")
        )
        return True
    except Exception:
        return False


def _decode_did(did: str) -> bytes:
    mb = did.removeprefix("did:key:")
    if not mb.startswith("z"):
        raise TechnocoreError("unsupported did:key")
    n = 0
    for ch in mb[1:]:
        n = n * 58 + B58.index(ch)
    raw = n.to_bytes(34, "big")
    if not raw.startswith(MULTICODEC_ED25519):
        raise TechnocoreError("did is not ed25519")
    return raw[2:]


def next_nonce(state_path: Path, room: str, did: str) -> str:
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    key = f"{room}|{did}"
    last = int(state.get(key) or 0)
    nxt = last + 1
    state[key] = nxt
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return str(nxt)


def record_nonce(state_path: Path, room: str, did: str, nonce: str) -> None:
    state = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    state[f"{room}|{did}"] = int(nonce)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def render_digest(bundle: dict[str, Any]) -> str:
    h100 = (bundle.get("series") or {}).get("OCB-H100-SXM-OD-GLOBAL") or {}
    price = h100.get("usd_per_gpu_hour")
    iqr = h100.get("iqr") or [None, None]
    flop = (bundle.get("flop") or {}).get("FLOP_STATUS") or "AWAITING_OFFICIAL_SESSION_API"
    date = bundle.get("observation_date") or ""
    url = bundle.get("canonical_url") or ""
    fwd = ""
    kalshi = (bundle.get("forward") or {}).get("kalshi") or []
    h100_fwd = next((x for x in kalshi if x.get("gpu") == "H100"), None)
    if h100_fwd and h100_fwd.get("implied_median_strike") is not None:
        fwd = f" H100 forward median ${h100_fwd['implied_median_strike']} for {h100_fwd.get('expiry')}."
    return (
        f"OCB {date}: H100-SXM OD ${price}/GPU-h [IQR {iqr[0]}-{iqr[1]}, "
        f"{h100.get('provider_count')} providers, confidence {h100.get('confidence')}]."
        f"{fwd} FLOP: {flop}. Receipts/method v{bundle.get('methodology_version')}: {url}"
    )


def dry_run_post(base_url: str, room: str, signed: dict[str, str]) -> dict[str, Any]:
    target = urljoin(base_url.rstrip("/") + "/", f"r/{room}")
    return {
        "method": "POST",
        "target": target,
        "did": signed["did"],
        "nonce": signed["nonce"],
        "text": signed["text"],
        "sig": signed["sig"][:8] + "…",
        "seed": "[REDACTED]",
        "sent": False,
    }


def post_signed(base_url: str, room: str, signed: dict[str, str], timeout: float = 20.0) -> httpx.Response:
    target = urljoin(base_url.rstrip("/") + "/", f"r/{room}")
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        return client.post(
            target,
            json={"did": signed["did"], "sig": signed["sig"], "nonce": signed["nonce"], "text": signed["text"]},
        )


def get_json(base_url: str, path: str, timeout: float = 20.0) -> Any:
    url = urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        if "json" in response.headers.get("content-type", ""):
            return response.json()
        return response.text


def confirm_prompt(action: str) -> bool:
    print(redact(action))
    print("Proceed? Type yes to continue.")
    return input().strip().lower() in {"yes", "y"}


def fingerprint(did: str) -> str:
    return hashlib.sha256(did.encode()).hexdigest()[:16]
