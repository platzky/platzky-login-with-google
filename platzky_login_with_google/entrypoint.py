from flask import jsonify, request, session
from jinja2 import Environment, FileSystemLoader

from pydantic import Field
from typing import Any, Dict
import os.path

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from platzky.plugin.plugin import PluginBase, PluginBaseConfig, PluginError


class LoginWithGoogleConfig(PluginBaseConfig):
    """Configuration for email sending functionality."""

    google_client_id: str = Field(
        alias="google_client_id", description="Google client ID"
    )


class LoginWithGoogle(PluginBase[LoginWithGoogleConfig]):
    """Plugin for login with Google."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

    def process(self, app: Any) -> Any:
        """Initialize the google login plugin.

        Args:
            app: The application instance

        Returns:
            The application instance

        Raises:
            ValidationError: If configuration is invalid
        """
        try:
            plugin_config = (
                self.config
            )  # Use the already validated config from __init__

            @app.route("/verify_google_login", methods=["POST"])
            def verify_google_login():
                data = request.get_json()
                token = data.get("credential")

                if not token:
                    return jsonify({"error": "Missing token"}), 400

                try:
                    id_info = id_token.verify_oauth2_token(
                        token, google_requests.Request(), plugin_config.google_client_id
                    )
                    session["user"] = id_info
                    return jsonify({"status": "logged_in", "user": id_info})
                except ValueError as e:
                    return jsonify({"error": "Invalid token", "details": str(e)}), 401

            template_dir = os.path.dirname(__file__)
            env = Environment(loader=FileSystemLoader(template_dir))

            with app.app_context():
                login_template = "login_with_google.html"
                template = env.get_template(login_template)
                # TODO this should not be template, but rather some interface for "loginMethod" or similar
                login_with_google = template.render(
                    google_client_id=plugin_config.google_client_id
                )
                app.add_login_method(login_with_google)

            return app
        except Exception as e:
            raise PluginError(f"Failed to initialize Google login plugin: {str(e)}")
