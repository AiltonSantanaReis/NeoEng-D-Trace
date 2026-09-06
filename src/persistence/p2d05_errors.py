"""Stable, privacy-safe error messages for the P2D-05 user flow.

Persistence and editing layers keep their typed exceptions.  This module is a
presentation boundary: it classifies those failures without importing UI
modules, removes host-specific data, and gives the user one concrete next
action.  It deliberately does not change whether an operation succeeds or
which transaction/recovery path is taken.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class P2D05ErrorMessage:
    """A reproducible error classification suitable for a user-facing UI."""

    code: str
    headline: str
    action: str
    preserved_state: str


_PATH_PATTERNS: Final[tuple[re.Pattern[str], ...]] = (
    re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\r\n\"']+"),
    re.compile(r"(?<![A-Za-z0-9_])\\\\[^\r\n\"']+"),
    re.compile(r"/(?:home|mnt|Users|tmp)/[^\r\n\"']+"),
)
_SECRET_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?i)\b(password|passwd|token|secret|api[_-]?key|authorization)\b"
    r"\s*[:=]\s*[^\s,;]+"
)
_WHITESPACE_PATTERN: Final[re.Pattern[str]] = re.compile(r"\s+")
_MAX_DETAIL_LENGTH: Final[int] = 240


_MESSAGES: Final[dict[str, dict[str, tuple[str, str, str]]]] = {
    "format": {
        "en": (
            "The scenario format is invalid",
            "Check UTF-8 JSON, required fields and the supported schema version",
            "The active document was not replaced",
        ),
        "pt": (
            "O formato do cenário é inválido",
            (
                "Verifique o JSON UTF-8, os campos obrigatórios e a versão de schema"
                " suportada"
            ),
            "O documento ativo não foi substituído",
        ),
    },
    "limit": {
        "en": (
            "The operation exceeds a supported limit",
            "Reduce the scene or operation size and retry",
            "No partial change was applied",
        ),
        "pt": (
            "A operação excede um limite suportado",
            "Reduza o tamanho da cena ou da operação e tente novamente",
            "Nenhuma alteração parcial foi aplicada",
        ),
    },
    "asset": {
        "en": (
            "A scene asset is missing, outside the project, or has changed",
            "Relink or replace the asset, then retry",
            "The last valid document remains preserved",
        ),
        "pt": (
            "Um asset do cenário está ausente, fora do projeto ou foi alterado",
            "Faça relink ou substitua o asset e tente novamente",
            "O último documento válido permanece preservado",
        ),
    },
    "target": {
        "en": (
            "The selected export target or capability is not supported",
            "Choose a supported target and retry",
            "No incomplete export was written",
        ),
        "pt": (
            "O destino ou a capacidade de exportação selecionada não é suportada",
            "Escolha um destino suportado e tente novamente",
            "Nenhum export incompleto foi gravado",
        ),
    },
    "read": {
        "en": (
            "The scenario could not be read",
            "Check that the file exists and is accessible, or use Recover Last Valid",
            "The active document was not replaced",
        ),
        "pt": (
            "Não foi possível ler o cenário",
            (
                "Verifique se o arquivo existe e está acessível, ou use Recuperar"
                " último válido"
            ),
            "O documento ativo não foi substituído",
        ),
    },
    "write": {
        "en": (
            "The scenario could not be saved",
            "Check write permission and free space, then retry",
            "The previous saved file remains unchanged",
        ),
        "pt": (
            "Não foi possível salvar o cenário",
            "Verifique a permissão de gravação e o espaço livre e tente novamente",
            "O arquivo salvo anteriormente permanece inalterado",
        ),
    },
    "recovery": {
        "en": (
            "Recovery could not be loaded",
            "Keep the current file and repair it or choose another valid recovery",
            "No document was replaced",
        ),
        "pt": (
            "Não foi possível carregar a recuperação",
            "Mantenha o arquivo atual e repare-o ou escolha outra recuperação válida",
            "Nenhum documento foi substituído",
        ),
    },
    "lock": {
        "en": (
            "The operation is blocked because the selection is locked",
            "Unlock the object, layer or group and retry",
            "No change was applied",
        ),
        "pt": (
            "A operação está bloqueada porque a seleção está bloqueada",
            "Desbloqueie o objeto, camada ou grupo e tente novamente",
            "Nenhuma alteração foi aplicada",
        ),
    },
    "reference": {
        "en": (
            "The operation references a missing scene item",
            "Refresh the document and select an existing item",
            "No change was applied",
        ),
        "pt": (
            "A operação referencia um item ausente do cenário",
            "Atualize o documento e selecione um item existente",
            "Nenhuma alteração foi aplicada",
        ),
    },
    "preview": {
        "en": (
            "The scenario preview could not be updated",
            "Check the active document and referenced assets, then retry",
            "The authored document was not changed",
        ),
        "pt": (
            "Não foi possível atualizar a visualização do cenário",
            "Verifique o documento ativo e os assets referenciados e tente novamente",
            "O documento autoral não foi alterado",
        ),
    },
    "operation": {
        "en": (
            "The operation was rejected",
            "Verify the selected item and document state, then retry",
            "No change was applied",
        ),
        "pt": (
            "A operação foi rejeitada",
            "Verifique o item selecionado e o estado do documento e tente novamente",
            "Nenhuma alteração foi aplicada",
        ),
    },
}

_CODES: Final[dict[str, str]] = {
    "format": "P2D05-FORMAT",
    "limit": "P2D05-LIMIT",
    "asset": "P2D05-ASSET",
    "target": "P2D05-TARGET",
    "read": "P2D05-READ",
    "write": "P2D05-WRITE",
    "recovery": "P2D05-RECOVERY",
    "lock": "P2D05-LOCK",
    "reference": "P2D05-REFERENCE",
    "preview": "P2D05-PREVIEW",
    "operation": "P2D05-OPERATION",
}


def redact_p2d05_detail(value: object) -> str:
    """Return a short diagnostic with host paths and credentials removed."""

    try:
        text = str(value)
    except Exception:
        return "details unavailable"
    for pattern in _PATH_PATTERNS:
        text = pattern.sub("<path>", text)
    text = _SECRET_PATTERN.sub(r"\1=<redacted>", text)
    text = _WHITESPACE_PATTERN.sub(" ", text).strip()
    if len(text) > _MAX_DETAIL_LENGTH:
        text = text[:_MAX_DETAIL_LENGTH].rstrip() + "…"
    return text


def _kind_for(exc: BaseException, operation: str) -> str:
    name = type(exc).__name__.lower()
    detail = redact_p2d05_detail(exc).lower()
    normalized_operation = operation.strip().lower()

    if normalized_operation in {"recovery", "recover"}:
        return "recovery"
    if "asset" in name or "asset" in detail:
        return "asset"
    if normalized_operation in {"export", "runtime_export"}:
        if "unsupported" in detail or "target" in detail or "capabilit" in detail:
            return "target"
        return "operation" if "validation" in name else "target"
    if any(token in detail for token in ("exceed", "limit", "too many", "oversized")):
        return "limit"
    if "format" in name or any(
        token in detail for token in ("utf-8", "bom", "json", "schema version")
    ):
        return "format"
    if "validation" in name or "schema" in detail:
        return "format"
    if isinstance(exc, PermissionError) or "lock" in detail:
        return (
            "lock"
            if normalized_operation in {"edit", "transform", "group"}
            else "write"
        )
    if isinstance(exc, KeyError) or "unknown" in detail or "reference" in detail:
        return "reference"
    if (
        "write" in name
        or isinstance(exc, OSError)
        or normalized_operation
        in {
            "save",
            "write",
        }
    ):
        return "write"
    if "read" in name or normalized_operation in {"load", "reload"}:
        return "read"
    if normalized_operation == "preview":
        return "preview"
    return "operation"


def classify_p2d05_error(
    exc: BaseException,
    *,
    operation: str,
    language: str = "en",
) -> P2D05ErrorMessage:
    """Classify a failure without changing its domain exception."""

    kind = _kind_for(exc, operation)
    lang = language if language in {"en", "pt"} else "en"
    headline, action, preserved_state = _MESSAGES[kind][lang]
    return P2D05ErrorMessage(_CODES[kind], headline, action, preserved_state)


def user_error_message(
    exc: BaseException,
    *,
    operation: str,
    language: str = "en",
) -> str:
    """Format a safe, actionable message for Qt status bars and dialogs."""

    classification = classify_p2d05_error(
        exc,
        operation=operation,
        language=language,
    )
    detail = redact_p2d05_detail(exc)
    suffix = f" Detail: {detail}." if detail else "."
    return (
        f"{classification.headline} [{classification.code}]. "
        f"{classification.action}. {classification.preserved_state}.{suffix}"
    )


__all__ = [
    "P2D05ErrorMessage",
    "classify_p2d05_error",
    "redact_p2d05_detail",
    "user_error_message",
]
