"""Roles y permisos de lectura/escritura por opción, para el lado del cliente.

Es una app de Django hecha para llevarla a cualquier proyecto: se copia la carpeta
en la raíz del proyecto (o se instala el paquete), se añade a ``INSTALLED_APPS`` y
se migra —las tablas las trae el propio paquete—. Con eso se pueden crear
**roles** (los que hagan falta, sin tocar código) y decidir, para cada **opción**
de la aplicación, si ese rol puede leerla o leerla y escribirla.

Se usa así:

* ``request.permisos`` — lo que puede el usuario de la petición (lo cuelga el
  middleware, ver :mod:`personalize_options.middleware`).
* ``@requiere_lectura("clientes")`` y ``@requiere_escritura("clientes")`` — para
  las vistas, y ``exigir_escritura(request, "clientes")`` dentro de una vista que
  sirve para ver y para guardar (ver :mod:`personalize_options.decoradores`).
* ``{% puede_leer "clientes" %}`` y ``{% puede_escribir "clientes" %}`` — para las
  plantillas y el menú (ver :mod:`personalize_options.templatetags.personalize_options`).
* ``personalize_options.permisos.de(usuario)`` — para el código que no tiene una
  petición.

Las opciones —una por pantalla o apartado del menú— viven en la base de datos, así
que se crean y se cambian sin tocar código ni migrar: se ven en el admin
(``personalize_options.Opcion``) y desde las pantallas que haga el proyecto con
:mod:`personalize_options.opciones`. Los ajustes van en
``settings.PERSONALIZE_OPTIONS`` (ver :mod:`personalize_options.conf`).
"""
