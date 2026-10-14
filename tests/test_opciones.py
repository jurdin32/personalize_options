"""El registro de opciones: de dónde salen las claves del menú."""

from __future__ import annotations

from django.test import TestCase

from personalize_options.opciones import (
    GRUPOS,
    OPCIONES,
    POR_CLAVE,
    de,
    existe,
    opciones_de_choices,
)


class PruebasDeLasOpciones(TestCase):
    """El registro de opciones: una sola lista, sin repetidos."""

    def test_las_claves_son_unicas(self) -> None:
        claves = [opcion.clave for opcion in OPCIONES]

        self.assertEqual(len(claves), len(set(claves)))
        self.assertEqual(set(claves), set(POR_CLAVE))

    def test_cada_opcion_esta_en_un_grupo_y_los_grupos_son_los_del_menu(self) -> None:
        grupos = [grupo for grupo, _ in GRUPOS]

        self.assertEqual(len(grupos), len(set(grupos)))
        for opcion in OPCIONES:
            self.assertIn(opcion.grupo, grupos, opcion.clave)

        # Ningún grupo vacío, y entre todos están todas las opciones.
        en_grupos = [opcion.clave for _, opciones in GRUPOS for opcion in opciones]
        self.assertEqual(sorted(en_grupos), sorted(POR_CLAVE))

    def test_las_opciones_del_menu_se_llaman_igual_que_las_del_registro(self) -> None:
        # Las claves que usa el menú del proyecto, que es lo que se protege.
        del_menu = {
            "tablero", "facturar", "facturas", "notas_credito", "notas_debito",
            "liquidaciones_compra", "guias_remision", "retenciones", "productos",
            "clientes", "conductores", "vehiculos", "inventario", "configuracion",
            "roles", "usuarios",
        }
        self.assertEqual(del_menu, set(POR_CLAVE))

    def test_ayudas(self) -> None:
        self.assertTrue(existe("clientes"))
        self.assertFalse(existe("inventada"))
        self.assertEqual(de("clientes").nombre, "Clientes")
        self.assertEqual(
            [clave for clave, _ in opciones_de_choices()], [opcion.clave for opcion in OPCIONES]
        )
