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
