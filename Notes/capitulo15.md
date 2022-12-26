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

