"""El registro de opciones: de dónde salen las claves del menú."""

from __future__ import annotations

from unittest.mock import patch

from django.test import TestCase

from personalize_options.models import Nivel, Opcion, Permiso, Rol
from personalize_options.opciones import (
    DE_SERIE,
    de,
    existe,
    grupos,
    opciones_de_choices,
    por_clave,
    todas,
)


class PruebasDeLasOpciones(TestCase):
    """El registro de opciones: una sola lista, sin repetidos."""

    def test_las_claves_son_unicas(self) -> None:
        claves = [opcion.clave for opcion in todas()]

        self.assertEqual(len(claves), len(set(claves)))
        self.assertEqual(set(claves), set(por_clave()))

    def test_cada_opcion_esta_en_un_grupo_y_los_grupos_son_los_del_menu(self) -> None:
        apartados = [grupo for grupo, _ in grupos()]

        self.assertEqual(len(apartados), len(set(apartados)))
        for opcion in todas():
            self.assertIn(opcion.grupo, apartados, opcion.clave)

        # Ningún grupo vacío, y entre todos están todas las opciones.
        en_grupos = [opcion.clave for _, opciones in grupos() for opcion in opciones]
        self.assertEqual(sorted(en_grupos), sorted(por_clave()))

    def test_las_opciones_del_menu_se_llaman_igual_que_las_del_registro(self) -> None:
        # Las claves que usa el menú del proyecto, que es lo que se protege.
        del_menu = {
            "tablero", "facturar", "facturas", "notas_credito", "notas_debito",
            "liquidaciones_compra", "guias_remision", "retenciones", "productos",
            "clientes", "conductores", "vehiculos", "inventario", "configuracion",
            "roles", "usuarios", "opciones",
        }
        self.assertEqual(del_menu, set(por_clave()))

    def test_ayudas(self) -> None:
        self.assertTrue(existe("clientes"))
        self.assertFalse(existe("inventada"))
        self.assertEqual(de("clientes").nombre, "Clientes")
        self.assertEqual(
            [clave for clave, _ in opciones_de_choices()], [opcion.clave for opcion in todas()]
        )


class PruebasDeLasOpcionesEnLaBase(TestCase):
    """Las opciones viven en la base: se crean y se cambian sin tocar código."""

    def test_las_opciones_de_serie_estan_sembradas(self) -> None:
        de_serie = {ficha.clave for ficha in DE_SERIE}

        self.assertTrue(de_serie)
        self.assertLessEqual(de_serie, set(por_clave()))

    def test_se_puede_crear_una_opción_y_sale_en_su_apartado(self) -> None:
        Opcion.objects.create(clave="reportes", nombre="Reportes", grupo="Sistema", orden=99)

        self.assertTrue(existe("reportes"))
        self.assertEqual(de("reportes").nombre, "Reportes")
        apartados = dict(grupos())
        self.assertIn("reportes", [opcion.clave for opcion in apartados["Sistema"]])

    def test_una_opción_apagada_no_cuenta_pero_sigue_guardada(self) -> None:
        Opcion.objects.create(clave="reportes", nombre="Reportes", grupo="Sistema", activo=False)

        self.assertNotIn("reportes", {opcion.clave for opcion in todas(solo_activas=True)})
        self.assertIn("reportes", por_clave())

    def test_cambiarle_la_clave_se_lleva_los_permisos(self) -> None:
        rol = Rol.objects.create(nombre="Ventas")
        Permiso.objects.create(rol=rol, opcion="clientes", nivel=Nivel.ESCRITURA.value)
        opcion = de("clientes")

        opcion.clave = "clientela"
        opcion.save()

        self.assertFalse(Permiso.objects.filter(opcion="clientes").exists())
        self.assertEqual(rol.opciones, {"clientela": Nivel.ESCRITURA.value})

    def test_borrar_una_opción_se_lleva_sus_permisos(self) -> None:
        rol = Rol.objects.create(nombre="Ventas")
        Permiso.objects.create(rol=rol, opcion="clientes", nivel=Nivel.LECTURA.value)

        de("clientes").delete()

        self.assertFalse(Permiso.objects.filter(opcion="clientes").exists())
        self.assertFalse(existe("clientes"))

    def test_si_la_tabla_no_está_todavía_se_usan_las_de_serie(self) -> None:
        # Un paquete recién añadido, sin migrar: el registro no puede reventar.
        from django.db.utils import ProgrammingError

        with patch("personalize_options.opciones._modelo", side_effect=ProgrammingError):
            self.assertEqual(
                {opcion.clave for opcion in todas()},
                {ficha.clave for ficha in DE_SERIE},
            )
