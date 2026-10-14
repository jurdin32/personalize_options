"""Las opciones de la aplicación: lo que se puede permitir o negar.

Una opción es una pantalla o un apartado del menú. Se declaran aquí, en un solo
sitio, y de aquí salen los permisos que se marcan en cada rol y las opciones que
enseña el menú. La clave es lo que se guarda; para que el menú y las vistas hablen
el mismo idioma, conviene no cambiarla una vez en marcha.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

__all__ = [
    "Opcion",
    "OPCIONES",
    "POR_CLAVE",
    "GRUPOS",
    "opciones_de_choices",
    "existe",
    "de",
]


@dataclass(frozen=True)
class Opcion:
    """Una pantalla o apartado de la aplicación."""

    clave: str
    nombre: str
    grupo: str

    def __str__(self) -> str:
        return f"{self.grupo} · {self.nombre}"


#: Las opciones de la aplicación, en el orden del menú.
OPCIONES: Tuple[Opcion, ...] = (
    Opcion("tablero", "Tablero", "Resumen"),
    Opcion("facturar", "Nueva factura", "Facturar"),
    Opcion("facturas", "Facturas emitidas", "Facturar"),
    Opcion("notas_credito", "Notas de crédito", "Comprobantes"),
    Opcion("notas_debito", "Notas de débito", "Comprobantes"),
    Opcion("liquidaciones_compra", "Liquidaciones de compra", "Comprobantes"),
    Opcion("guias_remision", "Guías de remisión", "Comprobantes"),
    Opcion("retenciones", "Retenciones", "Comprobantes"),
    Opcion("productos", "Productos y servicios", "Catálogo"),
    Opcion("clientes", "Clientes", "Catálogo"),
    Opcion("conductores", "Conductores", "Catálogo"),
    Opcion("vehiculos", "Vehículos", "Catálogo"),
    Opcion("inventario", "Inventario", "Catálogo"),
    Opcion("configuracion", "Configuración del SRI", "Sistema"),
    # Las pantallas de la seguridad: crear roles y dárselos a la gente.
    Opcion("roles", "Roles y permisos", "Sistema"),
    Opcion("usuarios", "Usuarios y sus roles", "Sistema"),
)

#: La opción de cada clave.
POR_CLAVE: Dict[str, Opcion] = {opcion.clave: opcion for opcion in OPCIONES}

#: Las opciones por apartado, en el orden en que se declararon.
GRUPOS: Tuple[Tuple[str, Tuple[Opcion, ...]], ...] = tuple(
    (grupo, tuple(opcion for opcion in OPCIONES if opcion.grupo == grupo))
    for grupo in dict.fromkeys(opcion.grupo for opcion in OPCIONES)
)


def opciones_de_choices() -> List[Tuple[str, str]]:
    """Las opciones como ``choices`` de un campo (agrupadas por apartado)."""
    return [(opcion.clave, str(opcion)) for opcion in OPCIONES]


def existe(clave: str) -> bool:
    """¿Esa clave es una opción de la aplicación?"""
    return clave in POR_CLAVE


def de(clave: str) -> Opcion:
    """La opción de esa clave (lanza ``KeyError`` si no existe)."""
    return POR_CLAVE[clave]
