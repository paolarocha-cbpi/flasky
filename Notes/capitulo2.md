# Estructura básica de una aplicación

## Inicialización

La *instancia de aplicación* es un objeto en Flask que recibe todas las peticiones de los clientes usando el protocolo Web Server Gateway Interface (WSGI). Se crea llamando al constructor de la clase Flask:
```python
from flask import Flask
app = Flask(__name__)
```
El argumento `__name__` que es pasado al constructor de la aplicación determina la ubicación de la aplicación (otros archivos de la aplicación como imágenes y plantillas).

# Rutas y Funciones de Visualización

Los clientes, como los navegadores web, envían *peticiones* al servidor web, que a su vez las envía a la instancia de la aplicación Flask. La instancia de la aplicación Flask necesita saber qué código necesita ejecutar para cada URL solicitada, por lo que mantiene un mapeo de URLs a funciones de Python. La asociación entre una URL y la función que la maneja se llama ruta. Ejemplo:
```python
@app.route('/')
def index():
    return '<h1>Hello World!</h1>'
```
Partes:
- `index()` es la función que maneja la URL raíz de la aplicación. Es la función de vista
- `app.route` es el decorador para registrar la función de vista

**Componentes dinámicos** <br>
Flask también soporta componentes dinámicos encapsulados entre corchetes, por ejemplo:
```python
@app.route('/user/<name>') def user(name):
return '<h1>Hello, {}!</h1>'.format(name)
```
Flask soporta los tipos `string`, `int`, `float` y `path`para rutas.

# Servidor web de desarrollo
Las aplicaciones Flask incluyen un servidor web de desarrollo que puede iniciarse con el comando `flask run`. 
Este comando busca el nombre del script de Python que contiene la instancia de la aplicación en la variable de entorno `FLASK_APP`.

Para Linux y macOS:
```bash
(venv) $ export FLASK_APP=hello.py
(venv) $ flask run
```

# Modo Debug

Las aplicaciones Flask pueden ejecutarse opcionalmente en modo *debug* En este modo, dos módulos muy convenientes del servidor de desarrollo llamados el *reloader* y el *debugger* están habilitados por defecto.

Cuando el *reloader* está habilitado, Flask vigila todos los archivos de código fuente de su proyecto y reinicia automáticamente el servidor cuando se modifica alguno de los archivos.

El *debugger* es una herramienta basada en la web que aparece en el navegador cuando la aplicación lanza una excepción no controlada. Es útil para inspeccionar el código fuente y evaluar expresiones.

Para habilitarlo:
```bash
(venv) $ export FLASK_APP=hello.py
(venv) $ export FLASK_DEBUG=1
(venv) $ flask run
```

# Ciclo request-response
## Contextos Application y Request

Para evitar saturar las funciones de la vista con un montón de argumentos que no siempre son necesarios, Flask utiliza **contextos** para hacer que ciertos objetos sean accesibles globalmente de forma temporal.

Existen dos contextos en flask: contexto de aplicación y contexto de request.

Flask activa (o empuja) los contextos de aplicación y de request antes de enviar una solicitud a la aplicación, y los elimina después de que el request sea procesado. Cuando el contexto de aplicación es empujado, las variables `current_app` y `g` se vuelven disponibles para el hilo (thread). Del mismo modo, cuando se envía el contexto de request, `request` y `session` también están disponibles. Si se accede a cualquiera de estas variables sin un contexto de aplicación o solicitud activo, se genera un error. 

## Request Dispatching (Solicitud de envío)

Cuando la aplicación recibe un request de un cliente, necesita averiguar qué función de la vista debe invocar para atenderla. Para esta tarea, Flask busca la URL dada en la solicitud en el mapa de URL de la aplicación, que contiene un mapeo de URLs a las funciones de vista que las manejan. Ejemplo:
```bash
(venv) $ python
>>> from hello import app
>>> app.url_map
Map([<Rule '/' (HEAD, OPTIONS, GET) -> index>,
     <Rule '/static/<filename>' (HEAD, OPTIONS, GET) -> static>,
     <Rule '/user/<name>' (HEAD, OPTIONS, GET) -> user>])
```
- La ruta `/static/<filename>` es una ruta especial añadida por Flask para dar acceso a archivos estáticos
- Los elementos `(HEAD, OPTIONS, GET)` que se muestran en el mapa de URLs son los métodos de solicitud que son manejados por las rutas.

## The Request Object
Flask expone un objeto request como una variable de contexto llamada `request`. Este es un objeto extremadamente útil que contiene toda la información que el cliente incluyó en la solicitud HTTP. 

## Request Hooks
En lugar de duplicar el código que realiza estas acciones en cada función de la vista, Flask le da la opción de registrar funciones comunes para ser invocadas antes o después de que se despache una solicitud.

## Responses

Cuando Flask invoca una función de vista, espera que su valor de retorno sea la respuesta a la solicitud. En la mayoría de los casos la respuesta es una simple cadena que se devuelve al cliente como una página HTML.

La función `redirect()` es un tipo de respuesta especial que solamente proporciona una nueva URL al navegador. `abort()` es otra función especial manejar errores.