"""Flask application factory and HTTP server configuration."""

from __future__ import annotations

import logging
from typing import Any

from flask import Flask, jsonify
from flask_cors import CORS
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    """Initialize and configure the Flask REST API application."""
    app = Flask(__name__)

    # Default configuration
    app.config.from_mapping(
        SECRET_KEY="studylab-dev-secret-key",
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB max upload
    )

    if test_config:
        app.config.update(test_config)

    # Configure CORS for frontend access
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register error handlers
    @app.errorhandler(ValidationError)
    def handle_validation_error(err: ValidationError) -> tuple[Any, int]:
        logger.warning(f"Request validation failed: {err}")
        return jsonify({"error": "Validation error", "details": err.errors()}), 400

    @app.errorhandler(FileNotFoundError)
    @app.errorhandler(LookupError)
    def handle_not_found_error(err: Exception) -> tuple[Any, int]:
        logger.warning(f"Resource not found: {err}")
        return jsonify({"error": str(err)}), 404

    @app.errorhandler(ValueError)
    def handle_value_error(err: ValueError) -> tuple[Any, int]:
        logger.warning(f"Unprocessable entity: {err}")
        return jsonify({"error": str(err)}), 422

    @app.errorhandler(Exception)
    def handle_generic_exception(err: Exception) -> tuple[Any, int]:
        logger.error(f"Internal server error: {err}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    # Base health endpoint
    @app.route("/api/health", methods=["GET"])
    def health_check() -> Any:
        return jsonify({"status": "ok", "version": "0.1.0"})

    # Register modular Blueprints
    from src.api.routes.analytics import analytics_bp
    from src.api.routes.books import books_bp
    from src.api.routes.player import player_bp

    app.register_blueprint(books_bp, url_prefix="/api/books")
    app.register_blueprint(player_bp, url_prefix="/api")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
