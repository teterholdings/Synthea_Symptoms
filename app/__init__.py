import os
from flask import Flask
from flask_session import Session
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from . import config

def create_app(test_config=None):

    # create app
    app = Flask(__name__)

    # load config
    app.config.from_object(config.Config)

    # Bootstrap plugin
    Bootstrap(app)

    # Session plugin
    Session(app)

    # Navbar plugin
    nav = Nav()
    @nav.navigation()
    def main_navbar():
        return Navbar(
            'Symptoms Investigator',
            View('Home','main.home')
        )
    nav.init_app(app)

    # Register main blueprint
    from .main import main as main_blueprint 
    app.register_blueprint(main_blueprint)

    return app

