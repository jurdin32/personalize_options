"""Las vistas protegidas: se pasa, o no se pasa."""

from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import TestCase, override_settings

from personalize_options.decoradores import (
    exigir_escritura,
    exigir_lectura,
    requiere_escritura,
    requiere_lectura,
)
from personalize_options.models import Nivel

from .comun import CERRADO, SIN_ROLES, rol_con


class PruebasDeLosDecoradores(TestCase):
    """Las vistas protegidas: se pasa, o no se pasa."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")

    def _pedir(self, usuario):
        return SimpleNamespace(user=usuario)

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_con_solo_lectura_se_entra_a_ver_pero_no_a_modificar(self) -> None:
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value)

        @requiere_lectura("clientes")
        def ver(peticion):
            return HttpResponse("se ve")

        @requiere_escritura("clientes")
        def modificar(peticion):
            return HttpResponse("se modifica")

        self.assertEqual(ver(self._pedir(self.usuario)).status_code, 200)
        with self.assertRaises(PermissionDenied):
            modificar(self._pedir(self.usuario))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_sin_permiso_no_se_entra_y_se_dice_por_que(self) -> None:
        rol_con("Otra-cosa", self.usuario, productos=Nivel.ESCRITURA.value)

        @requiere_lectura("clientes")
        def ver(peticion):
            return HttpResponse("se ve")

        with self.assertRaises(PermissionDenied) as queja:
            ver(self._pedir(self.usuario))

        self.assertIn("Clientes", str(queja.exception))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_con_escritura_se_entra_tambien_a_ver(self) -> None:
        rol_con("Ventas", self.usuario, clientes=Nivel.ESCRITURA.value)

        @requiere_lectura("clientes")
        def ver(peticion):
            return HttpResponse("se ve")

        self.assertEqual(ver(self._pedir(self.usuario)).status_code, 200)

    @override_settings(PERSONALIZE_OPTIONS=SIN_ROLES)
    def test_en_modo_abierto_quien_no_tiene_rol_entra(self) -> None:
        @requiere_lectura("clientes")
        def ver(peticion):
            return HttpResponse("se ve")

        self.assertEqual(ver(self._pedir(self.usuario)).status_code, 200)


    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_se_puede_preguntar_dentro_de_la_vista(self) -> None:
        # La misma pantalla se ve con lectura y se guarda con escritura.
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value)
        peticion = self._pedir(self.usuario)

        exigir_lectura(peticion, "clientes")  # ver: pasa

        with self.assertRaises(PermissionDenied) as queja:
            exigir_escritura(peticion, "clientes")  # guardar: corta

        self.assertIn("modificar «Clientes»", str(queja.exception))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_con_escritura_no_corta_al_guardar(self) -> None:
        rol_con("Ventas", self.usuario, clientes=Nivel.ESCRITURA.value)

        exigir_escritura(self._pedir(self.usuario), "clientes")
