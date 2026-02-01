from __future__ import annotations

import os
from dotenv import load_dotenv
from flask import Flask
from typing import Any

from .extensions import db
from .routes import main_bp
from .services import DB_PATH, init_database


def create_app(config_overrides: dict[str, Any] | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    openrouter_token = os.getenv("OPENROUTER_API_KEY", "")
    app.config["OPENROUTER_API_KEY"] = openrouter_token
    llm_enabled_env = os.getenv("LLM_ENABLED")
    if llm_enabled_env is None:
        app.config["LLM_ENABLED"] = bool(openrouter_token)
    else:
        app.config["LLM_ENABLED"] = llm_enabled_env.lower() == "true"
    app.config["OPENROUTER_MODEL"] = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    app.config["OPENROUTER_TIMEOUT"] = int(os.getenv("OPENROUTER_TIMEOUT", "30"))
    app.config["OPENROUTER_SITE_URL"] = os.getenv("OPENROUTER_SITE_URL", "")
    app.config["OPENROUTER_APP_NAME"] = os.getenv("OPENROUTER_APP_NAME", "")
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        init_database(app.config["SQLALCHEMY_DATABASE_URI"])

    return app
