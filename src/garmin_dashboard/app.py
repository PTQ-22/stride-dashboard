"""Application factory.

``create_app`` wires together the layout, theme and callbacks and returns a
configured :class:`dash.Dash` instance. Keeping construction in a factory keeps
import side effects out of module scope and makes the app easy to test.
"""

from __future__ import annotations

import dash_bootstrap_components as dbc
from dash import Dash

from .callbacks import register_callbacks
from .config import APP_TITLE, PROJECT_ROOT
from .layout import serve_layout
from .theme import DBC_THEME, FONT_CDN

# Custom HTML shell so we can use an SVG favicon and a social description.
_INDEX_STRING = """<!DOCTYPE html>
<html>
  <head>
    {%metas%}
    <title>{%title%}</title>
    <link rel="icon" type="image/svg+xml" href="/assets/favicon.svg">
    <meta name="description" content="Stride — six years of Garmin running data as an interactive Dash dashboard.">
    {%favicon%}
    {%css%}
  </head>
  <body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>"""


def create_app() -> Dash:
    app = Dash(
        __name__,
        title=APP_TITLE,
        assets_folder=str(PROJECT_ROOT / "assets"),
        external_stylesheets=[DBC_THEME, dbc.icons.BOOTSTRAP, FONT_CDN],
        suppress_callback_exceptions=True,
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        update_title=None,
    )
    app.index_string = _INDEX_STRING
    # Layout is a callable so it is re-evaluated per page load.
    app.layout = serve_layout
    register_callbacks()
    return app
