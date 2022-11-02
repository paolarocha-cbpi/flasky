# Estructura de aplicaciones grandes

## Estructura del proyecto

Flask no impone una organización específica para proyectos grandes, la manera en que se estructura una aplicación queda en manos del desarrollador.

Ejemplo básico de la estructura de una aplicación:
```
|-flasky
    |-app/
        |-templates/
        |-static/
        |-main/
            |-__init__.py
            |-errors.py
            |-forms.py
            |-views.py
        |-__init__.py
        |-email.py
        |-models.py
    |-migrations/
    |-tests/
        |-__init__.py
        |-test*.py
    |-venv/
    |-requirements.txt
    |-config.py
    |-flasky.py
```
Cuenta con cuatro carpetas de nivel superior:
- *app*: La aplicación Flask vive dentro de un paquete llamado genéricamente app.
- *migrations*: Contiene los scripts de migración de la base de datos
- *tests*: Las pruebas unitarias se escriben en un paquete de pruebas.
- *venv*: Contiene el entorno virtual de Python

También hay algunos archivos nuevos:
- *requirements.txt*: enumera las dependencias del paquete
- *config.py*: almacena los ajustes de configuración.
- *flasky.py*: define la instancia de la aplicación Flask, y también incluye algunas tareas que
ayudan a gestionar la aplicación.

## Opciones de configuración

Las aplicaciones suelen necesitar varios conjuntos de configuración. 

El siguiente muestra el archivo `config.py` que implementa una jerarquía de clases de configuración.
```python
# config.py
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googlemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in \
        ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    FLASKY_MAIL_SUBJECT_PREFIX = '[Flasky]'
    FLASKY_MAIL_SENDER = 'Flasky Admin <flasky@example.com>'
    FLASKY_ADMIN = os.environ.get('FLASKY_ADMIN')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \ 'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \ 'sqlite://'

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

- La clase base `Config` contiene ajustes que son comunes a todas las configuraciones; las diferentes subclases definen ajustes que son específicos de una configuración.
- La mayoría de los ajustes pueden ser importados opcionalmente desde las variables de entorno para una configuración flexible y más segura.
- Como una forma adicional de permitir a la aplicación personalizar su configuración, la clase `Config` y sus subclases pueden definir un método de clase `init_app()` que toma la instancia de la aplicación como un argumento.

## Paquete de aplicaciones

### Usando un 'Application Factory'


Como la aplicación se crea en el scope global, no hay forma de aplicar los cambios de configuración de forma dinámica.

La solución a este problema es retrasar la creación de la aplicación trasladándola a una función de fábrica (**Aplication Factory**) que pueda ser invocada explícitamente desde el script. Esto no sólo da tiempo al script para establecer la configuración, sino también la capacidad de crear múltiples instancias de la aplicación

```python
#  app/__init__.py
from flask import Flask, render_template 
from flask_bootstrap import Bootstrap 
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy 
from config import config

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    
    # attach routes and custom error pages here
    
    return app
```

- Primero se importan la mayoríad de las extensiones de Flask en uso, pero sin iniciarlas, esto es, no se pasan argunmentos a sus constructores. 
- La llamada a `init_app()` completa su inicialización.
- La función `create_app()` es la fábrica de la aplicación, que toma como argumento el nombre de una configuración a utilizar para la aplicación.
- El objeto de configuración se selecciona por su nombre en el diccionario de configuración.
- La función de fábrica devuelve la instancia de aplicación creada

## Implementación de la funcionalidad de la aplicación en un Blueprint

Un **blueprint** es similar a una aplicación en el sentido de que también puede definir rutas y manejadores de errores.
La diferencia es que cuando se definen en un blueprint están en estado latente hasta que el blueprint se registra en una aplicación, momento en el que pasan a formar parte de ella.

Para mayor flexibilidad, se crea en el archivo `app/main/__init__.py`:
```python
# app/main/__init__.py
from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
```
- El constructor de esta clase toma dos argumentos necesarios: el nombre del blueprint y el módulo o paquete donde se encuentra el blueprint

El blueprint se registra con la aplicación dentro de la función de fábrica `create_app()`.
```python
# app/__init__.py
def create_app(config_name):
    # ...
    
    from .main import main as 
    main_blueprint
    app.register_blueprint(main_blueprint)
    
    return app
```
```python
# app/main/errors.py
from flask import render_template
from . import main

@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500
```
- Una diferencia cuando se escriben manejadores de error dentro de un blueprint es que si se utiliza el decorador errorhandler, el manejador será invocado sólo para los errores que se originen en las rutas definidas por el blueprint.

Rutas de la aplicación dentro del blueprint `main`:
```python
# app/main/views.py
from datetime import datetime
from flask import render_template, session, redirect, url_for
from . import main
from .forms import NameForm
from .. import db
from ..models import User

@main.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        # ...
        return redirect(url_for('.index'))
    return render_template('index.html',
                            form=form, name=session.get('name'),
                            known=session.get('known', False),
                            current_time=datetime.utcnow())
```
Dos diferencias principales cuando se escribe una función de vista dentro de un blueprint:
- El decorador de la ruta proviene del blueprint, por lo que se utiliza `main.route` en lugar de `app.route`.
- El uso de la función `url_for()`.
    - Flask aplica un namespace a todos los endpoints definidos en un blueprint. El namespace es el nombre del blueprint (el primer argumento del constructor `Blueprint`) y se separa del nombre del endpoint con un punto. Por ejemplo, para la función de vista `index()` se registra entonces con el endpoint `main.index` y su URL puede obtenerse con `url_for('main.index')`.

## Script de la aplicación
El módulo `flasky.py` en el directorio de nivel superior es donde se define la instancia de la aplicación.
```python
# flasky.py
import os
from app import create_app, db
from app.models import User, Role
from flask_migrate import Migrate

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)
```
No olvidar actualizar las variables de entorno:
```bash
(venv) $ export FLASK_APP=flasky.py 
(venv) $ export FLASK_DEBUG=1
```

## Pruebas unitarias
Ejemplo de pruebas unitarias usando *unittest*:
```python
# test/test_basics.py
import unittest
from flask import current_app
from app import create_app, db

class BasicsTestCase(unittest.TestCase):  
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_app_exists(self):
        self.assertFalse(current_app is None)

    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
```
- El método `setUp()` crea una aplicación configurada para la prueba y activa su contexto. Después, crea una nueva base de datos para las pruebas utilizando el método `create_all()` de Flask- SQLAlchemy
- La primera prueba asegura que la instancia de la aplicación existe.
- La segunda prueba garantiza que la aplicación se ejecuta bajo la configuración de prueba.

Para ejecutar las pruebas unitarias, se puede añadir un comando personalizado al script flasky.py.
```python
# flasky.py
@app.cli.command()
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
```
Para ejecutar las pruebas:
```bash
(venv) $ flask test
```
## Configuración de la base de datos
La URL de la base de datos se toma de una variable de entorno como primera opción, con una base de datos SQLite por defecto como alternativa.

Independientemente del origen de la URL de la base de datos, las tablas de la base de datos deben crearse para la nueva base de datos.
```bash
(venv) $ flask db upgrade
```

## Ejecutando la aplicación
La refactorización está ahora completa, y la aplicación puede ser iniciada. Asegúrese de haber actualizado la variable de entorno `FLASK_APP`.
```bash
(venv) $ flask run
```
