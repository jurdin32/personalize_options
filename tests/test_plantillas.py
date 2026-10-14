"""Las etiquetas y los filtros que se usan en las plantillas."""

from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase, override_settings

from personalize_options.models import Nivel

from .comun import CERRADO, rol_con


class PruebasDeLasPlantillas(TestCase):
    """Las etiquetas y los filtros que se usan en las plantillas."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")
        self.peticion = SimpleNamespace(user=self.usuario)

    def _pintar(self, plantilla: str) -> str:
        return Template("{% load personalize_options %}" + plantilla).render(
            Context({"request": self.peticion, "usuario": self.usuario})
        ).strip()

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_se_pregunta_por_una_opcion(self) -> None:
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value)

        self.assertEqual(self._pintar('{% puede_leer "clientes" as ver %}{{ ver }}'), "True")
        self.assertEqual(
            self._pintar('{% puede_escribir "clientes" as ver %}{{ ver }}'), "False"
        )

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_las_opciones_visibles_son_las_del_menu(self) -> None:
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value, tablero=Nivel.LECTURA.value)

        self.assertEqual(
            self._pintar("{% opciones_visibles as visibles %}{{ visibles|length }}"), "2"
        )
        self.assertEqual(self._pintar('{% puede_leer "productos" as ver %}{{ ver }}'), "False")

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_los_filtros_van_sobre_un_usuario(self) -> None:
        rol_con("Ventas", self.usuario, clientes=Nivel.ESCRITURA.value)

        self.assertEqual(self._pintar('{{ usuario|puede_escribir:"clientes" }}'), "True")
        self.assertEqual(self._pintar('{{ usuario|puede_leer:"productos" }}'), "False")

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_sin_el_middleware_en_medio_tambien_funciona(self) -> None:
        # El menú y las plantillas no dependen de que esté puesto el middleware.
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value)

        self.assertEqual(
            self._pintar('{% puede_leer "clientes" as ver %}{{ ver }}'), "True"
        )

    def test_el_nombre_de_una_opcion(self) -> None:
        self.assertEqual(self._pintar('{% nombre_de "clientes" %}'), "Clientes")
        self.assertEqual(self._pintar('{% nombre_de "inventada" %}'), "inventada")
