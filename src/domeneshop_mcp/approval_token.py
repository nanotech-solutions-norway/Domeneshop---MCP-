"""One-time, payload-bound approval tokens for controlled mutations."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

from .credential_policy import has_runtime_value


class ApprovalTokenError(ValueError):
    """Raised for invalid, expired, mismatched, or replayed approvals."""


def _b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


@dataclass(frozen=True)
class ApprovalClaims:
    approval_id: str
    operator: str
    action: str
    target: str
    payload_sha256: str
    issued_utc: str
    expires_utc: str
    nonce: str


class UsedNonceStore:
    """File-backed one-time nonce ledger using atomic file creation."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def consume(self, nonce: str) -> None:
        path = self.directory / f"{hashlib.sha256(nonce.encode('utf-8')).hexdigest()}.used"
        try:
            with path.open("x", encoding="utf-8") as handle:
                handle.write(datetime.now(timezone.utc).replace(microsecond=0).isoformat())
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError as exc:
            raise ApprovalTokenError("Approval token has already been consumed") from exc


class ApprovalTokenManager:
    def __init__(
        self,
        signing_secret: str,
        nonce_store: UsedNonceStore,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not has_runtime_value(signing_secret) or len(signing_secret.encode("utf-8")) < 32:
            raise ApprovalTokenError("Approval signing secret must be a non-placeholder value of at least 32 bytes")
        self._secret = signing_secret.encode("utf-8")
        self._nonce_store = nonce_store
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def issue(
        self,
        *,
        approval_id: str,
        operator: str,
        action: str,
        target: str,
        payload_sha256: str,
        ttl_seconds: int = 600,
    ) -> str:
        if ttl_seconds < 30 or ttl_seconds > 3600:
            raise ApprovalTokenError("Approval token TTL must be between 30 and 3600 seconds")
        if len(payload_sha256) != 64:
            raise ApprovalTokenError("payload_sha256 must be a SHA-256 hexadecimal digest")
        now = self._clock().astimezone(timezone.utc).replace(microsecond=0)
        claims = ApprovalClaims(
            approval_id=approval_id,
            operator=operator,
            action=action,
            target=target,
            payload_sha256=payload_sha256,
            issued_utc=now.isoformat(),
            expires_utc=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            nonce=secrets.token_urlsafe(24),
        )
        body = json.dumps(asdict(claims), sort_keys=True, separators=(",", ":")).encode("utf-8")
        signature = hmac.new(self._secret, body, hashlib.sha256).digest()
        return f"{_b64encode(body)}.{_b64encode(signature)}"

    def verify_and_consume(
        self,
        token: str,
        *,
        action: str,
        target: str,
        payload_sha256: str,
        operator: str | None = None,
    ) -> ApprovalClaims:
        try:
            body_part, signature_part = token.split(".", 1)
            body = _b64decode(body_part)
            signature = _b64decode(signature_part)
        except Exception as exc:
            raise ApprovalTokenError("Approval token format is invalid") from exc

        expected = hmac.new(self._secret, body, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            raise ApprovalTokenError("Approval token signature is invalid")

        try:
            claims = ApprovalClaims(**json.loads(body.decode("utf-8")))
        except Exception as exc:
            raise ApprovalTokenError("Approval token payload is invalid") from exc

        now = self._clock().astimezone(timezone.utc)
        expires = datetime.fromisoformat(claims.expires_utc)
        if now > expires:
            raise ApprovalTokenError("Approval token has expired")
        if claims.action != action or claims.target != target or claims.payload_sha256 != payload_sha256:
            raise ApprovalTokenError("Approval token does not match the requested mutation")
        if operator is not None and claims.operator != operator:
            raise ApprovalTokenError("Approval token operator does not match")

        self._nonce_store.consume(claims.nonce)
        return claims
