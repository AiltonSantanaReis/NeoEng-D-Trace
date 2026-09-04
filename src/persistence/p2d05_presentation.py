"""UI-independent canonical presentation data for P2D-05 failures.

This module assembles the stable catalog entry and the presentation metadata.
It deliberately imports no Qt classes.  The Qt adapter consumes this immutable
descriptor and is responsible only for rendering it through the selected
channel.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, cast

from src.persistence.p2d05_errors import (
    classify_p2d05_error,
    redact_p2d05_detail,
    user_error_message,
)

ErrorChannel = Literal["modal", "status"]
ErrorSeverity = Literal["info", "warning", "error", "critical"]
PresentationChannel = Literal["MODAL", "STATUS"]
PresentationSeverity = Literal["INFO", "WARNING", "ERROR", "CRITICAL"]

_DETAIL_LABELS = {
    "en": {
        "code": "Error code",
        "severity": "Severity",
        "channel": "Channel",
        "operation": "Operation",
        "exception": "Exception type",
        "retryable": "Retryable",
        "detail": "Safe detail",
        "unavailable": "Details unavailable",
    },
    "pt": {
        "code": "Código do erro",
        "severity": "Severidade",
        "channel": "Canal",
        "operation": "Operação",
        "exception": "Tipo da exceção",
        "retryable": "Pode tentar novamente",
        "detail": "Detalhe seguro",
        "unavailable": "Detalhes indisponíveis",
    },
}


@dataclass(frozen=True)
class P2D05Presentation:
    """Complete, immutable descriptor required by the P2D-05 contract."""

    code: str
    severity: PresentationSeverity
    blocking: bool
    headline: str
    message: str
    action: str
    preserved_state: str
    channel: PresentationChannel
    safe_detail: str
    retryable: bool
    focus_target: str | None
    exception_type: str
    operation: str
    language: str

    @property
    def detailed_text(self) -> str:
        labels = _DETAIL_LABELS[self.language]
        detail = self.safe_detail or labels["unavailable"]
        return "\n".join(
            (
                f"{labels['code']}: {self.code}",
                f"{labels['severity']}: {self.severity}",
                f"{labels['channel']}: {self.channel}",
                f"{labels['operation']}: {self.operation}",
                f"{labels['exception']}: {self.exception_type}",
                f"{labels['retryable']}: {self.retryable}",
                f"{labels['detail']}: {detail}",
            )
        )


def _normalized_language(language: str) -> str:
    return (
        language if isinstance(language, str) and language in _DETAIL_LABELS else "en"
    )


def _normalized_severity(severity: str) -> ErrorSeverity:
    if not isinstance(severity, str) or severity not in {
        "info",
        "warning",
        "error",
        "critical",
    }:
        raise ValueError(f"Unsupported P2D-05 error severity: {severity}")
    return cast(ErrorSeverity, severity)


def _normalized_channel(channel: str) -> ErrorChannel:
    if not isinstance(channel, str) or channel not in {"modal", "status"}:
        raise ValueError(f"Unsupported P2D-05 error channel: {channel}")
    return cast(ErrorChannel, channel)


def build_p2d05_presentation(
    exc: BaseException,
    *,
    operation: str,
    language: str = "en",
    severity: str = "warning",
    channel: str = "modal",
    blocking: bool | None = None,
    retryable: bool = True,
    focus_target: str | None = None,
) -> P2D05Presentation:
    """Build localized, actionable, redacted P2D-05 presentation data."""

    normalized_language = _normalized_language(language)
    normalized_severity = _normalized_severity(severity)
    normalized_channel = _normalized_channel(channel)
    normalized_operation = (
        operation.strip() if isinstance(operation, str) else "operation"
    ) or "operation"
    classification = classify_p2d05_error(
        exc,
        operation=normalized_operation,
        language=normalized_language,
    )
    resolved_blocking = (
        normalized_channel == "modal" and normalized_severity in {"error", "critical"}
        if blocking is None
        else bool(blocking)
    )
    normalized_focus = (
        focus_target.strip()
        if isinstance(focus_target, str) and focus_target.strip()
        else None
    )
    return P2D05Presentation(
        code=classification.code,
        severity=cast(
            PresentationSeverity,
            normalized_severity.upper(),
        ),
        blocking=resolved_blocking,
        headline=classification.headline,
        message=user_error_message(
            exc,
            operation=normalized_operation,
            language=normalized_language,
        ),
        action=classification.action,
        preserved_state=classification.preserved_state,
        channel=cast(PresentationChannel, normalized_channel.upper()),
        safe_detail=redact_p2d05_detail(exc),
        retryable=bool(retryable),
        focus_target=normalized_focus,
        exception_type=type(exc).__name__,
        operation=normalized_operation,
        language=normalized_language,
    )


__all__ = [
    "ErrorChannel",
    "ErrorSeverity",
    "P2D05Presentation",
    "PresentationChannel",
    "PresentationSeverity",
    "build_p2d05_presentation",
]
