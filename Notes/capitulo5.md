# Bases de datos
## Bases de datos SQL
Las bases de datos relacionales almacenan los datos en tablas, que modelan las diferentes entidades del dominio de la aplicación. Una tabla tiene un número fijo de columnas y un número variable de filas. Las columnas definen los atributos de los datos de la entidad representada por la tabla.

**Columnas especiales**
- Llaves primarias: contienen un identificador único para cada fila almacenada en la tabla
- Llaves foráneas: hace referencia a una llave primaria en una fila en la misma u otra tabla
El vínculo entre estos se llaman *relaciones*.

El gráfico para representar la estructura de una base de datos se denomina **diagrama de entidad-relación**:
<img src='sql-edr-example.png'>

- Las cajas representan tablas de la base de datos, mostrando listas de los atributos o columnas de la tabla
- La línea que conecta las columnas roles.id y users.role_id representa una relación entre las dos tablas.
    - Los símbolos adjuntos a la línea en cada extremo indican la cardinalidad de la relación. En la imagen se muestra el caso de una relación *una-a-muchos*.

**Ventajas**
- Las bases de datos relacionales almacenan los datos de forma eficiente y evitan la duplicación.
- Cambiar el nombre de un rol de usuario en esta base de datos es sencillo porque los nombres de los roles existen en un único lugar

**Desventajas**
- Tener los datos divididos en varias tablas puede ser una complicación. La elaboración de un listado de usuarios con sus funciones presenta un pequeño problema, ya que los usuarios y las funciones de los usuarios deben leerse de dos tablas y unirse (*join*) antes de poder presentarlos juntos. 

## Bases de datos NoSQL
Las bases de datos que no siguen el modelo relacional descrito en la sección anterior se denominan bases de datos NoSQL. Una organización común para las bases de datos NoSQL utiliza *colecciones* en lugar de tablas y *documentos* en lugar de registros.

Una tabla NoSQL se muestra en la siguiente figura. Se puede observar que se aplicó una desnormalización, que reduce el número de tablas a costa de la duplicación de datos.
<img src='nosql-example.png'>

**Ventajas**
- Tener los datos duplicados permite una consulta más rápida.
- El listado de los usuarios y sus funciones es sencillo porque no se necesitan combinaciones.

**Desventajas**
- Cambiar el nombre de un rol puede resultar entonces una operación costosa que puede requerir la actualización de un gran número de documentos.

## ¿SQL o NoSQL?
Las bases de datos SQL hacen todo lo posible por preservar la consistencia, incluso ante fallos de alimentación o de hardware. El paradigma que permite a las bases de datos relacionales alcanzar este alto nivel de fiabilidad se llama **ACID**, que significa Atomicidad, Consistencia, Aislamiento y Durabilidad. Las bases de datos NoSQL relajan algunos de los requisitos de ACID y, como resultado, a veces pueden obtener una ventaja de rendimiento.

## Frameworks de bases de datos en Python

Flask no pone restricciones en cuanto a los paquetes de bases de datos que se pueden utilizar, por lo que puede trabajar con MySQL, Postgres, SQLite, Redis, MongoDB, CouchDB o DynamoDB.

Factores que hay que evaluar a la hora de elegir un framework de base de datos:

- *Fácil de usar*: Las capas de abstracción, también llamadas mapeadores objeto-relacionales (**ORM**) o mapeadores objeto-documento (**ODM**), proporcionan una conversión transparente de las operaciones orientadas a objetos de alto nivel en instrucciones de base de datos de bajo nivel.
- *Desempeño*: Las conversiones que los ORM y ODM tienen que hacer para traducir del dominio de los objetos al dominio de la base de datos tienen una sobrecarga. En general, la ganancia de productividad obtenida con los ORM y los ODM supera con creces una mínima degradación del rendimiento, por lo que esto no es un argumento válido para abandonar los ORM y los ODM.
- *Portabilidad*: Hay que tener en cuenta las opciones de bases de datos disponibles en sus plataformas de desarrollo y producción. Otro aspecto de la portabilidad se aplica a los ORM y ODM, ya que algunos de estos frameworks proporcionan una capa de abstracción para un único motor de base de datos, otros abstraen aún más y proporcionan una selección de motores de base de datos.
- *Integración con Flask*: Elegir un framework que tenga integración con Flask no es absolutamente necesario, pero podría simplificar la configuración y el funcionamiento.

## Gestión de bases de datos con Flask-SQLAlchemy
Flask-SQLAlchemy es una extensión de Flask que simplifica el uso de SQLAlchemy dentro de las aplicaciones Flask.

Instalación con pip:
```bash
(venv) $ pip install flask-sqlalchemy
```

En Flask-SQLAlchemy, una base de datos se especifica como una URL:
- MySQL: `mysql://username:password@hostname/database`
- Postgres: `postgresql://username:password@hostname/database`
- SQLite (Linux, macOS): `sqlite:////absolute/path/to/database`
- SQLite (Windows): `sqlite:///c:/absolute/path/to/database`

La URL de la base de datos de la aplicación debe configurarse como la clave `SQLALCHEMY_DATABASE_URI` en el objeto de configuración de Flask. La documentación de Flask-SQLAlchemy también sugiere configurar la clave `SQLALCHEMY_TRACK_MODIFICATIONS` a False para utilizar menos memoria a menos que se necesiten señales para los cambios de objeto

Ejemplo de configuración simple:

```python
import os
from flask_sqlalchemy import SQLAlchemy

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__) app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
```
## Definición del modelo
El término *modelo* se utiliza para referirse a las entidades persistentes utilizadas por la aplicación. En el contexto de un ORM, un modelo suele ser una clase de Python con atributos que coinciden con las columnas de una tabla de la base de datos correspondiente.

Ejemplo de modelo.
```python
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    
    def __repr__(self):
        return '<Role %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    
    def __repr__(self):
        return '<User %r>' % self.username
```
- La variable de clase `__tablename__` define el nombre de la tabla en la base de datos. Flask- SQLAlchemy asigna un nombre de tabla por defecto si se omite `__tablename__`, pero es mejor nombrar las tablas explícitamente.
- El primer argumento dado al constructor `db.Column` es el tipo de columna de la base de datos y el atributo del modelo.
- El método `__repr__()` da una representación de cadena legible que puede ser usada para propósitos de depuración y pruebas.

## Relaciones
Las bases de datos relacionales establecen conexiones entre las filas de diferentes tablas mediante el uso de relaciones.

Ejemplo de uno-a-muchos:
```python
class Role(db.Model): 
    # ...
    users = db.relationship('User', backref='role')

class User(db.Model): 
    # ...
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
```
- La columna `role_id` añadida al modelo de usuario se define como una clave foránea, y eso establece la relación.
    - El argumento `'roles.id'` a `db.ForeignKey()` especifica que la columna debe ser interpretada como si tuviera valores de `id` de las filas de la tabla `roles`.
- El atributo `users` añadido al modelo `Role` representa la vista orientada a objetos de la relación, vista desde el lado "uno". 
    - El primer argumento de `db.relationship()` indica qué modelo está al otro lado de la relación
- El argumento `backref` de `db.relationship()` define la dirección inversa de la relación, añadiendo un atributo de `role` al modelo de usuario. 

**Uno-a-uno**

La relación uno-a-uno puede expresarse de la misma manera que uno-a-muchos, pero con la opción `uselist` establecida en `False` dentro de la definición de `db.relationship()` para que el lado "muchos" se convierta en un lado "uno".

**Muchos-a-uno**

La relación muchos-a-uno también puede expresarse como uno-a-muchos si las tablas están invertidas, o puede expresarse con la clave foránea y la definición `db.relationship()` ambas en el lado "muchos".

## Operaciones de la base de datos

Recordar tener la variable de entorno `FLASK_APP` igual a `hello.py`.

### Creando tablas
```bash
(venv) $ flask shell
>>> from hello import db
>>> db.create_all()
...
>>> db.drop_all()
>>> db.create_all()
```
La función `db.create_all() `no recreará o actualizará una tabla de la base de datos si ya existe en la misma. 

### Insertando filas
Ejemplo:
```bash
>>> from hello import Role, User
>>> admin_role = Role(name='Admin')
>>> mod_role = Role(name='Moderator')
>>> user_role = Role(name='User')
>>> user_john = User(username='john', role=admin_role)
>>> user_susan = User(username='susan', role=user_role)
>>> user_david = User(username='david', role=user_role)
```
Los cambios en la base de datos se gestionan a través de una sesión de base de datos, que Flask- SQLAlchemy proporciona como `db.session`. Para preparar los objetos que se van a escribir en la base de datos, hay que añadirlos a la sesión:
```bash
>>> db.session.add_all([admin_role, mod_role, user_role,
...     user_john, user_susan, user_david])
```
Para escribir los objetos en la base de datos, la sesión necesita ser confirmada llamando a su método `commit()`:
```bash
>>> db.session.commit()
```

### Modificando filas
```bash
>>> admin_role.name = 'Administrator'
>>> db.session.add(admin_role)
>>> db.session.commit()
```

### Eliminando filas
```bash
>>> db.session.delete(mod_role) >>> db.session.commit()
```
### Consulta de filas
```bash
>>> Role.query.all()
[<Role 'Administrator'>, <Role 'User'>]
>>> User.query.all()
[<User 'john'>, <User 'susan'>, <User 'david'>]
>>> User.query.filter_by(role=user_role).all()
[<User 'susan'>, <User 'david'>]
```
Las relaciones funcionan de forma similar a las consultas. El siguiente ejemplo consulta la relación de uno-a-muchos entre roles y usuarios desde ambos extremos:
```bash
>>> users = user_role.users
>>> users
[<User 'susan'>, <User 'david'>]
>>> users[0].role
<Role 'User'>
```
La consulta implícita que se ejecuta cuando se emite la expresión `user_role.users` llama internamente a `all()` para devolver la lista de usuarios. Como el objeto de consulta está oculto, no es posible refinarlo con filtros de consulta adicionales. Para solucionar esto, la configuración de la relación se modifica con el argumento `lazy='dynamic'`:
```python
class Role(db.Model):
    # ...
    users = db.relationship('User', backref='role', lazy='dynamic')
    # ...
```
```bash
>>> user_role.users.order_by(User.username).all()
[<User 'david'>, <User 'susan'>]
>>> user_role.users.count()
2
```
## Migraciones de bases de datos con Flask-Migrate
Flask-SQLAlchemy crea tablas de base de datos a partir de modelos sólo cuando no existen ya, por lo que la única manera de hacer que actualice las tablas es destruyendo primero las tablas antiguas, pero por supuesto, esto hace que se pierdan todos los datos de la base de datos.
Una solución mejor es utilizar un framework de migración de bases de datos

El desarrollador de SQLAlchemy ha escrito un framework de migración llamado Alembic, pero en lugar de usar Alembic directamente, las aplicaciones Flask pueden usar el Flask-Migrate

### Creación de un repositorio de migración
Instalaciónde Flask-Migrate:
```bash
(venv) $ pip install flask-migrate
```
Configuración:
```python
from flask_migrate import Migrate 
# ...
migrate = Migrate(app, db)
```
Cuando se trabaja en un nuevo proyecto, se puede añadir soporte para las migraciones de bases de datos con el subcomando `init`:
```bash
(venv) $ flask db init
```
Este comando crea un directorio `migrations`, donde se almacenarán todos los scripts de migración. 

### Creación de un script de migración
En Alembic, la migración de una base de datos está representada por un script de migración. Este script tiene dos funciones llamadas upgrade() y downgrade():
- La función upgrade() aplica los cambios de la base de datos que son parte de la migración, y la función downgrade() los elimina.
Esta capacidad de añadir y eliminar cambios significa que Alembic puede reconfigurar una base de datos en cualquier punto del historial de cambios.

Las migraciones de Alembic pueden ser creadas manual o automáticamente usando los comandos revision y migrate, respectivamente.

Para realizar cambios en el esquema de su base de datos con Flask-Migrate, es necesario seguir el siguiente procedimiento:
1. Realice los cambios necesarios en las clases del modelo.
2. Crear un script de migración automática con el comando `flask db migrate`.
3. Revise el script generado y ajústelo para que represente con exactitud los cambios realizados en los modelos.
4. Añada el script de migración al control de origen.
5. Aplique la migración a la base de datos con el comando `flask db upgrade`.

```bash
(venv) $ flask db migrate -m "initial migration"
(venv) $ flask db upgrade
```
