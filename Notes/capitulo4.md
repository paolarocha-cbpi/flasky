# Formularios web

Con HTML es posible crear formularios web, en los que los usuarios pueden introducir información. Los datos del formulario son enviados por el navegador web al servidor, normalmente en forma de solicitud POST.

La extensión Flask-WTF hace que trabajar con formularios web sea una experiencia mucho más agradable. Para instalarla:
```bash
(venv) $ pip install flask-wtf
```


## Configuración

A diferencia de la mayoría de las extensiones, Flask-WTF no necesita ser inicializado a nivel de aplicación, pero espera que la aplicación tenga configurada una *clave secreta*. Una clave secreta es una cadena con cualquier contenido aleatorio y único que se utiliza como clave de cifrado o de firma para mejorar la seguridad de la aplicación de varias maneras. 

Esta clave secreta forma parte del mecanismo que la extensión utiliza para proteger todos los formularios contra los ataques de falsificación de solicitudes entre sitios (CSRF). Un ataque CSRF se produce cuando un sitio web malicioso envía peticiones al servidor de aplicaciones en el que el usuario está conectado en ese momento.


Ejemplo de configuración:
```python
app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
```

## Clases de formularios

Cuando se utiliza Flask-WTF, cada formulario web está representado en el servidor por una clase que hereda de la clase `FlaskForm`. La clase define la lista de campos del formulario, cada uno representado por un objeto. Cada objeto de campo puede tener uno o más validadores adjuntos. Un validador es una función que comprueba si los datos enviados por el usuario son válidos.

Ejemplo:
```python
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')
```

## Renderización HTML de los formularios

Ejemplo simple de formulario HTML:

```html
<form method="POST">
    {{ form.hidden_tag() }}
    {{ form.name.label }} {{ form.name() }}
    {{ form.submit() }}
</form>
```

La extensión Flask-Bootstrap proporciona una función de ayuda de alto nivel que renderiza un formulario Flask-WTF completo utilizando los estilos de formulario predefinidos de Bootstrap, todo con una sola llamada. Usando Flask-Bootstrap, el formulario puede ser renderizado como sigue:

```html
{% import "bootstrap/wtf.html" as wtf %}
{{ wtf.quick_form(form) }}
```

## Manejo de formularios en funciones de vista
Se añade el argumento `methods` al decorador `app.route` para indicar a Flask que registre la función de vista como gestor de peticiones `GET` y `POST` en el mapa de URL. Si no se da el argumento methods, la función de vista se registra para manejar sólo las solicitudes `GET`. Añadir `POST` a la lista de métodos es necesario porque los envíos de formularios se manejan mucho más convenientemente como peticiones `POST`.

Ejemplo:
```python
@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    form = NameForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
return render_template('index.html', form=form, name=name)
```
- El método `validate_on_submit()` del formulario devuelve `True` cuando el formulario fue enviado y los datos fueron aceptados por todos los validadores de campos.
- En todos los demás casos, `validate_on_submit()` devuelve `False`.


## Redirecciones y sesiones de usuario
Cuando la última petición enviada es una solicitud `POST` con datos de formulario, una actualización provocaría un envío duplicado del formulario, que en casi todos los casos no es la acción deseada. Esto sucede porque los navegadores repiten la última solicitud que enviaron cuando se les pide que actualicen una página.

Es buena práctica no dejar una petición `POST` como el último request enviado por el navegador. Para solucionar esto, se realiza un *redirect* en lugar de enviar una respuesta normal. Una redirección es un tipo especial de respuesta que contiene una URL en lugar de una cadena con código HTML. Cuando el navegador recibe una respuesta de redirección, emite una petición `GET` para la URL de redirección, y esa es la página que muestra. Esto se conoce como el ***patrón Post/Redirect/Get***

Sin embargo, esto conlleva otro problema y es que tan pronto como esa petición termina los datos del formulario se pierden.

Las aplicaciones pueden "recordar" cosas de una solicitud a la siguiente almacenándolas en la *sesión del usuario*, un almacenamiento privado que está disponible para cada cliente conectado.

Ejemplo:
```python
@app.route('/', methods=['GET', 'POST']) 
def index():
    form = NameForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form=form, name=session.get('name'))
```
- Al igual que con los diccionarios normales, el uso de `get()` para solicitar una clave del diccionario evita una excepción para las claves que no se encuentran. El método `get()` devuelve un valor por defecto de `None` para una clave faltante.

## Message Flashing
A veces es útil dar al usuario una actualización del estado después de completar una solicitud. Puede ser un mensaje de confirmación, una advertencia o un error. Para esto, se utiliza la función `flash()`. Ejemplo:
```python
from flask import Flask, render_template, session, redirect, url_for, flash
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks like you have changed your name!')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html', form = form, name = session.get('name'))
```
Flask pone a disposición de las plantillas una función `get_flashed_messages()` para recuperar los mensajes y renderizarlos. Ejemplo:
```html
{% block content %}
<div class="container">
    {% for message in get_flashed_messages() %}
    <div class="alert alert-warning">
        <button type="button" class="close" data-dismiss="alert">&times;</button>
        {{ message }}
    </div>
    {% endfor %}
    
    {% block page_content %}{% endblock %}
</div>
{% endblock %}
```
- Los mensajes que se recuperan de `get_flashed_messages()` no se devolverán la próxima vez que se llame a esta función, por lo que los mensajes flash aparecen sólo una vez y luego se descartan.