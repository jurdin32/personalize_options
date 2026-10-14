# personalize_options

**Roles y permisos de lectura y escritura por opción** para aplicaciones Django: se
marca, opción por opción, quién puede ver y quién puede modificar cada pantalla, con
los roles que hagan falta y sin tocar código.

- Las **opciones** (una por pantalla o apartado) y los **roles** viven en la base de
  datos: se crean y se cambian desde el admin de Django o desde las pantallas que haga
  la aplicación, sin migrar nada.
- Tres niveles por rol y opción: **sin acceso**, **solo lectura** o **lectura y
  escritura**. Escribir incluye leer: no se modifica lo que no se ve.
- Si un usuario lleva varios roles, manda **el nivel más alto**.
- La aplicación se protege en tres sitios: `request.permisos` en las vistas, los
  decoradores `@requiere_lectura` / `@requiere_escritura`, y las etiquetas
  `{% puede_leer %}` / `{% puede_escribir %}` en las plantillas —y el menú, con
  `{% opciones_visibles %}`—.
- Es una app de Django normal: **trae sus migraciones**, así que en el proyecto solo
  hay que añadirlo y migrar.
- Trae el motor y el admin; las pantallas propias (un asistente del rol, la tabla de
  usuarios) se hacen con lo que deja: `RolForm`, el registro de opciones y las
  etiquetas.

| Tabla | Qué guarda |
|---|---|
| `Opcion` | Las pantallas que se pueden permitir o negar |
| `Rol` | Un permiso con nombre («Facturador», «Bodega»), con sus usuarios |
| `Permiso` | Lo que un rol puede en una opción |

---

## Instalación

```bash
# desde GitHub
pip install "personalize_options @ git+https://github.com/jurdin32/personalize_options.git"

# una versión concreta
pip install "personalize_options @ git+https://github.com/jurdin32/personalize_options.git@v1.0.0"

# desde una copia local, para desarrollarlo
pip install -e /ruta/a/personalize_options
```

**Requisitos:** Python 3.9 o superior y Django 4.2 o superior. El paquete **no trae
Django** como dependencia: lo pone el proyecto que lo usa, que ya lo tiene. Para las
pruebas del paquete hay un extra `dev` que sí lo añade:

```bash
pip install "personalize_options[dev] @ git+https://github.com/jurdin32/personalize_options.git"
```

---

## Puesta en marcha con Django

### 1. Instale el paquete

```bash
pip install "personalize_options @ git+https://github.com/jurdin32/personalize_options.git"
```

### 2. Añada la app, el middleware y los ajustes

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

El middleware va **después** de `AuthenticationMiddleware`: necesita el usuario de la
petición para saber qué puede.

### 3. Cree las tablas (obligatorio)

```bash
python manage.py migrate
```

Las migraciones viajan dentro del paquete: crea las tres tablas (`personalize_options_opcion`,
`_rol` y `_permiso`) y siembra las **opciones de serie**, para que las pantallas de un
proyecto recién añadido tengan por dónde protegerse desde el primer día.

### 4. Proteja las pantallas

```python
from personalize_options.decoradores import requiere_escritura, requiere_lectura

@login_required
@requiere_lectura("clientes")
def lista(request): ...

@login_required
@requiere_escritura("clientes")
def guardar(request): ...
```

```django
{% load personalize_options %}
{% puede_leer "clientes" as ver %}
{% if ver %}<a href="…">Clientes</a>{% endif %}
```

El detalle está en [Cómo se usa](#cómo-se-usa).

### 5. Cree el primer rol

En el admin (**Seguridad (roles y permisos) → Roles**) o desde las pantallas de la
aplicación: nombre, los usuarios que lo llevan y una casilla por opción. Con los roles
puestos, ponga `"MODO": "cerrado"` y ya solo se puede lo que los roles permitan.

---

## Las opciones

Una opción es una pantalla o un apartado (Clientes, Guías de remisión, Inventario…).
Viven en la **base de datos**, así que se crean, se renombran y se apagan desde el
admin o desde las pantallas que haga la aplicación, **sin tocar código y sin migrar**.
Lo que se guarda por rol es la clave de la opción (`clientes`) y su nivel; lo que no
está marcado, no se puede.

El paquete siembra las que trae de serie —`personalize_options.opciones.DE_SERIE`— con
la migración de datos. Si la tabla todavía no existe (paquete sin migrar), el registro
usa esa lista para no romper nada.

Cada opción tiene su clave (con lo que se pregunta en el código), su nombre, su
apartado y, si se quiere que salga en el menú, su dirección y su icono:

```python
from personalize_options.models import Opcion

Opcion.objects.create(
    clave="reportes",
    nombre="Reportes de ventas",
    grupo="Reportes",
    url="/reportes/",          # para que salga en el menú
    icono="chart-bar",
    orden=20,
)
```

Para leer el registro (estas funciones consultan la base):

```python
from personalize_options.opciones import todas, grupos, por_clave, de, existe

todas()                    # todas, en orden
todas(solo_activas=True)   # sin las apagadas
grupos()                   # [(apartado, [opciones]), …], para pintar una matriz
por_clave()                # {clave: opción}
de("clientes")             # la opción de esa clave (KeyError si no está)
existe("clientes")
```

> La clave de una opción no debería cambiarse una vez en marcha: es lo que hay guardado
> en los permisos. Si se cambia, el paquete muda los permisos con ella; si se borra la
> opción, sus permisos se van también.

Para que una opción creada después salga sola en el menú, el menú del proyecto pide las
que no pinta a mano:

```django
{% load personalize_options %}

{% opciones_del_menu "Sistema" "configuracion roles usuarios opciones" as extras %}
{% for o in extras %}
  <li><a href="{{ o.url }}">{{ o.nombre }}</a></li>
{% endfor %}

{% apartados_nuevos "Resumen Facturar Comprobantes Catálogo Sistema" as apartados %}
{% for apartado, opciones in apartados %}
  <li>
    <h3>{{ apartado }}</h3>
    <ul>{% for o in opciones %}<li><a href="{{ o.url }}">{{ o.nombre }}</a></li>{% endfor %}</ul>
  </li>
{% endfor %}
```

---

## Cómo se usa

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

Cuando la misma pantalla sirve para ver y para modificar, se pide lectura al entrar y se
pregunta por la escritura al guardar:

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

Todo lo que puede un usuario, de una vez:

```python
from personalize_options.permisos import de as permisos_de

quien = permisos_de(request.user)
quien.puede_leer("clientes")        # True / False
quien.puede_escribir("clientes")
quien.nivel("clientes")            # "lectura", "escritura" o ""
quien.visibles                     # {"clientes", "facturas", …}
```

---

## Pantallas propias

El admin sirve para dejarlo montado, pero lo normal es tener las pantallas dentro de la
aplicación. El paquete pone las piezas:

* `personalize_options.forms.RolForm` — el rol con una casilla por opción
  (`nivel_<clave>`), que guarda los permisos al guardar el rol (`guardar_los_permisos`
  se puede reescribir para cambiar la forma de marcarlos).
* `personalize_options.opciones.grupos()` — las opciones agrupadas por apartado, para
  pintar la matriz.
* `Rol.nivel(clave)` y `Rol.opciones` — lo que tiene marcado un rol.
* `personalize_options.permisos.de(usuario)` — lo que puede hoy una persona, opción por
  opción, para enseñarlo en una pantalla.

En `MODO: "cerrado"`, quien no tenga ningún rol no puede nada; los superusuarios pueden
todo salvo que se ponga `"SUPERUSUARIOS_TODO": False`.

---

## Administración

El paquete registra sus tres tablas en el admin de Django, bajo **Seguridad (roles y
permisos)**:

* **Opciones** — el catálogo de pantallas que se pueden permitir: se crean aquí, con su
  apartado, su orden y, si llevan dirección, su sitio en el menú.
* **Roles** — el rol, sus usuarios y una casilla por opción con *Sin acceso*, *Solo
  lectura* o *Lectura y escritura*. Trae acciones para dar solo lectura, dar lectura y
  escritura o quitar todos los permisos a los roles que se seleccionen.
* **Permisos** — la tabla tal cual, una fila por rol y opción, con el nivel editable en
  la propia lista y filtros por permiso y por rol.

---

## Actualizar

```bash
pip install -U "personalize_options @ git+https://github.com/jurdin32/personalize_options.git"
python manage.py migrate
```

Para quedarse en una versión concreta, ponga la etiqueta al instalar (por ejemplo
`@v1.0.0`); sin etiqueta, `pip` siempre baja la última de `main`.

---

## Pruebas del paquete

Con el extra `dev` (trae Django) y su propio entorno:

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m django test --settings=tests.settings
```
