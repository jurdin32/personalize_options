"""Los ajustes de la aplicación, en la base de datos.

Cada paquete y cada aplicación **declara** sus ajustes —una clave, un valor de
serie y para qué sirve— desde su ``AppConfig.ready()``, y este módulo los guarda en
la tabla ``Ajuste``. Así:

* el proyecto no necesita un bloque de configuración propio en ``settings.py``:
  basta con tener el paquete en ``INSTALLED_APPS`` y migrar;
* al terminar ``migrate`` se siembran los que falten (señal ``post_migrate``), sin
  pisar nunca un valor que ya esté puesto;
* lo que se cambia desde el admin o desde la aplicación vale en todo el proyecto,
  sin reiniciar;
* cada ajuste guarda de qué **paquete o aplicación** viene (``origen``), que se
  toma de quien lo declara: así en la tabla se ve qué pone ``personalize_options``,
  qué ``factec`` y qué cada aplicación del proyecto.

Un ajuste que todavía no está en la base se lee de su valor de serie, así que el
paquete funciona igual antes de migrar o si la tabla no existe.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from functools import lru_cache
from typing import Any, Dict, Iterable, Iterator, Optional, Sequence, Tuple

__all__ = [
    "AjusteDeSerie",
    "DE_SERIE",
    "booleano",
    "entero",
    "lista",
    "poner",
    "registrar",
    "sembrar",
    "texto",
    "todos",
    "usar",
    "valor",
]

#: Verdadero tal como se escribe en la base.
_SI = ("1", "si", "sí", "true", "verdadero", "on", "yes")


@dataclass(frozen=True)
class AjusteDeSerie:
    """Un ajuste que un paquete declara: su valor de serie y para qué sirve."""

    clave: str
    valor: str
    tipo: str = "texto"
    grupo: str = "General"
    descripcion: str = ""
    orden: int = 0
    editable: bool = True
    #: Quién lo declara. Vacío = se toma de quien llama a ``registrar()``.
    origen: str = ""


#: Los ajustes del propio paquete: cómo se comportan los permisos.
DE_SERIE: Tuple[AjusteDeSerie, ...] = (
    AjusteDeSerie(
        "modo",
        "abierto",
        origen="personalize_options",
        grupo="Seguridad",
        orden=1,
        descripcion=(
            "«abierto»: quien no tenga ningún rol puede todo, para montar la "
            "seguridad sin dejar a nadie fuera. «cerrado»: solo se puede lo que "
            "los roles permitan."
        ),
    ),
    AjusteDeSerie(
        "superusuarios_todo",
        "si",
        tipo="booleano",
        origen="personalize_options",
        grupo="Seguridad",
        orden=2,
        descripcion="Los superusuarios de Django pueden todo, aunque no tengan rol.",
    ),
)

#: Lo que han declarado los paquetes y las aplicaciones que están puestos.
_REGISTRO: Dict[str, AjusteDeSerie] = {
    ajuste.clave: replace(ajuste, origen=ajuste.origen or "personalize_options")
    for ajuste in DE_SERIE
}


# ------------------------------------------------------------------ registro


def _origen_de_quien_llama() -> str:
    """El paquete o la aplicación desde donde se declara el ajuste.

    Se mira la pila: el primer módulo que no sea este fichero. Así
    ``factec.django.ajustes`` declara como «factec» y ``inventario.apps`` como
    «inventario», sin tener que repetirlo en cada ajuste.
    """
    import sys

    marco = sys._getframe(1)  # noqa: SLF001 - es la forma de saber quién llama
    while marco is not None:
        modulo = marco.f_globals.get("__name__", "")
        if modulo and modulo != __name__:
            return modulo.split(".")[0]
        marco = marco.f_back
    return ""


def registrar(*nuevos: AjusteDeSerie) -> None:
    """Declara ajustes. Se llama desde el ``ready()`` de cada aplicación.

    El origen se rellena solo con el paquete de quien declara; si se pasa a mano,
    manda el que se pase.
    """
    origen = _origen_de_quien_llama()
    for ajuste in nuevos:
        if not ajuste.origen and origen:
            ajuste = replace(ajuste, origen=origen)
        _REGISTRO[ajuste.clave] = ajuste
    _leidos_de_la_base.cache_clear()


def por_clave(clave: str) -> Optional[AjusteDeSerie]:
    return _REGISTRO.get(clave)


def todos() -> Sequence[AjusteDeSerie]:
    """Los ajustes declarados, ordenados como se enseñan."""
    return tuple(
        sorted(
            _REGISTRO.values(),
            key=lambda ajuste: (
                ajuste.origen,
                ajuste.grupo,
                ajuste.orden,
                ajuste.clave,
            ),
        )
    )


# ----------------------------------------------------------------- la lectura


#: Lo que se ha fijado a mano (pruebas): manda sobre la base.
_SOBRESCRITOS: Dict[str, str] = {}


def _en_pruebas() -> bool:
    """En una tanda de pruebas no se guarda nada en memoria.

    Cada prueba corre en una transacción que se deshace al terminar: una caché
    entre pruebas devolvería el valor que puso la anterior.
    """
    import sys

    return "test" in sys.argv


@lru_cache(maxsize=1)
def _leidos_de_la_base() -> Dict[str, str]:
    from django.db.utils import DatabaseError, OperationalError, ProgrammingError

    try:
        from .models import Ajuste

        return {ajuste.clave: ajuste.valor for ajuste in Ajuste.objects.all()}
    except (DatabaseError, OperationalError, ProgrammingError):  # pragma: no cover
        return {}


def _leidos() -> Dict[str, str]:
    """Los valores guardados. Sin tabla (paquete sin migrar) no hay ninguno."""
    if _en_pruebas():
        _leidos_de_la_base.cache_clear()
    return _leidos_de_la_base()


def _de_la_base() -> Dict[str, str]:
    if not _SOBRESCRITOS:
        return _leidos()
    return {**_leidos(), **_SOBRESCRITOS}


@contextmanager
def usar(**valores: Any) -> Iterator[None]:
    """Fija ajustes mientras dure el bloque, sin tocar la base.

    Es para las pruebas::

        with ajustes.usar(inventario_descontar_al_facturar=False):
            ...

    """
    anteriores = dict(_SOBRESCRITOS)
    _SOBRESCRITOS.update({clave: ("si" if valor is True else "no" if valor is False else str(valor)) for clave, valor in valores.items()})
    try:
        yield
    finally:
        _SOBRESCRITOS.clear()
        _SOBRESCRITOS.update(anteriores)


def valor(clave: str, por_defecto: Any = None) -> str:
    """El valor guardado de ese ajuste, o el de serie, o el que se pase."""
    guardado = _de_la_base().get(clave)
    if guardado is not None:
        return guardado
    serie = _REGISTRO.get(clave)
    if serie is not None:
        return serie.valor
    return "" if por_defecto is None else str(por_defecto)


def texto(clave: str, por_defecto: str = "") -> str:
    return valor(clave, por_defecto).strip()


def entero(clave: str, por_defecto: int = 0) -> int:
    try:
        return int(str(valor(clave, por_defecto)).strip())
    except (TypeError, ValueError):
        return por_defecto


def booleano(clave: str, por_defecto: bool = False) -> bool:
    guardado = _de_la_base().get(clave)
    if guardado is None:
        serie = _REGISTRO.get(clave)
        if serie is None:
            return por_defecto
        guardado = serie.valor
    return str(guardado).strip().lower() in _SI


def lista(clave: str, por_defecto: Iterable[str] = ()) -> Tuple[str, ...]:
    """Un ajuste guardado como valores separados por comas."""
    crudo = valor(clave, ",".join(por_defecto))
    return tuple(pieza.strip() for pieza in crudo.split(",") if pieza.strip())


# ---------------------------------------------------------------- la escritura


def poner(clave: str, nuevo: Any) -> None:
    """Guarda un ajuste (lo crea si no está) y refresca lo que se lee."""
    from .models import Ajuste

    serie = _REGISTRO.get(clave)
    if isinstance(nuevo, bool):
        nuevo = "si" if nuevo else "no"
    Ajuste.objects.update_or_create(
        clave=clave,
        defaults={
            "valor": str(nuevo),
            "tipo": serie.tipo if serie else "texto",
            "origen": serie.origen if serie else "",
            "grupo": serie.grupo if serie else "General",
            "descripcion": serie.descripcion if serie else "",
            "orden": serie.orden if serie else 0,
            "editable": serie.editable if serie else True,
        },
    )
    _leidos_de_la_base.cache_clear()


def sembrar(usando: str = "default") -> int:
    """Crea los ajustes declarados que falten. Nunca pisa lo que ya está.

    Lo llama la señal ``post_migrate``: al terminar ``migrate`` quedan sembrados
    los de todos los paquetes que estén en ``INSTALLED_APPS``.
    """
    from .models import Ajuste

    existentes = set(Ajuste.objects.using(usando).values_list("clave", flat=True))
    creados = 0
    for ajuste in _REGISTRO.values():
        if ajuste.clave in existentes:
            # Ya está: se refresca lo que viene de la declaración —el origen, el
            # tipo, el grupo, para qué sirve— pero **no** el valor, que es lo que
            # alguien pudo cambiar.
            Ajuste.objects.using(usando).filter(clave=ajuste.clave).update(
                tipo=ajuste.tipo,
                origen=ajuste.origen,
                grupo=ajuste.grupo,
                descripcion=ajuste.descripcion,
                orden=ajuste.orden,
                editable=ajuste.editable,
            )
            continue
        Ajuste.objects.using(usando).create(
            clave=ajuste.clave,
            valor=ajuste.valor,
            tipo=ajuste.tipo,
            origen=ajuste.origen,
            grupo=ajuste.grupo,
            descripcion=ajuste.descripcion,
            orden=ajuste.orden,
            editable=ajuste.editable,
        )
        creados += 1
    _leidos_de_la_base.cache_clear()
    return creados


def sembrar_al_migrar(sender: Any, app_config: Any = None, using: str = "default", **kwargs: Any) -> None:
    """La señal ``post_migrate``: deja los ajustes de serie en la base."""
    sembrar(usando=using)
