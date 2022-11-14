# Roles de usuario
## Representación de usuarios en la base de datos
```python
# app/models.py
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
```
- El campo `default` se añadió a la base de datos. Este campo debe ser establecido como `True` para un solo rol (y a los nuevos usuarios al registrarse) y `False` para todos los demás.
- El campo `permissions` guarda un valor entero que define la lista de permisos para el rol de una manera compacta. Dado que SQLAlchemy establecerá este campo en `None` por defecto, se añade un constructor de clase que lo establece en 0.

Los permisos toman valores en potencias de dos ya que permite combinar los permisos, dando a cada posible combinación de permisos un valor único para almacenar en el campo de permisos del rol.
```python
# app/models.py
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16
```
Métodos para administrar permisos:
```python
# app/models.py
class Role(db.Model):
    # ...
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm
```
La definición de usuarios se muestra en la siguiente lista:
- `None`: `None`. Usuario solo para la lectura y usuarios que no han iniciado sesión.
- `User`: `FOLLOW`, `COMMENT`, `WRITE`. Permisos básicos para nuevos usuarios.
- `Moderatos`: `FOLLOW`, `COMMENT`, `WRITE`, `MODERATE`. Modera comentarios de otros usuarios.
- `Administrator`: `FOLLOW`, `COMMENT`, `WRITE`, `MODERATE`, `ADMIN`. Acceso completo.

Se crea un método de clase para añadir usuarios.
```python
# app/models.py
class Role(db.Model):
    # ...

    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                        Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                            Permission.WRITE, Permission.MODERATE,
                            Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()
```
- La función `insert_roles()` no crea directamente nuevos objetos de rol, sino que trata de encontrar los roles existentes por su nombre y los actualiza. Se crea un nuevo objeto de rol sólo para los roles que no están ya en la base de datos. 
- `insert_roles()` es un método estático, un tipo especial de método que no requiere la creación de un objeto, ya que puede ser invocado directamente en la clase.


## Asignación de roles
Para la mayoría de los usuarios, se le asignará el rol `User`. La única excepción es cuando hay que asignar el rol de "`Administrator`" desde el principio. Este usuario se identifica mediante una dirección de correo electrónico almacenada en la variable de configuración `FLASKY_ADMIN`.

```python
# app/models.py
class User(UserMixin, db.Model):
    # ...
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASKY_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
    # ...
```
## Verificación de roles
```python
# app/models.py
from flask_login import UserMixin, AnonymousUserMixin

class User(UserMixin, db.Model):
    # ...

    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_administrator(self):
        return self.can(Permission.ADMIN)

class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser
```
- El método `can()` añadido al modelo de usuario devuelve `True` si el permiso solicitado está presente en el rol
- `AnonymousUser` implementa los métodos `can()` y `is_administrator()` sin tener que verificar primero si el usuario está conectado.
- Flask-Login utiliza el usuario anónimo personalizado de la aplicación estableciendo su clase en el atributo `login_manager.anonymous_user`.

Para los casos en los que una función de vista debe estar disponible sólo para los usuarios con ciertos permisos, se puede utilizar un decorador personalizado

```python
# app/decorators.py
from functools import wraps
from flask import abort
from flask_login import current_user
from .models import Permission


def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.can(permission):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return permission_required(Permission.ADMIN)(f)
```

Los permisos también pueden necesitar ser verificados desde las plantillas, por lo que la clase `Permission` con todas sus constantes necesita ser accesible para ellas. Para evitar tener que añadir un argumento de plantilla en cada llamada a `render_template()`, se puede utilizar un *procesador de contexto*. Los procesadores de contexto hacen que las variables estén disponibles para todas las plantillas durante el renderizado.

```python
# app/main/__init__.py
from ..models import Permission

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
```

**Añadiendo los nuevos roles a la base de datos de desarrollo en una sesión de shell**
```bash
(venv) $ flask shell
>>> Role.insert_roles()
>>> Role.query.all()
[<Role 'Administrator'>, <Role 'User'>, <Role 'Moderator'>]
```

**Actualizando la lista de usuarios para que todas las cuentas de usuario que fueron creadas antes de que existieran los roles y permisos tengan un rol asignado**

```bash
(venv) $ flask shell
>>> admin_role = Role.query.filter_by(name='Administrator').first()
>>> default_role = Role.query.filter_by(default=True).first()
>>> for u in User.query.all():
...    if u.role is None:
...        if u.email == app.config['FLASKY_ADMIN']:
...            u.role = admin_role
...        else:
...            u.role = default_role
...
>>> db.session.commit()
```
