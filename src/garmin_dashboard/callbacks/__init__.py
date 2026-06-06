"""Callback registration.

Importing this package imports every callback module, whose ``@callback``
decorators register against Dash's global callback registry. Call
:func:`register_callbacks` after the app's layout is assigned.
"""

from __future__ import annotations


def register_callbacks() -> None:
    """Import all callback modules so their decorators take effect."""
    from . import controls, explorer, overview, physiology  # noqa: F401
