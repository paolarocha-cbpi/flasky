# Flasky
Notas del libro Flask Web Development por Miguel Grinberg.

## Ejecución de proyecto

Crear el ambiente virtual con
```bash
python3 -m venv venv
```

Activación del ambiente virtual. En Windows se ejecuta:
```bash
venv\Scripts\activate.bat
```
En Unix o MacOS, ejecuta:
```bash
source venv/bin/activate
```

En el archivo requirements.txt se encuentran las librerías y paquetes necesarios para ejecutar el proyecto. Para instalarlos, ejecutar lo siguiente con el ambiente virtual activado:
```bash
(venv) $ pip install -r requirements.txt
```
Con el siguiente comando se puede ejecutar la aplicación en modo debug
```bash
(venv) $ flask --app hello --debug run
```

## Migraciones a la base de datos

Para crear migraciones, se utiliza primero el comando `init`:
```bash
(venv)  $ flask --app hello db init
```
Este último comando creará la carpeta `migrations` donde se encuentran los scripts de de las migraciones. 

Para crear de manera automática un script de migración:
```bash
(venv) $ flask --app hello db migrate -m "initial migration"
```
Una vez que el script ha sido revisado y aceptado, se pueden aplicar los cambios con:
```bash
(venv) $ flask --app hello db upgrade
```
