"""Unlister: The Web App For Detecting Unlisted YouTube Videos"""

import logging
import logging.config
import json
import os
import sys

from flask import Flask
from flask.logging import default_handler as flask_default_handler

# Configuration values
CONFIG_YOUTUBE_DEV_KEY = "YOUTUBE_DEV_KEY"

def create_app(config=None) -> Flask:
    """Creates the Flask app."""
    # Setup the logging name so that all the levels have the same length
    logging.addLevelName(logging.NOTSET, "UNK")
    logging.addLevelName(logging.DEBUG, "DBG")
    logging.addLevelName(logging.INFO, "INF")
    logging.addLevelName(logging.WARN, "WRN")
    logging.addLevelName(logging.ERROR, "ERR")
    logging.addLevelName(logging.CRITICAL, "CRI")

    # Initialize Flask
    app = Flask(__name__, instance_relative_config=True)
    app.logger.info("Loading configuration from %s...", app.instance_path)

    # Load the logging configuration.
    log_config_path = os.path.join(app.instance_path, "logging.json")
    try:
        with open(log_config_path, "r") as fp:
            logging.config.dictConfig(json.load(fp))

        app.logger.removeHandler(flask_default_handler)
        app.logger.info("Successfully loaded logging configuration from %s", log_config_path)
    except Exception: # pylint: disable=broad-except
        # Looks like the logging configuration doesn't exist. Provide some sane defaults.
        logging.basicConfig(
            level=logging.DEBUG if app.debug else logging.INFO,
            format="%(asctime)s - [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            stream=sys.stderr
        )

        app.logger.removeHandler(flask_default_handler)
        app.logger.error(
            "Unable to load logging configuration from %s. Using defaults...",
            log_config_path,
            exc_info=1)

    # How should we load Flask config?
    if config is not None:
        # Use the configuration that was passed explicitly.
        app.config.from_mapping(config)
    else:
        # Use the JSON file in our instance path.
        app.config.from_file("config.json", load=json.load)

    # Ensure that the configuration is OK. If not, we should print some errors (in the form
    # of warnings)
    if not is_config_ok(app):
        app.logger.warning(
            "One or more configuration keys were not defined. Unlister may not run properly. "
            "Check the logs for more information.")
    else:
        app.logger.info("Configurations loaded successfully.")


    # Register our blueprints
    from unlister import api, app as a
    app.register_blueprint(a.bp)
    app.register_blueprint(api.bp)

    return app

def is_config_ok(app: Flask):
    """
    Ensures the `config` inside a provided Flask `app` contains the configuration keys expected and
    returns `True` if the config is OK.
    """
    # Ensure we have a YouTube key
    has_error = False
    for key in [CONFIG_YOUTUBE_DEV_KEY]:
        if key not in app.config:
            app.logger.warning("Configuration value not found: %s", CONFIG_YOUTUBE_DEV_KEY)
            has_error = True

    return not has_error
