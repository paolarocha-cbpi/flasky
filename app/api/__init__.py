from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from . import authentication, posts, users, comments, errors
from ..main import api as api_blueprint

bootstrap = Bootstrap()
moment = Moment()
db = SQLAlchemy()


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    bootstrap.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    return app
