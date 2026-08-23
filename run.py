"""Development entry point: `python run.py`. For anything beyond local
dev, prefer `flask run` / a real WSGI server against `create_app()`."""
import os

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
