""" App initialization module."""

import logging
from logging.config import dictConfig
from os import path
import yaml
from flask import Flask

from server.managers.mqtt_manager import mqtt_manager_service
from server.managers.wifi_bands_manager import wifi_bands_manager_service
from server.managers.thread_manager import thread_manager_service
from server.managers.alimelo_manager import alimelo_manager_service
from .managers.camera_manager import camera_manager_service
from .managers.electrical_panel_manager import electrical_panel_manager_service
from .rest_api.wifi_controler import bp as wifi_controler_bp
from .rest_api.thread_controler import bp as thread_controler_bp
from .rest_api.alimelo_controler import bp as alimelo_controler_bp
from .rest_api.camera_controler import bp as camera_controler_bp
from .rest_api.electrical_panel_controler import bp as electrical_panel_controler_bp
from .rest_api.use_situations_controler import bp as use_situations_controler_bp
from .rest_api.system_version_controler import bp as system_version_controler_bp
from .orchestrator import orchestrator_service
from .extension import api
from .common import ServerBoxException, handle_server_box_exception

logger = logging.getLogger(__name__)


def create_app(
    config_dir: str = path.join(path.dirname(path.abspath(__file__)), "config"),
):
    """Create the Flask app"""

    # Create app Flask
    app = Flask("Server Box")

    # Get configuration files
    app_config = path.join(config_dir, "server-box-config.yml")
    logging_config = path.join(config_dir, "logging-config.yml")

    # Load logging configuration and configure flask application logger
    with open(logging_config) as stream:
        dictConfig(yaml.full_load(stream))

    logger.info("App config file: %s", app_config)

    # Load configuration
    app.config.from_file(app_config, load=yaml.full_load)

    # Register extensions
    register_extensions(app)
    # register orchestrator
    register_orchestrator(app)
    # Register blueprints for REST API
    register_blueprints(app)
    logger.info("App ready!!")

    return app


def register_extensions(app: Flask):
    """Initialize all extensions"""

    # Initialize REST APIs.
    #
    # The spec_kwargs dict is used to generate the OpenAPI document that describes our APIs.
    # The securitySchemes field defines the security scheme used to protect our APIs.
    #   - BasicAuth  allows to authenticate a user with a login and a password.
    #   - BearerAuth allows to authenticate a user using a token (the /login API allows to a user
    #     to retrieve a valid token).

    api.init_app(
        app,
        spec_kwargs={
            "info": {"description": "`Orchestrator` OpenAPI 3.0 specification."},
            "components": {
                "securitySchemes": {
                    "basicAuth": {"type": "http", "scheme": "basic"},
                    "tokenAuth": {"type": "http", "scheme": "bearer"},
                },
            },
        },
    )
    # MQTT service
    mqtt_manager_service.init_app(app=app)
    # Wifi bands manager extension
    wifi_bands_manager_service.init_app(app=app)
    # Thread manager extension
    thread_manager_service.init_app(app=app)
    # Camera manager service
    camera_manager_service.init_app(app=app)
    # Electrical panel manager service
    electrical_panel_manager_service.init_app(app=app)
    # Alimelo manager extension
    alimelo_manager_service.init_app(app=app)


def register_orchestrator(app: Flask):
    """Initialize Orchestrator"""
    orchestrator_service.init_app(app=app)


def register_blueprints(app: Flask):
    """Store App APIs blueprints."""
    # Register error handler
    app.register_error_handler(ServerBoxException, handle_server_box_exception)
    # Register REST blueprints
    api.register_blueprint(wifi_controler_bp)
    api.register_blueprint(thread_controler_bp)
    api.register_blueprint(alimelo_controler_bp)
    api.register_blueprint(camera_controler_bp)
    api.register_blueprint(electrical_panel_controler_bp)
    api.register_blueprint(use_situations_controler_bp)
    api.register_blueprint(system_version_controler_bp)
