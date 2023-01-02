# Desempeño

## Registro del rendimiento lento de la base de datos
Cuando el rendimiento de la aplicación degenera lentamente con el tiempo, es probable que se deba a la lentitud de las consultas a la base de datos, que empeora a medida que aumenta el tamaño de la base de datos.

Flask-SQLAlchemy dispone de una opción para registrar estadísticas sobre las consultas a bases de datos realizadas durante una petición.
```python
# app/main/views.py
@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n' %
                    (query.statement, query.parameters, query.duration,
                    query.context))
    return response
```
- `after_app_request`: 
    - Se invoca después de que regrese la función de la vista que gestiona la solicitud.
    - No modifica la respuesta; sólo obtiene los tiempos de consulta registrados por Flask-SQLAlchemy y registra los lentos en el logger de la aplicación que Flask establece en `app.logger`, antes de devolver la respuesta, que será enviada al cliente
    - Recorre la lista y registra cualquier consulta que haya durado más de un threshold dado en la variable de configuración `FLASKY_SLOW_DB_QUERY_TIME`.
- Por defecto, la función `get_debug_queries()` sólo está habilitada en modo debug.

> Lamentablemente, los problemas de rendimiento de las bases de datos rara vez aparecen durante el desarrollo porque se utilizan bases de datos mucho más pequeñas. Por esta razón, es mucho más útil activar esta opción en producción.

```python
# config.py
class Config: 
    # ...
    SQLALCHEMY_RECORD_QUERIES = True
    FLASKY_SLOW_DB_QUERY_TIME = 0.5 
    # ...
```
- `SQLALCHEMY_RECORD_QUERIES` indica a Flask-SQLAlchemy que active el registro de estadísticas de consulta.

## Perfilado de código fuente

Otra posible fuente de problemas de rendimiento es el elevado consumo de CPU, causado por funciones que realizan cálculos pesados. Los perfiladores de código fuente son útiles para encontrar las partes más lentas de una aplicación.

El servidor web de desarrollo de Flask, que proviene de Werkzeug, puede habilitar opcionalmente el perfilador de Python para cada petición.
```python
# flasky.py
@app.cli.command()
@click.option('--length', default=25,
                help='Number of functions to include in the profiler report.')
@click.option('--profile-dir', default=None,
                help='Directory where profiler data files are saved.')
def profile(length, profile_dir):
    """Start the application under the code profiler."""
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                    profile_dir=profile_dir)
    app.run(debug=False)
```
- Este comando adjunta el `ProfilerMiddleware` de Werkzeug a la aplicación, a través de su atributo `wsgi_app`.
- Cuando se inicia la aplicación con el perfil flask, la consola mostrará las estadísticas del profiler para cada petición, que incluirán las 25 funciones más lentas.

ACTUALIZACIÓN:
La opción de hacer personalizado el comando 'run' de Flask con el perfilado de código no se encuentra disponible. Una forma de solucionarlo es la siguiente:
```python
# flasky.py
if __name__ == "__main__":
    from werkzeug.middleware.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[3],
                                    profile_dir=None)
    app.run(debug=False)
```
Para ejecutar el programa es:
```bash
(venv) $ python flasky.py
```
