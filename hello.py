from flask import Flask, render_template, request, abort
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from datetime import datetime


app = Flask(__name__)
bootstrap = Bootstrap(app)
moment = Moment(app)

@app.route('/')
def index():
    user_agent = request.headers.get('User-Agent')
    return render_template('index.html', current_time=datetime.utcnow())

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)

@app.route('/user/<id>')
def get_user(id):
    user = load_user(id)
    if not user:
        abort(404)
    return '<h1>Hello, {}</h1>'.format(user.name)

@app.errorhandler(404)  # Route not known
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)  # Unhandled exception
def internal_server_error(e):
    return render_template('500.html'), 500
    