# Plantillas

Una plantilla es un archivo que contiene el texto de una respuesta, con variables de marcador de posición para las partes dinámicas que sólo se conocerán en el contexto de una solicitud. El proceso que reemplaza las variables con valores reales y devuelve una cadena de respuesta final se llama *renderización*. Para la tarea de renderizar las plantillas, Flask utiliza un potente motor de plantillas llamado *Jinja2*.

## Motor de plantillas de Jinja2

Una plantilla Jinja2 es un archivo que contiene el texto de una respuesta.

```html
<h1>Hello World!</h1>
```

También se pueden usar respuestas con los componentes dinámicos.
```html
<h1>Hello, {{ name }}!</h1>
```

El constructor `{{ nombre }}` hace referencia a una **variable**, un marcador de posición especial que indica al motor de la plantilla que el valor que va en ese lugar debe obtenerse a partir de los datos proporcionados en el momento en que se renderiza la plantilla.
Jinja2 reconoce variables de cualquier tipo, incluso tipos complejos como listas, diccionarios y objetos.

Las variables se pueden modificar a través de filtros a través de un pipe `|`, por ejemplo

```html
Hello, {{ name|capitalize }}
````

Los filtros más comunes se muestran en la siguiente tabla:

| Filter name | Description                                                                      |
|-------------|----------------------------------------------------------------------------------|
| safe        | Renders the value without applying escaping                                      |
| capitalize  | Converts the first character of the value to uppercase and the rest to lowercase |
| lower       | Converts the value to lowercase characters                                       |
| upper       | Converts the value to uppercase characters                                       |
| title       | Capitalizes each word in the value                                               |
| trim        | Removes leading and trailing whitespace from the value                           |
| striptags   | Removes any HTML tags from the value before rendering                            |

### Renderizando plantillas
Por defecto, Flask busca las plantillas en el subdirectorio de `templates` situado dentro del directorio principal de la aplicación.

Ejemplo de renderización de plantillas

```python
from flask import Flask, render_template

# ...

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)
```
- Los argumentos adicionales son pares clave-valor que representan los valores reales de las variables referenciadas en la plantilla.
- El "name" de la izquierda representa el argumento `name`, que se utiliza en la plantilla.
- El "nombre" de la derecha es una variable en el alcance (scope) actual que proporciona el valor del argumento del mismo nombre.
- No es necesario tener el mismo nombre en ambos lados

### Estructuras de control

En los siguientes ejemplos muestra cómo se pueden introducir condicionales en una plantilla:

```html
{% if user %}
    Hello, {{ user }}!
{% else %}
    Hello, Stranger!
{% endif %}
```
```html
<ul>
    {% for comment in comments %}
        <li>{{ comment }}</li>
    {% endfor %}
</ul>
```

Otra forma poderosa de reutilizar es a través de la herencia de plantillas. Primero, se crea una plantilla base con el nombre *base.html* con el siguiente contenido:

```html
<html>
<head>
    {% block head %}
    <title>{% block title %}{% endblock %} - My Application</title>
    {% endblock %}
</head>
<body>
        {% block body %}
        {% endblock %}
</body>
</html>
```

El siguiente ejemplo es una plantilla derivada de la plantilla base:
```html
{% extends "base.html" %}
{% block title %}Index{% endblock %}
{% block head %}
    {{ super() }}
    <style>
    </style>
{% endblock %}
{% block body %}
<h1>Hello, World!</h1>
{% endblock %}
```
- Se utiliza `super()` para referenciar el contenido del bloque en la plantilla base.

## Integración de Bootstrap con Flask-Bootstrap

**Bootstrap** es un framework de código abierto para navegadores web de Twitter que proporciona componentes de interfaz de usuario que ayudan a crear páginas web limpias y atractivas que son compatibles con todos los navegadores web modernos utilizados en plataformas de escritorio y móviles.

Instalación con pip:
```bash
(venv) $ pip install flask-bootstrap
````

Primero, las extensiones de Flask se inicializan al mismo tiempo que se crea la instancia de la aplicación:

```python
from flask_bootstrap import Bootstrap
# ...
bootstrap = Bootstrap(app)
```

Una vez inicializado Flask-Bootstrap, una plantilla base que incluye todos los archivos de Bootstrap y la estructura general está disponible para la aplicación. La aplicación entonces aprovecha la herencia de plantillas de Jinja2 para extender esta plantilla base.
Ejemplo de *user.html*:

```html
{% extends "bootstrap/base.html" %}

{% block title %}Flasky{% endblock %}

{% block navbar %}
<div class="navbar navbar-inverse" role="navigation">
    <div class="container">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle"
            data-toggle="collapse" data-target=".navbar-collapse">
                <span class="sr-only">Toggle navigation</span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
                <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="/">Flasky</a>
        </div>
        <div class="navbar-collapse collapse">
            <ul class="nav navbar-nav">
                <li><a href="/">Home</a></li>
            </ul>
        </div>
    </div>
</div>
{% endblock %}

{% block content %}
<div class="container">
    <div class="page-header">
        <h1>Hello, {{ name }}!</h1>
    </div>
</div>
{% endblock %}
```

## Links

Escribir las URLs como enlaces directamente en la plantilla es trivial para rutas simples, pero para rutas dinámicas con partes variables puede ser más complicado construir las URLs directamente en la plantilla. Además, las URLs escritas explícitamente crean una dependencia no deseada de las rutas definidas en el código. 

Para evitar estos problemas, Flask proporciona la función `url_for()`, que genera URLs a partir de la información almacenada en el mapa de URLs de la aplicación. Ejemplos:
- `url_for('index')`: retorna `/`, la URL raíz de la aplicación
- `url_for('index', _external=True)`: retorna un URL absoluto, en este caso es `http://localhost:5000/`
- `url_for('user', name='john', _external=True)`: retorna `http://localhost:5000/user/john`
- `url_for('user', name='john', page=2, version=1)`: retorna `/user/john?page=2&version=1`

## Localización de fechas y horas con Flask-Moment

El servidor necesita unidades de tiempo uniformes e independientes de la ubicación de cada usuario, por lo que normalmente se utiliza el UTC. El servidor trabajará exclusivamente en UTC para enviar estas unidades de tiempo al navegador web, donde se convierten a la hora local y se renderizan utilizando JavaScript.

**Flask-Moment** es una extensión para aplicaciones Flask que facilita la integración de **Moment.js** en plantillas Jinja2. 

Instalación:
```bash
(venv) $ pip install flask-moment
```

Inicialización:
```python
from flask_moment
import Moment moment = Moment(app)
```

Flask-Moment depende de **jQuery.js** además de **Moment.js**. Estas dos bibliotecas deben incluirse en alguna parte del documento HTML. Bootstrap ya incluye **jQuery.js**.

Para su importación, se coloca el siguiente código:
```html
{% block scripts %}
{{ super() }}
{{ moment.include_moment() }}
{{ moment.locale('es') }}
{% endblock %}
```
