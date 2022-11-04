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


