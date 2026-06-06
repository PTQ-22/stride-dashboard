"""Visual identity: colour palette and a shared Plotly template.

Charts call :func:`styled_figure` / :func:`apply_theme` so every figure in the
app shares the same dark, cinematic look without repeating layout boilerplate.
"""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# --- palette ---------------------------------------------------------------
# Charcoal base + warm "track orange" accent, evoking a tartan running track.
COLORS = {
    "bg": "#12141a",
    "surface": "#1b1e27",
    "surface_alt": "#232734",
    "grid": "#2c3140",
    "text": "#e8e6e1",
    "text_muted": "#8b91a3",
    "accent": "#ff6b35",       # track orange
    "accent_soft": "#ffb38a",
    "secondary": "#4cc9f0",    # cool cyan for HR / contrast
    "good": "#69db7c",
    "warn": "#ffd43b",
}

# Sport -> colour mapping (used across charts, table, map for consistency).
SPORT_COLORS = {
    "running": "#ff6b35",
    "cycling": "#4cc9f0",
    "walking": "#69db7c",
    "mountaineering": "#ffd43b",
    "other": "#8b91a3",
}

# Sequential scale for heatmaps / continuous encodings.
SEQUENTIAL = [
    [0.0, "#1b1e27"],
    [0.4, "#7a3a1f"],
    [0.7, "#ff6b35"],
    [1.0, "#ffb38a"],
]

FONT_FAMILY = "Inter, 'Segoe UI', system-ui, sans-serif"

# --- Plotly template -------------------------------------------------------
_template = go.layout.Template()
_template.layout = go.Layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family=FONT_FAMILY, color=COLORS["text"], size=13),
    title=dict(font=dict(size=16, color=COLORS["text"]), x=0.01, xanchor="left"),
    margin=dict(l=56, r=24, t=48, b=44),
    colorway=[
        COLORS["accent"], COLORS["secondary"], COLORS["good"],
        COLORS["warn"], COLORS["accent_soft"], "#b197fc",
    ],
    xaxis=dict(gridcolor=COLORS["grid"], zeroline=False, linecolor=COLORS["grid"]),
    yaxis=dict(gridcolor=COLORS["grid"], zeroline=False, linecolor=COLORS["grid"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=COLORS["text_muted"])),
    hoverlabel=dict(bgcolor=COLORS["surface_alt"], font=dict(family=FONT_FAMILY)),
)
pio.templates["stride"] = _template

# dbc Bootstrap theme used for the component library.
DBC_THEME = "https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css"
FONT_CDN = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"


def apply_theme(fig: go.Figure, **layout_kwargs) -> go.Figure:
    """Apply the shared template + sensible defaults to a figure in-place."""
    fig.update_layout(template="stride", **layout_kwargs)
    return fig


def empty_figure(message: str = "No activities match the current filters") -> go.Figure:
    """A themed placeholder shown when a selection yields no data."""
    fig = go.Figure()
    fig.add_annotation(
        text=message, showarrow=False,
        font=dict(color=COLORS["text_muted"], size=14),
        xref="paper", yref="paper", x=0.5, y=0.5,
    )
    fig.update_layout(
        template="stride",
        xaxis=dict(visible=False), yaxis=dict(visible=False),
        margin=dict(l=8, r=8, t=8, b=8),
    )
    return fig
