from __future__ import annotations

import logging
import re
from typing import Iterable

_HEX64 = re.compile(r"\b[0-9a-fA-F]{64}\b")
_SEED_KEYS = re.compile(
    r"(TECHNOCORE_AGENT_SEED|SIGN_SEED|owner.seed|recovery.seed|private.seed)",
    re.IGNORECASE,
)


def redact(text: str) -> str:
    text = _HEX64.sub("[REDACTED_SEED]", text)
    text = _SEED_KEYS.sub("[REDACTED_KEY]", text)
    return text


class RedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return redact(super().format(record))


def configure_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("ocb")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(RedactingFormatter("%(levelname)s %(message)s"))
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def assert_no_secrets(text: str, secrets: Iterable[str]) -> None:
    for secret in secrets:
        if secret and secret in text:
            raise AssertionError("secret material leaked into logs or artifacts")
