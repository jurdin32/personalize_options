# personalize_options

Roles y permisos de **lectura** y **escritura** por opción, para el lado del
cliente de una aplicación Django.

* Los **roles** se crean desde el admin, los que haga falta y sin tocar código.
* Cada rol marca, **opción por opción**, si puede verla o verla y modificarla.
* Si un usuario lleva varios roles, manda **el nivel más alto**.
* La aplicación se protege de tres maneras: `request.permisos` en las vistas, los
  decoradores `@requiere_lectura` / `@requiere_escritura`, y las etiquetas
  `{% puede_leer %}` / `{% puede_escribir %}` en las plantillas (y para esconder
  del menú lo que no se puede ver, `{% opciones_visibles %}`).
* El paquete es una app de Django normal: **trae sus migraciones**, así que en el
  proyecto solo hay que añadirlo y migrar.
* Trae el motor, no las pantallas: el admin de Django viene hecho, y para hacer las
  pantallas propias (un asistente del rol con casillas, la tabla de usuarios) el
  paquete deja el formulario `RolForm`, el registro de opciones y `Rol.opciones`
  para guardar los niveles.

## Instalarlo en un proyecto

```bash
pip install -e /ruta/a/personalize_options      # o pip install personalize_options
```

En `settings.py`:

```python
INSTALLED_APPS = [
    ...,
    "personalize_options",
]

MIDDLEWARE = [
    ...,
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "personalize_options.middleware.PermisosMiddleware",   # deja request.permisos
    ...,
]

PERSONALIZE_OPTIONS = {
    # "abierto": quien no tenga ningún rol puede todo (es lo de serie, para poder
    #   montar los roles sin dejar a nadie fuera). Cuando los roles estén puestos:
    #   "cerrado", y entonces solo se puede lo que los roles permitan.
    "MODO": "abierto",
    # Los superusuarios de Django pueden todo, aunque no tengan ningún rol.
    "SUPERUSUARIOS_TODO": True,
}
```

Y migrar: los roles y los permisos son tablas del paquete.

```bash
python manage.py migrate
```

## Declarar las opciones

Las opciones (una por pantalla o apartado del menú) se declaran en un solo sitio,
`personalize_options/opciones.py`; de ahí salen las casillas del admin y las del
menú. Cada opción es una clave (lo que se guarda y con lo que se pregunta) y un
nombre (lo que se lee):

```python
Opcion("clientes", "Clientes", "Catálogo"),
```

> La clave de una opción no se debe cambiar una vez en marcha: es lo que hay
> guardado en los permisos de cada rol.

Añadir o quitar opciones **no necesita migración**: las opciones no son columnas de
la base ni `choices` guardados, son esa lista. Lo que se guarda por rol es la clave
(«clientes») y su nivel, y lo que no está marcado no se puede. El paquete lo
comprueba en sus pruebas (`tests/test_migraciones.py`).

## Usarlo

En las vistas:

```python
from personalize_options.decoradores import requiere_escritura, requiere_lectura

@login_required
@requiere_lectura("clientes")            # para ver
def lista(request): ...

@login_required
@requiere_escritura("clientes")          # para modificar (incluye ver)
def guardar(request): ...
```

Cuando la misma pantalla sirve para ver y para modificar, se pide lectura al
entrar y se pregunta por la escritura al guardar:

```python
from personalize_options.decoradores import exigir_escritura, requiere_lectura

@login_required
@requiere_lectura("clientes")
def cliente(request, pk=None):
    if request.method == "POST":
        exigir_escritura(request, "clientes")   # 403 si no puede modificar
```

En las plantillas:

```django
{% load personalize_options %}
{% puede_leer "clientes" as ver_clientes %}
{% if ver_clientes %}<a href="…">Clientes</a>{% endif %}

{% if usuario|puede_escribir:"clientes" %}<button>Guardar</button>{% endif %}
```

Y para esconder del menú lo que no se puede ver:

```django
{% opciones_visibles as visibles %}
{% if "clientes" in visibles %}<li>…</li>{% endif %}
```

## Pantallas propias

El admin sirve para dejarlo montado, pero lo normal es tener las pantallas dentro de
la aplicación. El paquete pone las piezas:

* `personalize_options.forms.RolForm` — el rol con una casilla por opción
  (`nivel_<clave>`), que guarda los permisos al guardar el rol (`guardar_los_permisos`
  se puede reescribir para cambiar la forma de marcarlos).
* `personalize_options.opciones.GRUPOS` — las opciones agrupadas por apartado, para
  pintar la matriz.
* `Rol.nivel(clave)` y `Rol.opciones` — lo que tiene marcado un rol.
* `personalize_options.permisos.de(usuario)` — lo que puede hoy una persona, opción
  por opción, para enseñarlo en una pantalla.

En `MODO: "cerrado"`, quien no tenga ningún rol no puede nada; los superusuarios
pueden todo salvo que se ponga `"SUPERUSUARIOS_TODO": False`.

## Administración

El paquete registra sus dos tablas en el admin de Django, bajo
**Seguridad (roles y permisos)**:

* **Roles** — el rol, sus usuarios y una casilla por opción con *Sin acceso*, *Solo
  lectura* o *Lectura y escritura*. Trae acciones para dar solo lectura, dar lectura
  y escritura o quitar todos los permisos a los roles que se seleccionen.
* **Permisos** — la tabla tal cual, una fila por rol y opción, con el nivel editable
  en la propia lista y filtros por permiso y por rol.

Si un usuario no tiene ningún rol y el modo es `"abierto"`, puede todo; en
`"cerrado"`, nada. Los superusuarios pueden todo salvo que se ponga
`"SUPERUSUARIOS_TODO": False`.

## Pruebas del paquete

```bash
.venv/bin/python -m django test --settings=tests.settings
```
