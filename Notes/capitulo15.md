# Pruebas unitarias

Existen 2 razones principales para la implementación de pruebas unitarias:
1. Confirmas que el nuevo código está trabajando como se espera
2. Cada vez que la aplicación es modificada, todas las pruebas unitarias pueden ser ejecutadas para asegurarse que los nuevos cambios no afecten al funcionamiento del código antiguo.

## Obtención de informes de cobertura del código

Las herramientas de cobertura del código miden qué parte de la aplicación se comprueba mediante pruebas unitarias y pueden proporcionar un informe detallado que indique qué partes del código de la aplicación no se comprueban.

Python tiiene la herramienta *coverage*. Se puede instalar con *pip*:
```bash
(venv) $ pip install coverage
```

Para la implementación de esta herramienta:
```python
import os

COV = None
if os.environ.get('FLASK_COVERAGE'):
    import coverage
    COV = coverage.coverage(branch=True, include='app/*')
    COV.start()

import sys
import click

# ...

@app.cli.command()
@click.option('--coverage/--no-coverage', default=False,
              help='Run tests under code coverage.')
@click.argument('test_names', nargs=-1)
def test(coverage, test_names):
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):
        import subprocess
        os.environ['FLASK_COVERAGE'] = '1'
        sys.exit(subprocess.call(sys.argv))

    import unittest
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:
        tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)
    if COV:
        COV.stop()
        COV.save()
        print('Coverage Summary:')
        COV.report()
        basedir = os.path.abspath(os.path.dirname(__file__))
        covdir = os.path.join(basedir, 'tmp/coverage')
        COV.html_report(directory=covdir)
        print('HTML version: file://%s/index.html' % covdir)
        COV.erase()
```
- El soporte de cobertura de código se activa pasando la opción `--coverage` al comando `flask test`.
- Cuando se recibe la opción `--coverage` en la función `test()`, ya es demasiado tarde para activar las métricas de cobertura. Por lo tanto, para obtener métricas precisas, el script se reinicia recursivamente después de establecer la variable de entorno `FLASK_COVERAGE`. En la segunda ejecución, la parte superior del script descubre que la variable de entorno está establecida y activa la cobertura desde el principio, incluso antes de que se importen todas las aplicaciones.
- La función `coverage.coverage()` inicia el motor de cobertura.
- La opción `branch=True` activa el análisis de cobertura de ramas que, además de rastrear qué líneas de código se ejecutan, comprueba si para cada condicional se han ejecutado tanto el caso `True` como el `False`. 
- La opción `include` se utiliza para limitar el análisis de cobertura a los archivos que están dentro del paquete de la aplicación. Sin la opción `include`, todas las extensiones instaladas en el entorno virtual y el propio código de las pruebas se incluirían en los informes de cobertura.

Para correr las pruebas:
```bash
(venv) $ flask test --coverage

# OR
(venv) $ flask --app flasky test --coverage
```

## El cliente de pruebas de Flask

Algunas partes del código de la aplicación dependen en gran medida del entorno creado por una aplicación en ejecución, esto es que las funciones de vista sólo pueden ejecutarse en el contexto de una solicitud y una aplicación en ejecución.

El cliente de pruebas reproduce el entorno que existe cuando una aplicación se ejecuta dentro de un servidor web, permitiendo que las pruebas actúen como clientes y envíen peticiones.

### Probando aplicaciones web

```python
# tests/test_client.py
import unittest
from app import create_app, db 
from app.models import User, Role

class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Stranger' in response.get_data(as_text=True))
```
- Se añade una variable de instancia `self.client`, que es el objeto cliente de prueba de Flask.
- Con la opción `use_cookies` activada, se aceptará y enviará cookies de la misma forma que lo hacen los navegadores, por lo que se pueden utilizar funcionalidades que dependen de las cookies para recordar el contexto entre peticiones, como son el uso de sesiones de usuario.

Para evitar la molestia de tratar con tokens CSRF en las pruebas, es mejor desactivar la protección CSRF en la configuración de las pruebas:

```python
# config.py
class TestingConfig(Config): #...
    WTF_CSRF_ENABLED = False
```

Prueba unitaria más elaborada:
```python
# tests/test_client.py
class FlaskClientTestCase(unittest.TestCase):
    # ...
    def test_register_and_login(self):
        # register a new account
        response = self.client.post('/auth/register', data={
            'email': 'john@example.com',
            'username': 'john',
            'password': 'cat',
            'password2': 'cat'
        })
        self.assertEqual(response.status_code, 302)

        # login with the new account
        response = self.client.post('/auth/login', data={
            'email': 'john@example.com',
            'password': 'cat'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(re.search('Hello,\s+john!',
                                    response.get_data(as_text=True)))
        self.assertTrue(
            'You have not confirmed your account yet' in response.get_data(
                as_text=True))

        # send a confirmation token
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get('/auth/confirm/{}'.format(token),
                                    follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            'You have confirmed your account' in response.get_data(
                as_text=True))

        # log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have been logged out' in response.get_data(
            as_text=True))
```
- El argumento `data` de `post()` es un diccionario con los campos del formulario, que deben coincidir exactamente con los nombres de campo definidos en el formulario HTML.
- Si los datos de registro son válidos, una redirección envía al usuario a la página de login. Para validar esto, la prueba comprueba que el código de estado de la respuesta es 302, que es el código de una redirección.
- Para la prueba de inicio de sesión a la aplicación se utiliza el correo electrónico y la contraseña que se acaban de registrar. Con una petición `POST` a la ruta `/auth/login`, esta vez con el argumento `follow_redirects=True` para hacer que el cliente de prueba funcione como un navegador y emita automáticamente una petición `GET` para la URL redirigida. 
    - Con esta opción, no se devolverá el código de estado 302; en su lugar, se devuelve la respuesta de la URL redirigida.
    - Una búsqueda de la cadena 'Hello, john!' no funcionaría porque esta cadena se ensambla a partir de porciones estáticas y dinámicas. Para evitar un error en esta prueba debido a los espacios en blanco, se utiliza una expresión regular.
- Para la prueba de confirmación de la cuenta, se omite el token que se generó como parte del registro y genera otro directamente a partir de la instancia `User`.
- Para la prueba en la que el usuario hace clic en la URL del token de confirmación recibido por correo electrónico, se envía una petición `GET` a la URL de confirmación, que incluye el token. La respuesta a esta petición es una redirección a la página de inicio.
- Finalmente, se envia una petición `GET` a la ruta de cierre de sesión; para confirmar que ha funcionado, la prueba busca el mensaje flash en la respuesta.

### Probando Servicios Web

```python
# tests/test_api.py
import unittest
import json
import re
from base64 import b64encode
from app import create_app, db
from app.models import User, Role, Post, Comment


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + b64encode(
                (username + ':' + password).encode('utf-8')).decode('utf-8'),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_no_auth(self):
        response = self.client.get('/api/v1/posts/',
                                    content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_posts(self):
        # add a user
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(email='john@example.com', password='cat', confirmed=True,
                    role=r)
        db.session.add(u)
        db.session.commit()

        # write an empty post
        response = self.client.post(
            '/api/v1/posts/',
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({'body': ''}))
        self.assertEqual(response.status_code, 400)

        # write a post
        response = self.client.post(
            '/api/v1/posts/',
            headers=self.get_api_headers('john@example.com', 'cat'),
            data=json.dumps({'body': 'body of the *blog* post'}))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # get the new post
        response = self.client.get(
            url,
            headers=self.get_api_headers('john@example.com', 'cat'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'body of the *blog* post')
        self.assertEqual(json_response['body_html'],
                        '<p>body of the <em>blog</em> post</p>')
        json_post = json_response
```
- `get_api_headers()` es un método helper que devuelve las cabeceras comunes que necesitan ser enviadas con la mayoría de las peticiones API. 
- `test_no_auth()` es una prueba sencilla que garantiza que una solicitud que no incluya credenciales de autenticación se rechace con el código de error 401. 
- `test_posts()` añade un usuario a la base de datos y luego utiliza la API RESTful para insertar una entrada de blog y luego leerla de vuelta. 
- Cualquier petición que envíe datos en el cuerpo debe codificarlos con `json.dumps()`, porque el cliente de prueba Flask no codifica automáticamente a JSON. 


## Pruebas integrales con Selenium
El cliente de prueba de Flask no puede emular completamente el entorno de una aplicación en ejecución. Cuando las pruebas requieren el entorno completo, no hay más remedio que utilizar un navegador web real conectado a la aplicación que se ejecuta en un servidor web real. **Selenium** es una herramienta de automatización de navegadores web compatible con los navegadores más populares de los tres principales sistemas operativos.
```bash
(venv) $ pip install selenium
```

Selenium requiere que se instale por separado un controlador para el navegador web deseado, además del propio navegador.
```bash
(venv) $ brew install chromedriver
```

Realizar pruebas con Selenium requiere que la aplicación se esté ejecutando dentro de un servidor web que esté escuchando peticiones HTTP reales. Bajo el control de las pruebas, Selenium lanza un navegador web y hace que se conecte a la aplicación para realizar las operaciones requeridas.

Un problema con este enfoque es que después de que todas las pruebas se han completado, el servidor Flask necesita ser detenido, idealmente de una manera elegante, para que las tareas en segundo plano, como el motor de cobertura de código puedan terminar limpiamente su trabajo. El servidor web Werkzeug tiene una opción de apagado, pero debido a que el servidor se ejecuta aislado en su propio hilo, la única manera de pedir al servidor que se apague es mediante el envío de una solicitud HTTP regular.
```python
# app/main/views.py
@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'
```

[Aquí](https://github.com/paolarocha-cbpi/flasky/blob/main/tests/test_selenium.py) se encuentra el código de las diferentes pruebas unitarias realizadas con Selenium. De lo cual, podemos rescatar que:
- Los métodos `setUpClass()` y `tearDownClass()` se invocan antes y después de que se ejecuten las pruebas de esta clase.
- La configuración implica iniciar una instancia de Chrome a través de la API webdriver de Selenium, y crear una aplicación y una base de datos con algunos datos falsos iniciales para que las pruebas los utilicen.
- La aplicación se inicia en un hilo utilizando el método `app.run()`. 
- Al final la aplicación recibe una petición a `/shutdown`, que hace que el hilo de fondo termine.
- Cuando se realizan pruebas con Selenium, las pruebas envían comandos al navegador web y nunca interactúan con la aplicación directamente. Es decir, **los comandos están relacionados con las acciones que hace un usuario real con su teclado y mouse**.
    - Por ejemplo, para ir a la página de inicio de sesión, la prueba busca el enlace "Iniciar sesión" utilizando `find_element_by_link_text()` y luego llama a `click()` sobre él para provocar un clic real en el navegador

## ¿Vale la pena?

Las pruebas de extremo a extremo del tipo que el cliente de pruebas Flask y Selenium pueden llevar a cabo son a veces necesarias, pero debido a la mayor complejidad de escribirlas, deberían utilizarse sólo para funcionalidades que no puedan probarse de forma aislada.

El código que existe en las funciones de vista debe ser simple y sólo actuar como una capa delgada que acepta peticiones e invoca las acciones correspondientes en otras clases o funciones que encapsulan la lógica de la aplicación.

Así que sí, las pruebas merecen la pena. Pero es importante diseñar una estrategia de pruebas eficiente y escribir código que pueda aprovecharla.
