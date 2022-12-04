# Entradas del blog

## Presentación y visualización de publicaciones en el blog

Se hacen cambios en la base de datos para almacenar las publicaciones:

```python
# app/models.py
class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class User(UserMixin, db.Model):
    # ...
    posts = db.relationship('Post', backref='author', lazy='dynamic')
```
- La entrada del blog se encuentra representado por un cuerpo, un timestamp y una relación uno-a-muchos con el modelo `User`.
- El campo `body` se define de tipo `db.Text` para que no haya limitaciones en la longitud del texto.

Se agrega un formulario en la página principal en el que se puedan ingresar nuevas publicaciones.

```python
# app/main/forms.py
class PostForm(FlaskForm):
    body = TextAreaField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')
```

La función de vista `index()` contiene el formulario y pasa la lista de publicaciones anteriores a la plantilla:
```python
# app/main/views
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))
    posts = Post.query.order_by(Post.timestamp.desc()).all()
    return render_template('index.html', form=form, posts=posts)
```

- El atributo `author` se determina con la expresión `current_user._get_current_object()`. La base de datos necesita un objeto del usuario real, el cual se obtiene llamando `_get_current_object()` sobre el objeto proxy.

## Entradas de blog en las páginas de perfil

La página de perfil de usuario puede mostrar los posts publicados por el usuario.
```python
# app/main/<username>
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)
```

Para evitar repetir la etiqueta `<ul>` de HTML dentro del archivo *index.html*, se crea el archivo *_posts.html* que la contenga. Este código se puede reutilizar con la directiva `include`de Jinja2.

```html
<!-- app/templates/user.html -->
...
<h3>Posts by {{ user.username }}</h3>
{% include '_posts.html' %}
...
```

## Paginación para posts extensos

Para evitar que la página tarde en cargar y en renderizar, la solución es paginar los datos y renderizarlos en trozos.

### Creando datos de publicaciones falsos

Se utiliza la librería *Fake* para la creación de datos másivo de publicaciones.
```bash
(venv) $ pip install faker
```

Para generar, crear el siguiente script:
```python
from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post


def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        u = User(email=fake.email(),
                username=fake.user_name(),
                password='password',
                confirmed=True,
                name=fake.name(),
                location=fake.city(),
                about_me=fake.text(),
                member_since=fake.past_date())
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(body=fake.text(),
                timestamp=fake.past_date(),
                author=u)
        db.session.add(p)
    db.session.commit()
```

A través de la terminal se crean los datos:
```bash
(venv) $ flask shell 
>>> from app import fake >>> fake.users(100)
>>> fake.posts(100)
```

NOTA: En este paso es importante asegurarse que todos los posts tengan un usuario registrado en la tabla `users`.

### Renderizando en páginas

Cambios en la página de inicia para que soporte paginación:

```python
# app/main/views.py
@main.route('/', methods=['GET', 'POST'])
def index():
    # ...
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.order_by(Post.timestamp.desc()).paginate(page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)
```
- El número de página a renderizar se obtiene del `request.args`. Por default, se pasa a la primera página.
- El método `paginate()` toma el número de página como su primer y único argumento requerido. 
- El argumento opcional `error_out` puede establecerse como `True` (por defecto) para emitir un error de código 404 cuando se solicite una página fuera del rango válido. Si `error_out` es `False`, las páginas fuera del rango válido se devuelven con una lista de elementos vacía. 
- Para que el tamaño de las páginas sea configurable, el valor del argumento `per_page` se lee de una variable de configuración `FLASKY_POSTS_PER_PAGE` que se añade en *config.py*.

### Añadiendo un widget de paginación

`paginate()` es un objeto de la clase Pagination, una clase definida por Flask-SQLAlchemy. Este objeto contiene varias propiedades que son útiles para generar enlaces de página en una plantilla, por lo que se pasa a la plantilla como argumento.

## Mensajes de texto enriquecido con Markdown y Flask-PageDown

En esta sección se mostrará cómo añadir soporte a entradas extensas. Primero, se instalan las librerías necesarias:
```bash
(venv) $ pip install flask-pagedown markdown bleach
```

### Usando Flask-PageDown

Flask-PageDown necesita ser inicializado.
```python
# app/__init__.py
from flask_pagedown import PageDown
# ...
pagedown = PageDown()
# ...
def create_app(config_name): 
    # ...
    pagedown.init_app(app)
    # ...
```

Para soportar texto con Markdown, el campo `body` de `PostForm` debe ser cambiado a `PageDownField`.
```python
# app/main/forms.py
class PostForm(FlaskForm):
    body = PageDownField("What's on your mind?", validators=[DataRequired()])
    submit = SubmitField('Submit')
```

Agregando una vista previa del markdown:
```html
<!-- app/templates/index.html -->
{% block scripts %}
{{ super() }}
{{ pagedown.include_pagedown() }}
{% endblock %}
```

### Manejo del texto enriquecido en el servidor

Cuando se envía el formulario, sólo se envía el texto Markdown sin procesar con la solicitud `POS`; la vista previa HTML que se muestra en la página se descarta.

Para evitar cualquier riesgo de seguridad, sólo se envía el texto fuente Markdown, y una vez en el servidor se convierte de nuevo a HTML utilizando Markdown, un convertidor de Markdown a HTML de Python. El HTML resultante se "depura" con Bleach para garantizar que sólo se utiliza una lista corta de etiquetas HTML permitidas.

```python
# app/models.py
from markdown import markdown import bleach
class Post(db.Model): 
    # ...
    body_html = db.Column(db.Text)
    # ...
    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

db.event.listen(Post.body, 'set', Post.on_changed_body)
```
- La función `on_changed_body()` está registrada como receptor del evento "set" para body, lo que significa que será invocada automáticamente cada vez que el campo body se establezca con un nuevo valor. La función renderiza la versión HTML del cuerpo y la almacena en `body_html`.

Reemplazando `post.body` con `post.body_html` en las plantillas:

```html
<!-- app/templates/_posts.html -->
...
<div class="post-body">
{% if post.body_html %}
        {{ post.body_html | safe }}
    {% else %}
        {{ post.body }}
    {% endif %}
</div>
...
```

## Enlaces permanentes a publicaciones del blog

Función de vista que soporta enlances permanentes para las publicaciones.
```python
# app/main/views.py
@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])
```

Los enlaces permanentes se agregan al final de cada post.
```html
<!-- app/templates/_posts.html -->
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        ...
        <div class="post-content">
            ...
            <div class="post-footer">
                <a href="{{ url_for('.post', id=post.id) }}">
                    <span class="label label-default">Permalink</span>
                </a>
            </div>
        </div>
    </li>
    {% endfor %}
</ul>
```
Se crea una nueva plantilla para *post.html*
```html
<!-- app/templates/post.html -->
{% extends "base.html" %}

{% block title %}Flasky - Post{% endblock %}

{% block page_content %}
{% include '_posts.html' %}
{% endblock %}
```

## Editor de publicaciones

Finalmente, para la función de editar publicaciones publicaciones de los usuarios se crea su plantilla y función de vista:

```html
<!-- app/templates/edit_post.html -->
{% extends "base.html" %}
{% import "bootstrap/wtf.html" as wtf %}

{% block title %}Flasky - Edit Post{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>Edit Post</h1>
</div>
<div>
    {{ wtf.quick_form(form) }}
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
{{ pagedown.include_pagedown() }}
{% endblock %}
```

```python
# app/main/views.py
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)
```
- Esta función de vista solo permie que el autor de una entrada del blog pueda editarla, excepto los administradores, que pueden editar las entradas de todos los usuarios.
- Si un usuario intenta editar una entrada de otro usuario, la función de vista responde con un código 403.

Añadiendo el link permanent:
```html
app/templates/_posts.html
<ul class="posts">
    {% for post in posts %}
    <li class="post">
        ...
        <div class="post-content">
            ...
            <div class="post-footer">
                ...
                {% if current_user == post.author %}
                <a href="{{ url_for('.edit', id=post.id) }}">
                    <span class="label label-primary">Edit</span>
                </a>
                {% elif current_user.is_administrator() %}
                <a href="{{ url_for('.edit', id=post.id) }}">
                    <span class="label label-danger">Edit [Admin]</span>
                </a>
                {% endif %}
            </div>
        </div>
    </li>
    {% endfor %}
</ul>
```


