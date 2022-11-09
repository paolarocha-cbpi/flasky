# Interfaces de programación de aplicaciones (API)

**Rich Internet Applications (RIAs)**: arquitectura en donde el servidor proporciona a la aplicación cliente servicios de recuperación y almacenamiento de datos. En este modelo, el servidor se convierte en un servicio web o en una **Interfaz de Programación de Aplicaciones (API)**.

Existen varios protocolos mediante los cuales las RIA pueden comunicarse con un servicio web. Los protocolos de llamada a procedimiento remoto (RPC) o el Protocolo de Acceso a Objetos Simplificado (SOAP). Más recientemente, la arquitectura de **Transferencia de Estado Representacional (REST)** ha surgido como la favorita para las aplicaciones web.

## Introducción a REST

Seis características:
- **Cliente-servidor**: Debe haber una clara separación entre clientes y servidores.
- **Sin estado**: Una petición del cliente debe contener toda la información necesaria para llevarla a cabo. El servidor no debe almacenar ningún estado sobre el cliente que persista de una petición a la siguiente.
- **Caché**: Las respuestas del servidor pueden etiquetarse como almacenables en caché o no.
- **Interfaz uniforme**: El protocolo por el que los clientes acceden a los recursos del servidor debe ser coherente, estar bien definido y estandarizado. 
- **Sistema de capas**: Entre los clientes y los servidores se pueden intercalar servidores proxy, cachés o pasarelas.
- **Código a la carta**: Los clientes pueden descargar opcionalmente código del servidor para ejecutarlo en su contexto.

### Recursos
**Recursos**: es el núcleo del estilo arquitectónico REST. En este contexto, un recurso es un elemento de interés en el dominio de la aplicación.

Cada recurso debe tener un identificador único que lo represente. Cuando se trabaja con HTTP, los identificadores de los recursos son URLs. Una colección de todos los recursos de una clase también tiene una URL asignada.

Una API también puede definir URLs de colecciones que representen subconjuntos lógicos de todos los recursos de una clase.

### Métodos request

La aplicación cliente envía peticiones al servidor en las URL de recursos establecidas y utiliza el método de petición para indicar la operación deseada. Métodos request: `GET`, `POST`, `PUT`, `DELETE`.

### Bodies de los resquests y responses

Los recursos se envían de ida y vuelta entre el cliente y el servidor en los cuerpos de las peticiones y las respuestas, pero REST no especifica el formato a utilizar para codificar los recursos.

Los dos formatos más utilizados en los servicios web RESTful son **JavaScript Object Notation (JSON)** y **Extensible Markup Language (XML)**. Para las RIA basadas en la web, JSON resulta atractivo por ser mucho más conciso que XML.

### Versiones
Una práctica común es dar a los servicios web una versión, que se añade a todas las URLs definidas en esa versión de la aplicación del servidor.
Ejemplo: Una actualización del servicio de blogging podría cambiar el formato JSON de las entradas del blog y exponer ahora las entradas del blog como */api/v2/posts/*, manteniendo el formato JSON anterior para los clientes que se conectan a */api/v1/posts/*.

## Servicios web RESTful con Flask

- `request.get_json()`: obtener los datos de un request en formato json
- `jsonify()`: generar JSON a un response

### Creación de un Blueprint de la API
La estructura del Blueprint de la API se muestra a continuación:
```
|-flasky
    |-app/
        |-api
            |-__init__.py 
            |-users.py 
            |-posts.py 
            |-comments.py 
            |-authentication.py 
            |-errors.py 
            |-decorators.py
```

Importando todos los componentes necesarios:
```python
# app/api/__init__.py
from flask import Blueprint

api = Blueprint('api', __name__)

from . import authentication, posts, users, comments, errors
```
```python
def create_app(config_name): 
    # ...
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')
    # ...
```

### Manejo de errores
Un servicio web RESTful informa al cliente del estado de una solicitud enviando el código de estado HTTP apropiado en la respuesta y cualquier información adicional en el cuerpo de la respuesta.

Una forma de generar respuestas adecuadas para todos los clientes es hacer que los manejadores de errores adapten sus respuestas en función del formato solicitado por el cliente, una técnica denominada *negociación de contenidos*. Ejemplos:
```python
# app/api/errors.py
@main.app_errorhandler(404) def page_not_found(e):
if request.accept_mimetypes.accept_json and \ not request.accept_mimetypes.accept_html:
response = jsonify({'error': 'not found'}) response.status_code = 404
return response
return render_template('404.html'), 404
```
- Este manejador de error 404 comprueba la cabecera de solicitud `Accept`, que se decodifica en `request.accept_mimetypes` para determinar en qué formato quiere el cliente la respuesta.

```python
# app/api/errors.py
def forbidden(message):
    response = jsonify({'error': 'forbidden', 'message': message})
    response.status_code = 403
    return response
```
### Autenticación de usuarios con Flask-HTTPAuth
Dado que la arquitectura RESTful se basa en el protocolo HTTP, la *autenticación HTTP* es el método preferido para enviar las credenciales, ya sea en su modalidad Basic o Digest. Con la autenticación HTTP, las credenciales del usuario se incluyen en un encabezado `Autorization` con todas las solicitudes.

Flask-HTTPAuth es instalado con pip:
```bash
(venv) $ pip install flask-httpauth
```
```python
# app/api/authentication.py
from flask_httpauth import HTTPBasicAuth
from flask import g
from ..models import User

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(email, password):
    if email == '':
        return False
    user = User.query.filter_by(email = email).first()
    if not user:
        return False
    g.current_user = user
    return user.verify_password(password)
```
- La llamada de retorno (*callback*) de verificación devuelve `True` cuando el inicio de sesión es válido y `False` en caso contrario.
- Cuando `email` es una cadena vacía, la función devuelve `False` para bloquear la solicitud
- La *callback** de la autenticación guarda el usuario autenticado en la variable de contexto `g` de Flask para que la función de la vista pueda acceder a él más tarde.

Las respuestas de error se pueden personalizar:
```python
# app/api/authentication.py
from .errors import unauthorized, forbidden

@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')

@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and \
        not g.current_user.confirmed:
        return forbidden('Unconfirmed account')
```
- `auth.login_required`, `login_required`, `before_request` protegen las rutas
- `before_request` rechaza usuarios autenticados que no han confirmado sus cuentas

### Autenticación basada en tokens
En la autenticación basada en tokens, el cliente solicita un token de acceso enviando una solicitud que incluye las credenciales de inicio de sesión como autenticación. Por temas de seguridad, el token tiene un tiempo de expiración.
```python
# app/models.py
class User(db.Model):
    # ...
    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
                        expires_in=expiration)
        return s.dumps({'id': self.id}).decode('utf-8')
    
    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY']) 
        try:
            data = s.loads(token) 
        except:
            return None
        return User.query.get(data['id'])
```
- `generate_auth_token()` devuelve un token firmado que codifica el campo `id` del usuario.
- `verify_auth_token()` toma un token y, si es válido, devuelve el usuario almacenado en él. Este es un método estático, ya que el usuario se conocerá sólo después de decodificar el token.

Se debe modificar `verify_password` para aceptar tokens:
```python
# app/api/authentication.py
@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        g.current_user = User.verify_auth_token(email_or_token)
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token.lower()).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)
```
- Si la contraseña está vacía, se asume que el campo `email_o_token` es un token y se valida como tal. Si ambos campos no están vacíos, se asume la autenticación normal de correo electrónico y contraseña. 
- Para dar a las funciones de la vista la capacidad de distinguir entre los dos métodos de autenticación se añade una variable `g.token_used`.

La ruta que devuelve los tokens de autenticación al cliente también se añade al blueprint de la API.
```python
# app/api/authentication.py
@api.route('/tokens/', methods=['POST'])
def get_token():
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token(
        expiration=3600), 'expiration': 3600})
```
### Serialización de recursos hacia y desde JSON

El proceso de convertir una representación interna a un formato de transporte como JSON se llama **serialización**.
```python
# app/models.py
class User(db.Model, UserMixin):
    # ...
    def to_json(self):
        json_user = {
            'url': url_for('api.get_user', id=self.id),
            'username': self.username,
            'member_since': self.member_since,
            'last_seen': self.last_seen,
            'posts_url': url_for('api.get_user_posts', id=self.id),
            'followed_posts_url': url_for('api.get_user_followed_posts',
                                          id=self.id),
            'post_count': self.posts.count()
        }
        return json_user
# ...

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

    def to_json(self):
        json_post = {
            'url': url_for('api.get_post', id=self.id),
            'body': self.body,
            'body_html': self.body_html,
            'timestamp': self.timestamp,
            'author_url': url_for('api.get_user', id=self.author_id),
            'comments_url': url_for('api.get_post_comments', id=self.id),
            'comment_count': self.comments.count()
        }
        return json_post
```
La representación de un recurso ofrecida a los clientes **no** tiene por qué ser idéntica a la definición interna del modelo de base de datos correspondiente.

El proceso inverso de la serialización se llama *deserialización*. Deserializar una estructura JSON de vuelta a un modelo presenta el reto de que algunos de los datos procedentes del cliente pueden ser inválidos, erróneos o innecesarios.
```python
# app/models.py
from app.exceptions import ValidationError

class Post(db.Model):
    # ...
    @staticmethod
    def from_json(json_post):
        body = json_post.get('body')
        if body is None or body == '':
            raise ValidationError('post does not have a body')
        return Post(body=body)
```
- Si el campo del cuerpo falta o está vacío, se lanza una excepción `ValidationError`.

La clase `ValidationError` se implementa como una simple subclase de `ValueError` de Python.
```python
# app/exceptions.py
class ValidationError(ValueError):
    pass
```
Para evitar tener que añadir código de manejo de excepciones en las funciones de la vista, se puede instalar un manejador de excepciones global utilizando el decorado de `errorhandler` de Flask. 
```python
# app/api/errors.py
from app.exceptions import ValidationError
from . import api

@api.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
```
- La función decorada será invocada cada vez que se lance una excepción de la clase dada. Tener en cuenta que el decorador se obtiene del blueprint de la API, por lo que este manejador se invocará sólo cuando la ruta del blueprint sea manejada.

### Implementación de endpoints de recursos
Manejadores de recursos `GET` para los posts:

```python
# app/api/posts.py
from flask import jsonify, request, url_for
from ..models import Post
from . import api

@api.route('/posts/')
def get_posts():
    posts = Post.query.all()
    return jsonify({
        'posts': [post.to_json() for post in posts]
    })

@api.route('/posts/<int:id>')
def get_post(id):
    post = Post.query.get_or_404(id)
    return jsonify(post.to_json())
```
- La primera ruta maneja la solicitud de colección de posts.
- La segunda ruta devuelve una sola entrada del blog y responde con un error de código 404 cuando el `id` dado no se encuentra en la base de datos.

Manejador de recursos `POST` para los posts:
```python
# app/api/posts.py
@api.route('/posts/', methods=['POST'])
@permission_required(Permission.WRITE)
def new_post():
    post = Post.from_json(request.json)
    post.author = g.current_user
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json()), 201, \
        {'Location': url_for('api.get_post', id=post.id)}
```
- `permission_required`: garantiza que el usuario autentificado tiene permiso para escribir entradas en el blog.
- Se crea un blog a partir de los datos JSON y su autor se asigna explícitamente como usuario autentificado
- Se devuelve un código de estado 201 y se añade una cabecera `Location` con la URL del recurso recién creado.

Implementación del decorador `permission_required`:
```python
# app/api/decorators.py
from functools import wraps
from flask import g
from .errors import forbidden

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not g.current_user.can(permission):
                return forbidden('Insufficient permissions')
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```
Manejador de recursos `PUT` para los posts:
```python
# app/api/posts.py
@api.route('/posts/<int:id>', methods=['PUT'])
@permission_required(Permission.WRITE)
def edit_post(id):
    post = Post.query.get_or_404(id)
    if g.current_user != post.author and \
            not g.current_user.can(Permission.ADMIN):
        return forbidden('Insufficient permissions')
    post.body = request.json.get('body', post.body)
    db.session.add(post)
    db.session.commit()
    return jsonify(post.to_json())
```
- Para permitir que un usuario edite una entrada del blog, la función también debe garantizar que el usuario es el autor de la entrada o bien es un administrador

### Pruebas de servicios web con HTTPie
Los dos clientes más utilizados para probar los servicios web de Python desde la línea de comandos son cURL y HTTPie:
```bash
(venv) $ pip install httpie
```
Suponiendo que el servidor de desarrollo se está ejecutando en la dirección por defecto http://127.0.0.1:5000
se puede realizar una petición `GET` desde otra ventana de terminal de la siguiente manera:
```bash
(venv) $ http --json --auth <email>:<password> GET \
> http://127.0.0.1:5000/api/v1/posts
```
El siguiente comando envía una petición `POST` para añadir una nueva entrada en el blog:
```bash
(venv) $ http --auth <email>:<password> --json POST \
> http://127.0.0.1:5000/api/v1/posts/ \
> "body=I'm adding a post from the *command line*."
```
Para utilizar tokens de autenticación en lugar de un nombre de usuario y una contraseña, se envía primero una solicitud `POST`
a */api/v1/tokens/*:
```bash
(venv) $ http --auth <email>:<password> --json POST \
> http://127.0.0.1:5000/api/v1/tokens/
```
