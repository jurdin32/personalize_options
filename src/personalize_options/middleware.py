"""El middleware que deja los permisos del usuario en cada petición.

Se calculan una vez por petición y quedan en ``request.permisos``: así el menú, las
vistas y las plantillas no repiten las consultas.
"""

from __future__ import annotations

from typing import Any, Callable

from . import permisos

__all__ = ["PermisosMiddleware"]


class PermisosMiddleware:
    """Cuelga ``request.permisos``."""

    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        request.permisos = permisos.de(getattr(request, "user", None))
        return self.get_response(request)
