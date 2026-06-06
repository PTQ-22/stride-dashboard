"""WSGI entry point for production servers (``gunicorn wsgi:server``)."""

from garmin_dashboard.app import create_app

app = create_app()
server = app.server  # the underlying Flask server gunicorn binds to

if __name__ == "__main__":
    from garmin_dashboard.config import DEBUG, HOST, PORT

    app.run(host=HOST, port=PORT, debug=DEBUG)
