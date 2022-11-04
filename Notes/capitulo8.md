# Autentificación de usuarios

**Autenticación**: proceso por el cual se hace reconocimiento de una entiendad

## Extensiones de autenticación para Flask

Para este capítulo se estarán empleando 3 extensiones principales para la autenticación de usuarios:
- Flask-Login: Gestión de las sesiones de los usuarios que han iniciado sesión
- Werkzeug: Hashing y verificación de contraseñas
- itsdangerous: Generación y verificación de tokens criptográficamente seguros

## Seguridad de las contraseñas

La clave para almacenar las contraseñas de los usuarios de forma segura en una base de datos se basa en no almacenar la contraseña en sí, sino un **hash** de la misma. Con esto:
- Una función de hashing de contraseñas toma una contraseña como entrada, le añade un componente aleatorio y luego le aplica varias transformaciones criptográficas de un solo sentido.
- El resultado es una nueva secuencia de caracteres que no tiene forma conocida de volver a ser transformada en la contraseña original pero sí pueden ser verificados

## Cifrado de contraseñas con Werkzeug

Dos funciones principales:
- `generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)`:
toma una contraseña de texto plano y devuelve el hash de la contraseña 
- `check_password_hash(hash, password)`:
toma un hash de contraseña previamente almacenado en la base de datos y la contraseña introducida por el usuario. Un valor de retorno de True indica que la palabra de paso del usuario es correcta.

```python
# app/models.py
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    # ...
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
```
- Cuando se establece la propiedad `password`, el método setter llamará a la función `generate_password_hash()` y escribirá el resultado en el campo `password_hash`
- El intento de leer la propiedad de la contraseña devolverá un error
- El método `verify_password()` toma una contraseña y la pasa a la función `check_password_hash()` para verificarla con la versión hash almacenada en el modelo de usuario. 

> El decorador `@property`puede ser usado sobre un método, que hará que actúe como si fuera un atributo. Existen varios añadidos al decorador `@property` como pueden ser el `setter`. Se trata de otro decorador que permite definir un “método” que modifica el contenido del atributo que se esté usando. [Fuente](https://ellibrodepython.com/decorador-property-python)

Se pueden aplicar las siguientes pruebas unitarias:
```python
# test/test_user_model.py
import unittest
from app.models import User

class UserModelTestCase(unittest.TestCase):
    def test_password_setter(self):
    u = User(password = 'cat')
    self.assertTrue(u.password_hash is not None)
    
    def test_no_password_getter(self):
    u = User(password = 'cat')
    with self.assertRaises(AttributeError):
        u.password

    def test_password_verification(self):
        u = User(password = 'cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))
    
    def test_password_salts_are_random(self):
    u = User(password='cat')
    u2 = User(password='cat')
    self.assertTrue(u.password_hash != u2.password_hash)
```
Para ejecutar las pruebas:
```bash
(venv) $ flask test
```

## Creación de un Blueprint de autenticación

El uso de diferentes blueprints para diferentes subsistemas de la aplicación es una excelente manera de mantener el código ordenado. Por eso, se creará un blueprint para la autenticación de usuarios.

```python
# app/auth/__init__.py
from flask import Blueprint

auth = Blueprint('auth', __name__)

from . import views
```

```python
# app/auth/views.py
from flask import render_template
from . import auth

@auth.route('/login')
def login():
    return render_template('auth/login.html')
```
- El archivo de plantilla que se le da a `render_template()` se almacena dentro del directorio `auth`. Este directorio debe ser creado dentro de `app/templates`.

```python
# app/__init__.py
def create_app(config_name):
    # ...
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    return app
```

## Autenticación de usuarios con Flask-Login
Flask-Login es una extensión para la gestión de un sistema de autenticación de usuarios.
```bash
(venv) $ pip install flask-login
```

### Preparación del modelo de usuario para los inicios de sesión

Propiedades y métodos comunes de Flask-Login:
- `is_authenticated`: Debe ser `True` si el usuario tiene credenciales de acceso válidas o `False` en caso contrario.
- `es_active`: Debe ser `True` si el usuario tiene permitido para iniciar sesión o `False`en caso contrario. Un valor `False` puede ser utilizado para deshabilitar cuentas.
- `is_anonymous`: Debe ser `False` para usuarios regulares y `True` para un usuario especial que representa usuarios anónimos.
- `get_id()`: Debe devolver un identificador único para el usuario, codificado como una cadena Unicode.

Flask-Login proporciona una clase `UserMixin` que tiene implementaciones por defecto que son apropiadas para la mayoría de los casos. 
```python
# app/models.py
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
```
```python
# app/__init__.py
from flask_login import LoginManager 

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_name):
    # ...
    login_manager.init_app(app)
    # ...
```
- El atributo `login_view` del objeto `LoginManager` establece el endpoint de la página de inicio de sesión. Flask-Login redirigirá a la página de inicio de sesión cuando un usuario anónimo intente acceder a una página protegida. 

Flask-Login requiere que la aplicación designe una función para ser invocada cuando la extensión necesite cargar un usuario desde la base de datos dado su identificador.
```python
# app/models.py
from . import login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```
- El decorador `login_manager.user_loader` se utiliza para registrar la función con Flask-Login, que la llamará cuando necesite recuperar información sobre el usuario conectado

### Protegiendo rutas
Para proteger una ruta de modo que sólo puedan acceder a ella los usuarios autentificados, Flask-Login proporciona un decorador `login_required`.

### Añadiendo un formulario de inicio de sesión
```python
# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField 
from wtforms.validators import DataRequired, Length, Email

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')
```
- La clase `PasswordField` representa un elemento `<input>` con `type="password"`. La clase BooleanField representa una casilla de verificación.

Para agregar en la barra de navegación los enlaces de "Log In" o "Log Out"
```html
<!-- app/templates/base.html -->
<ul class="nav navbar-nav navbar-right">
    {% if current_user.is_authenticated %}
    <li><a href="{{ url_for('auth.logout') }}">Log Out</a></li>
    {% else %}
    <li><a href="{{ url_for('auth.login') }}">Log In</a></li>
    {% endif %}
</ul>
```
### Inicio de sesión de los usuarios
```python
# app/auth/views.py
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user
from . import auth
from ..models import User
from .forms import LoginForm

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
                return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)
```
- Cuando la petición es de tipo `GET`, se renderiza la plantilla, que a su vez muestra el formulario.
- Cuando el formulario se envía en una solicitud `POST`, la función `validate_on_submit()` valida las variables del formulario e intenta iniciar la sesión del usuario.
- Si el formulario de inicio de sesión se presentó al usuario para evitar el acceso no autorizado a una URL protegida que el usuario quería visitar, entonces Flask-Login habrá guardado esa URL original en el argumento `next`, al que se puede acceder desde el diccionario `request.args`. Si el argumento `next`  no está disponible, se emite en su lugar una redirección a la página de inicio.

```html
<!-- app/templates/auth/login -->
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Flasky - Login{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Login</h1>
</div>
<div class="col-md-4">
    {{ wtf.quick_form(form) }}
</div>
{% endblock %}
```
### Cierre de sesión de los usuarios
```python
# app/auth/views.py
from flask_login import logout_user, login_required

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.') 
    return redirect(url_for('main.index'))
```
- Se elimina y reinicia la sesión del usuario.

## Registro de nuevos usuarios
### Añadir un formulario de registro de usuario
```python
# app/auth/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField 
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
               'Usernames must have only letters, numbers, dots or '
               'underscores')])
    password = PasswordField('Password', validators=[
        DataRequired(), EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Confirm password', validators=[DataRequired()])
    submit = SubmitField('Register')
    
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
    
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
```
- Validador `Regexp` de WTForms para asegurar que el campo de nombre de usuario comienza con una letra y sólo contiene letras, números, guiones bajos y puntos

```html
<!-- app/templates/auth/login.html -->
<p>
    New user?
    <a href="{{ url_for('auth.register') }}">
        Click here to register
    </a>
</p>
```
### Registrando nuevos usuarios
```python
# app/auth/views.py
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now login.')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)
```
## Confirmación de la cuenta
Las cookies de la sesión de usuario contienen una firma criptográfica generada por un paquete llamado `itsdangerous`. Si se altera el contenido de la sesión de usuario, la firma dejará de coincidir con el contenido, por lo que Flask descarta la sesión e inicia una nueva. 

El paquete `itsdangerous` proporciona varios tipos de generadores de tokens. Entre ellos, la clase `TimedJSONWebSignatureSerializer` genera JSON Web Signatures (JWSs) con un tiempo de expiración.

> `TimedJSONWebSignatureSerializer` esta obsoleto. Para instalar la versión que se emplea en el libro, hay que hacerle un downgrade: `pip install itsdangerous==2.0.1`.

```python
# app/models.py
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from . import db

class User(UserMixin, db.Model):
    # ...
    confirmed = db.Column(db.Boolean, default=False)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration) 
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8')) 
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True
```
- El constructor de `TimedJSONWebSignatureSerializer` toma como argumento una clave de cifrado, que puede ser la `SECRET_KEY` configurada
- `dumps()` genera una firma criptográfica para los datos y luego serializa.
- `expires_in` establece un tiempo de expiración para el token, expresado en segundos
- `loads()` que toma el token como único argumento para decodificarlo
- Cuando el método `loads()` recibe un token no válido o un token válido que ha ca
- `confirm()` verifica el token y, si es válido, establece el nuevo atributo confirmed en el modelo de usuario como `True`.


