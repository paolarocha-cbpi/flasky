# Periles de usuario

## Información del perfil
Se extiende el modelo `User` para almacenar más información del usuario:

```python
# app/models.py
class User(UserMixin, db.Model):
    # ...
    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
```
- La diferencia entre `db.String` y `db.Text` es que `db.Text`es longitud variable por que no se necesita especificar una longitud máxima.
- `datetime.utcnow` no lleva los paréntesis `()` debido a que el argumento `default` acepta funciones como valor.

Para el caso del campo `last_seen`, es necesario actualizarlo cada vez que el usuario ingrese al sitio.

```python
# app/models.py
class User(UserMixin, db.Model): 
    # ...

    def ping(self):
    self.last_seen = datetime.utcnow()
    db.session.add(self)
    db.session.commit()
```

```python
# app/auth/views.py
@auth.before_app_request
def before_request():
    if current_user.is_authenticated :
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))
```
- `before_app_request` se ejecuta antes de cada request

## Página de perfil de usuario

```python
# app/main/views.py:
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)
```
```html
<!-- app/templates/user.html -->
{% extends "base.html" %}
{% block title %}Flasky - {{ user.username }}{% endblock %}

{% block page_content %}
<div class="page-header">
    <h1>{{ user.username }}</h1>
    {% if user.name or user.location %}
    <p>
        {% if user.name %}{{ user.name }}{% endif %}
        {% if user.location %}
            From <a href="http://maps.google.com/?q={{ user.location }}">
                {{ user.location }}
            </a>
        {% endif %}
    </p>
    {% endif %}
    {% if current_user.is_administrator() %}
    <p><a href="mailto:{{ user.email }}">{{ user.email }}</a></p>
    {% endif %}
    {% if user.about_me %}<p>{{ user.about_me }}</p>{% endif %}
    <p>
        Member since {{ moment(user.member_since).format('L') }}.
        Last seen {{ moment(user.last_seen).fromNow() }}.
    </p>
</div>
{% endblock %}
```
- El campo `location` del usuario se presenta como un enlace a una consulta de Google Maps, de modo que al hacer clic en él se abre un mapa centrado en la ubicación.

```html
 <!-- app/templates/base.html -->
{% if current_user.is_authenticated %}
<li>
    <a href="{{ url_for('main.user', username=current_user.username) }}">
        Profile
    </a>
</li>
{% endif %}
```

## Editar perfil

### Editor de perfil a nivel de User
Páginas donde el usuario entra información acerca de sí mismo es necesario agregar. Se crea el form:
```python
# app/main/forms.py
class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')
```
- Notar que los campos son opcionales, la longitud del validador tiene como mínimo cero. Para agregar la ruta:
```python
# app/main/views.py
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)
```

### Editor de perfil a nivel Administrator

Para el perfil de administrador, se agregan 3 campos adicionales a editar: email, username y estatus de confirmado del usuario.

```python
#
class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    username = StringField('Username', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
            'Usernames must have only letters, numbers, dots or '
            'underscores')])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                            for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use.')
```



