"""Las etiquetas y los filtros que se usan en las plantillas."""

from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth.models import User
from django.template import Context, Template
from django.test import TestCase, override_settings

from personalize_options.models import Nivel, Opcion

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


class PruebasDelMenuDinamico(TestCase):
    """Las opciones creadas después salen en el menú sin tocar la plantilla."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-mira")
        self.peticion = SimpleNamespace(user=self.usuario)

    def _pintar(self, plantilla: str) -> str:
        return Template("{% load personalize_options %}" + plantilla).render(
            Context({"request": self.peticion, "usuario": self.usuario})
        ).strip()

    def test_una_opción_con_dirección_sale_en_su_apartado(self) -> None:
        Opcion.objects.create(
            clave="reportes", nombre="Reportes", grupo="Sistema", url="/reportes/", icono="chart-bar"
        )

        pintado = self._pintar(
            '{% opciones_del_menu "Sistema" "configuracion roles usuarios" as extras %}'
            "{% for o in extras %}{{ o.nombre }}={{ o.url }};{% endfor %}"
        )

        self.assertEqual(pintado, "Reportes=/reportes/;")

    def test_lo_que_la_plantilla_ya_pinta_no_se_repite(self) -> None:
        Opcion.objects.create(
            clave="reportes", nombre="Reportes", grupo="Sistema", url="/reportes/"
        )

        pintado = self._pintar(
            '{% opciones_del_menu "Sistema" "reportes" as extras %}{{ extras|length }}'
        )

        self.assertEqual(pintado, "0")

    def test_sin_dirección_no_sale_en_el_menú(self) -> None:
        Opcion.objects.create(clave="reportes", nombre="Reportes", grupo="Sistema")

        pintado = self._pintar(
            '{% opciones_del_menu "Sistema" "" as extras %}{{ extras|length }}'
        )

        self.assertEqual(pintado, "0")

    def test_un_apartado_nuevo_sale_entero(self) -> None:
        Opcion.objects.create(
            clave="reportes", nombre="Reportes", grupo="Reportes", url="/reportes/", orden=99
        )

        pintado = self._pintar(
            '{% apartados_nuevos "Resumen Facturar Comprobantes Catálogo Sistema" as nuevos %}'
            "{% for grupo, opciones in nuevos %}{{ grupo }}:{% for o in opciones %}{{ o.nombre }}{% endfor %}{% endfor %}"
        )

        self.assertEqual(pintado, "Reportes:Reportes")

    def test_sin_permiso_no_sale_en_el_menú(self) -> None:
        from django.test import override_settings

        from .comun import CERRADO

        Opcion.objects.create(
            clave="reportes", nombre="Reportes", grupo="Sistema", url="/reportes/"
        )
        with override_settings(PERSONALIZE_OPTIONS=CERRADO):
            pintado = self._pintar(
                '{% opciones_del_menu "Sistema" "" as extras %}{{ extras|length }}'
            )

        self.assertEqual(pintado, "0")
