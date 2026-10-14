"""Qué puede cada quien, y cómo llegan esos permisos a la petición."""

from __future__ import annotations

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

from personalize_options import conf, permisos
from personalize_options.middleware import PermisosMiddleware
from personalize_options.models import Nivel
from personalize_options.opciones import todas

from .comun import CERRADO, SIN_ROLES, rol_con


class PruebasDeLaResolucion(TestCase):
    """Qué puede cada quien: sin rol, con rol, con varios y superusuario."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")

    @override_settings(PERSONALIZE_OPTIONS=SIN_ROLES)
    def test_en_modo_abierto_quien_no_tiene_rol_puede_todo(self) -> None:
        quien = permisos.de(self.usuario)

        self.assertTrue(quien.puede_escribir("clientes"))
        self.assertEqual(quien.visibles, {opcion.clave for opcion in todas()})

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_en_modo_cerrado_quien_no_tiene_rol_no_puede_nada(self) -> None:
        quien = permisos.de(self.usuario)

        self.assertFalse(quien.puede_leer("clientes"))
        self.assertFalse(quien.puede_escribir("clientes"))
        self.assertEqual(quien.visibles, set())

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_lo_que_no_marca_el_rol_no_se_puede(self) -> None:
        rol_con("Ventas", self.usuario, facturar=Nivel.ESCRITURA.value, clientes=Nivel.LECTURA.value)
        quien = permisos.de(self.usuario)

        self.assertTrue(quien.puede_escribir("facturar"))
        self.assertTrue(quien.puede_leer("facturar"))
        self.assertTrue(quien.puede_leer("clientes"))
        self.assertFalse(quien.puede_escribir("clientes"))
        self.assertFalse(quien.puede_leer("productos"))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_con_varios_roles_manda_el_nivel_mas_alto(self) -> None:
        rol_con("Consulta", self.usuario, clientes=Nivel.LECTURA.value)
        rol_con("Ventas", self.usuario, clientes=Nivel.ESCRITURA.value, productos=Nivel.LECTURA.value)
        quien = permisos.de(self.usuario)

        self.assertEqual(quien.nivel("clientes"), Nivel.ESCRITURA.value)
        self.assertTrue(quien.puede_escribir("clientes"))
        self.assertEqual(quien.visibles, {"clientes", "productos"})

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_un_rol_apagado_no_da_nada(self) -> None:
        rol = rol_con("Ventas", self.usuario, clientes=Nivel.ESCRITURA.value)
        rol.activo = False
        rol.save()

        self.assertFalse(permisos.de(self.usuario).puede_leer("clientes"))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_el_superusuario_puede_todo_aunque_no_tenga_rol(self) -> None:
        jefe = User.objects.create_superuser("quien-manda", "jefe@ejemplo.ec", "secreta-clave")

        self.assertTrue(permisos.de(jefe).puede_escribir("configuracion"))

    @override_settings(PERSONALIZE_OPTIONS={"MODO": "cerrado", "SUPERUSUARIOS_TODO": False})
    def test_al_superusuario_se_le_puede_quitar_ese_atajo(self) -> None:
        jefe = User.objects.create_superuser("quien-manda", "jefe@ejemplo.ec", "secreta-clave")

        self.assertFalse(permisos.de(jefe).puede_leer("configuracion"))

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_una_clave_que_no_es_opcion_no_se_protege(self) -> None:
        # Si alguien se equivoca con el nombre en un decorador, no se cierra todo.
        self.assertTrue(permisos.de(self.usuario).puede_escribir("lo-que-sea"))

    @override_settings(PERSONALIZE_OPTIONS=SIN_ROLES)
    def test_sin_identificarse_no_se_puede_nada(self) -> None:
        quien = permisos.de(None)

        self.assertFalse(quien.puede_leer("clientes"))
        self.assertEqual(quien.visibles, set())

    @override_settings(PERSONALIZE_OPTIONS=SIN_ROLES)
    def test_los_ajustes_se_leen_de_settings(self) -> None:
        self.assertEqual(conf.modo(), "abierto")
        self.assertTrue(conf.es_abierto())
        self.assertTrue(conf.superusuarios_todo())

    def test_sin_ajustes_en_settings_se_usa_lo_de_serie(self) -> None:
        with self.settings(PERSONALIZE_OPTIONS=None):
            self.assertEqual(conf.modo(), conf.MODO_ABIERTO)
        with self.settings(PERSONALIZE_OPTIONS={"MODO": "lo-que-sea"}):
            self.assertEqual(conf.modo(), conf.MODO_ABIERTO)



class PruebasDelMiddleware(TestCase):
    """Los permisos quedan colgados de la petición, una vez por vuelta."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")

    @override_settings(PERSONALIZE_OPTIONS=CERRADO)
    def test_deja_los_permisos_en_la_peticion(self) -> None:
        rol_con("Ventas", self.usuario, clientes=Nivel.LECTURA.value)
        visto = {}

        def _vista(peticion):
            visto["quien"] = peticion.permisos
            return HttpResponse("hola")

        peticion = RequestFactory().get("/")
        peticion.user = self.usuario
        respuesta = PermisosMiddleware(_vista)(peticion)

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsInstance(visto["quien"], permisos.Permisos)
        self.assertTrue(visto["quien"].puede_leer("clientes"))
