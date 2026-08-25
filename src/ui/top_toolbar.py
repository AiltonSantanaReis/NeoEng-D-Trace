"""Compatibility entrypoint for the semantic top-command contract.

The historical function name remains available while callers migrate, but the
function no longer reads, configures, clears, or populates physical ``QToolBar``
hosts.  ``TopCommandContract`` is the canonical source of command-family
membership; visible product chrome is composed separately by
:mod:`src.ui.reference_chrome`.
"""

from __future__ import annotations

from typing import Any

from src.ui.top_command_contract import build_top_command_contract


def configure_top_toolbars(window: Any) -> None:
    """Install semantic command-family surfaces without physical projection.

    The public entrypoint is intentionally retained for compatibility with the
    MainWindow initialization sequence.  Existing QAction/control identities
    are reused by :func:`build_top_command_contract`; no toolbar widget is read
    or mutated here.
    """

    semantic_contract = build_top_command_contract(window)
    semantic_groups = semantic_contract.as_mapping()
    window.top_command_contract = semantic_contract
    window.top_command_groups = semantic_groups

    # Transitional aliases remain object-level compatibility surfaces only.
    # They now describe the semantic contract and carry no physical-toolbar
    # requirements.  New code should consume ``top_command_contract``.
    window.top_toolbar_groups = semantic_groups
    window.top_toolbar_contract = {
        "stage": semantic_contract.stage,
        "group_order": semantic_contract.group_names(),
        "group_roles": {
            group.name: group.role for group in semantic_contract.groups
        },
        "action_identity_preserved": semantic_contract.action_identity_preserved,
        "physical_toolbar_required": semantic_contract.physical_toolbar_required,
    }


__all__ = ["configure_top_toolbars"]
