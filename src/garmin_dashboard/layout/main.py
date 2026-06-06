"""Root layout: navbar, sticky filter sidebar, tabbed content and stores."""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import dcc, html

from ..components.controls import control_panel
from ..components.navbar import navbar
from ..data.loader import get_meta
from . import about, explorer, map_tab, overview, physiology

# Store id holding the currently selected activity id (linked-view state).
SELECTED_STORE = "selected-activity"
TABS_ID = "main-tabs"


def serve_layout() -> html.Div:
    """Layout factory (called per request so caches/data stay fresh)."""
    meta = get_meta()
    tabs = dbc.Tabs(
        id=TABS_ID,
        active_tab="tab-overview",
        children=[
            dbc.Tab(overview.layout(), label="Overview", tab_id="tab-overview",
                    tab_class_name="nav-tab"),
            dbc.Tab(explorer.layout(), label="Explorer", tab_id="tab-explorer",
                    tab_class_name="nav-tab"),
            dbc.Tab(map_tab.layout(), label="Map", tab_id="tab-map",
                    tab_class_name="nav-tab"),
            dbc.Tab(physiology.layout(), label="Performance", tab_id="tab-physiology",
                    tab_class_name="nav-tab"),
            dbc.Tab(about.layout(meta), label="About", tab_id="tab-about",
                    tab_class_name="nav-tab"),
        ],
    )
    sidebar = html.Div(control_panel(meta), className="sidebar")
    content = html.Div(tabs, className="content")
    return html.Div(
        [
            dcc.Store(id=SELECTED_STORE, data=None),
            navbar(meta),
            html.Div([sidebar, content], className="app-body"),
        ],
        className="app-root",
    )
