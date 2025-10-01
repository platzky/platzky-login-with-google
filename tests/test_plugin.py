from unittest.mock import patch, ANY
from platzky.platzky import create_app_from_config, Config
from typing import Any, Dict


def test_that_plugin_loads_plugin():
    client_id = "google-client-id"

    data_with_plugin: Dict[str, Any] = {
        "APP_NAME": "testingApp",
        "SECRET_KEY": "secret",
        "USE_WWW": False,
        "BLOG_PREFIX": "/",
        "TRANSLATION_DIRECTORIES": ["/some/fake/dir"],
        "DB": {
            "TYPE": "json",
            "DATA": {
                "site_content": {"pages": []},
                "plugins": [
                    {
                        "name": "login_with_google",
                        "config": {"google_client_id": client_id},
                    }
                ],
            },
        },
    }

    config_with_plugin = Config.model_validate(data_with_plugin)
    app_with_plugin = create_app_from_config(config_with_plugin)

    mock_user_info = {
        "sub": "123456789",
        "name": "Test User",
        "email": "testuser@example.com",
    }

    with app_with_plugin.test_client() as app:
        # Generate CSRF token and setup session
        with app_with_plugin.app_context():
            with app_with_plugin.test_request_context():
                from flask import session
                from flask_wtf.csrf import generate_csrf

                csrf_token = generate_csrf()
                session_data = dict(session)

        # Set session data in test client
        with app.session_transaction() as sess:
            for key, value in session_data.items():
                sess[key] = value

        with patch(
            "google.oauth2.id_token.verify_oauth2_token", return_value=mock_user_info
        ) as mock_verify:
            response = app.post(
                "/verify_google_login",
                json={"credential": "google-token"},
                headers={"X-CSRFToken": csrf_token},
            )
            assert response.status_code == 200
            assert response.json is not None
            assert response.json["status"] == "logged_in"
            assert response.json["user"] == mock_user_info
            mock_verify.assert_called_once_with("google-token", ANY, client_id)
