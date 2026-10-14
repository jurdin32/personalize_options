"""El formulario del rol: sus datos y una casilla por opción.

Se marcan todas las opciones de una vez (y del mismo sitio), en vez de ir añadiendo
un permiso por fila: es como se piensa un rol, «qué puede y qué no».
"""

from __future__ import annotations

from typing import Any, Dict

from django import forms

from . import opciones
from .models import Nivel, Permiso, Rol

__all__ = ["SIN_ACCESO", "NIVELES", "CAMPO", "clave_de", "RolForm"]

#: Lo que se marca cuando no se da acceso a una opción.
SIN_ACCESO = ""

#: Los tres estados que se pueden marcar en cada opción.
NIVELES = (
    (SIN_ACCESO, "Sin acceso"),
    (Nivel.LECTURA.value, "Solo lectura"),
    (Nivel.ESCRITURA.value, "Lectura y escritura"),
)

#: Lo que se le pone delante al nombre del campo de cada opción.
CAMPO = "nivel_"


def clave_de(nombre_del_campo: str) -> str:
    """La clave de la opción a la que corresponde ese campo."""
    return nombre_del_campo[len(CAMPO):]


class RolForm(forms.ModelForm):
    """El rol, con una casilla por opción de la aplicación."""

    class Meta:
        model = Rol
        fields = ["nombre", "descripcion", "activo", "usuarios"]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        puestos: Dict[str, str] = self.instance.opciones if self.instance.pk else {}
        for opcion in opciones.todas(solo_activas=True):
            self.fields[f"{CAMPO}{opcion.clave}"] = forms.ChoiceField(
                label=opcion.nombre,
                choices=NIVELES,
                required=False,
                initial=puestos.get(opcion.clave, SIN_ACCESO),
            )

    def _save_m2m(self) -> None:
        """Los usuarios del rol y, con ellos, sus permisos.

        Se guarda aquí y no en :meth:`save` porque Django, cuando se guarda con
        ``commit=False`` (que es como lo hace el admin), no llama a ``save_m2m``
        sino que lo rebautiza a este método: así los permisos se escriben en los
        dos casos, y siempre con el rol ya guardado.
        """
        super()._save_m2m()
        self.guardar_los_permisos(self.instance)

    def guardar_los_permisos(self, rol: Rol) -> None:
        """Deja los permisos como se hayan marcado: lo no marcado se quita."""
        for opcion in opciones.todas():
            nivel = self.cleaned_data.get(f"{CAMPO}{opcion.clave}") or SIN_ACCESO
            if nivel:
                Permiso.objects.update_or_create(
                    rol=rol, opcion=opcion.clave, defaults={"nivel": nivel}
                )
            else:
                Permiso.objects.filter(rol=rol, opcion=opcion.clave).delete()
