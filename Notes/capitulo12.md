# Seguidores

## Relaciones entre bases de datos

### Relaciones muchos-a-muchos

Consideremos el ejemplo clásico de una relación de muchos a muchos: una base de datos de estudiantes y las clases a las que asisten. Está claro que no se puede añadir una clave externa a una clase en la tabla de alumnos, porque un alumno asiste a muchas clases: una clave externa no es suficiente. Del mismo modo, no se puede añadir una clave externa a un estudiante en la tabla de clases, porque las clases tienen más de un estudiante. Ambas partes necesitan una lista de claves foráneas.

La solución es añadir una tercera tabla a la base de datos, denominada **tabla de asociación**. 

Con SQLAchemy, esto se ve de la siguiente forma:
```python
registrations = db.Table('registrations',
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('class_id', db.Integer, db.ForeignKey('classes.id'))
)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    classes = db.relationship('Class',
                                secondary=registrations,
                                backref=db.backref('students', lazy='dynamic'),
                                lazy='dynamic')


class Class(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
```
- La relación se define con `db.relationship()`, pero en el caso de una relación muchos a muchos el argumento `secondary` debe establecerse en la tabla de asociación. 
- La relación puede definirse en cualquiera de las dos clases, y el argumento `backref` se encarga también de exponer la relación desde el otro lado. 
- La tabla de asociación se define como una **tabla simple**, no como un modelo, ya que SQLAlchemy gestiona esta tabla internamente.

### Relaciones autorreferenciales

Una relación en la que ambas partes pertenecen a la misma tabla se dice que es **autorreferencial**. Este es el caso para los seguidores de la aplicación Flasky.

### Relaciones múltiples avanzadas

Existe una limitación con la tabla de asociación ya que al ser una tabla interna manejada por SQLAlchemy no permite almacenar información adicional. Para este caso, es necesario que la tabla de asociación se elabore su propio modelo.

```python
# app/models.py
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
```
- No es necesario configurar manualmente el campo de fecha y hora porque se ha definido con un valor por defecto que establece la fecha y hora actuales

La relación de muchos-a-muchos debe descomponerse en las dos relaciones básicas de uno-a-muchos:
```python
class User(UserMixin, db.Model):
    # ...
    followed = db.relationship('Follow',
                            foreign_keys=[Follow.follower_id],
                            backref=db.backref('follower', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
    followers = db.relationship('Follow',
                            foreign_keys=[Follow.followed_id],
                            backref=db.backref('followed', lazy='joined'),
                            lazy='dynamic',
                            cascade='all, delete-orphan')
```
- Las relaciones de `followed` y `followers` se definen como relaciones individuales uno a muchos. 
- Es necesario eliminar cualquier ambigüedad entre llaves foráneas especificando en cada relación qué llave foránea utilizar mediante `foreign_keys`. 
- Los argumentos de `db.backref()` de estas relaciones no se aplican entre sí; las referencias se aplican al modelo `Follow`.
- El argumento `lazy` se especifica como `joined` lo que hace que el objeto relacionado se cargue inmediatamente desde la consulta join
- El argumento `cascade` configura cómo las acciones realizadas sobre un objeto padre se propagan a los objetos relacionados.

Métodos para controlar las relaciones:
```python
# app/modesl.py
class User(UserMixin, db.Model):
    # ...
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None
```

## Seguidores en la página de perfil

Se agregan botones de "Follow" y "Unfollow", al igual que el conteo de seguidores.
```html
{% if current_user.can(Permission.FOLLOW) and user != current_user %}
    {% if not current_user.is_following(user) %}
    <a href="{{ url_for('.follow', username=user.username) }}"
        class="btn btn-primary">Follow</a> {% else %}
    <a href="{{ url_for('.unfollow', username=user.username) }}"
        class="btn btn-default">Unfollow</a>
    {% endif %}
{% endif %}
<a href="{{ url_for('.followers', username=user.username) }}">
    Followers: <span class="badge">{{ user.followers.count() }}</span>
</a>
<a href="{{ url_for('.followed_by', username=user.username) }}">
    Following: <span class="badge">{{ user.followed.count() }}</span>
</a>
{% if current_user.is_authenticated and user != current_user and
    user.is_following(current_user) %}
| <span class="label label-default">Follows you</span>
{% endif %}
```

Esta plantilla utiliza 4 nuevos endpoints. La ruta `/follow/<user-name>` se invoca al dar click en el botón "Follow":
```python
# app/main/views.py
@main.route('/follow/<username>')
@login_required 
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index')) 
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))
```
- Se trae el usuario solicitado, se verifica que es válido y que no está ya seguido por el usuario conectado, y luego llama a la función `follow()` en el modelo `User` para establecer el enlace. 
- La ruta `/unfollow/<username>` se implementa de forma similar.

La ruta `/followers/<nombredeusuario>` se invoca cuando un usuario hace clic en el conteo de seguidores.

```python
# app/main/views.py
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page=page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
                for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                            endpoint='.followers', pagination=pagination,
                            follows=follows)
```
- Esta función carga y valida el usuario solicitado y enpagina su relación `followers`.
- Como la consulta de seguidores devuelve instancias `Follow`, la lista se convierte en otra lista que tiene campos `user` y `timestamp` en cada entrada para que la renderización sea más sencilla.

## Consulta de post de personas seguidas

Como característica adicional, se da la opción de que el usuario vea posts de solo usuarios que sigue.

Sin embargo, las consultas caen en el problema comúnmente conocido como "problema N+1", ya que al trabajar con la base de datos de esta forma requiere realizar N+1 consultas a la base de datos, siendo N el número de resultados devueltos por la primera consulta.

Para hacer la consulta, se hace una consulta join. Para obtener la lista de posts de los usuarios seguidos, las tablas `posts`y `follows` necesitan combinarse:
```python
return db.session.query(Post).select_from(Follow).\
    filter_by(follower_id=self.id).\
    join(Post, Follow.followed_id == Post.author_id)
```
- `db.session.query(Post)` especifica que se trata de una consulta que devuelve objetos `Post`.
- `select_from(Follow)` indica que la consulta comienza con el modelo `Follow`.
- `filter_by(follower_id=self.id)` realiza el filtrado de la tabla `follows` por
el usuario seguidor.
- `join(Post, Follow.followed_id == Post.author_id)` une los resultados de `filter_by`() con los objetos `Post`.

La query anterior puede ser simplificada:
```python 
# app/models.py
class User(db.Model):
    # ...
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)
```
- `followed_posts()` se define como una propiedad para que no necesita el `()`

## Mostrar las entradas de usuarios seguidos en la página de inicio

La página de inicio ahora permite a los usuarios ver todas las entradas del blog o sólo las de los usuarios seguidos.
```python
# app/main/views.py
@main.route('/', methods = ['GET', 'POST'])
def index():
    # ...
    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    pagination = query.order_by(Post.timestamp.desc()).paginate(
            page=page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
    error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, show_followed=show_followed, pagination=pagination)
```
- La opción de mostrar todos los mensajes o los seguidos se almacena en una cookie llamada `show_followed` que, cuando se establece en una cadena no vacía, indica que sólo se deben mostrar los mensajes seguidos.
- Las cookies se almacenan en el objeto request como un diccionario `request.cookies`. 
- Para mostrar todas las entradas, se utiliza la consulta de nivel superior `Post.query`, y la propiedad recientemente añadida `User.followed_posts` cuando la lista debe restringirse a los usuarios seguidos

La cookie `show_followed` se establece en dos nuevas rutas
```python
# app/main/views.py
@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60) # 30 days
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60) # 30 days
    return resp
```
- Las cookies sólo se pueden establecer en un objeto response, por lo que estas rutas necesitan crear un objeto response a través de `make_response()` en lugar de dejar que Flask lo haga.
- La función `set_cookie()` toma el nombre y el valor de la cookie como los dos primeros argumentos. El argumento opcional `max_age` establece el número de segundos hasta que expira la cookie.

Para poder ver las publicaciones propias del usuario en la pestaña "Followed", se agrega lo siguiente:
```python
# app/models.py
class User(UserMixin, db.Model): 
    # ...
    def __init__(self, **kwargs):
        # ...
        self.follow(self)

    # ...
    @staticmethod
    def add_self_follows():
        for user in User.query.all():
        if not user.is_following(user):
            user.follow(user)
            db.session.add(user)
            db.session.commit()
    # ...
```
- Los números necesitan ser disminuidos en uno para ser precisos, lo que es fácil de hacer directamente en la plantilla: `{{ user.followers.count() - 1 }}` y `{{ user.followed.count() - 1 }}`. 


