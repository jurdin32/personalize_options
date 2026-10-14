"""Los roles, sus permisos y el formulario y el admin que los manejan."""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.models import User
from django.test import TestCase

from personalize_options.forms import RolForm
from personalize_options.models import Nivel, Permiso, Rol
from personalize_options.opciones import todas

from .comun import rol_con


class PruebasDeLosRoles(TestCase):
    """Los roles y sus permisos, tal como se guardan."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")

    def test_un_rol_tiene_sus_opciones_y_su_nivel(self) -> None:
        rol = rol_con("Ventas", self.usuario, facturar=Nivel.ESCRITURA.value, clientes=Nivel.LECTURA.value)

        self.assertEqual(rol.nivel("facturar"), Nivel.ESCRITURA.value)
        self.assertEqual(rol.nivel("clientes"), Nivel.LECTURA.value)
        self.assertEqual(rol.nivel("productos"), "")
        self.assertEqual(
            rol.opciones, {"facturar": Nivel.ESCRITURA.value, "clientes": Nivel.LECTURA.value}
        )

    def test_no_se_puede_repetir_la_opcion_en_el_mismo_rol(self) -> None:
        rol = rol_con("Ventas", self.usuario, clientes=Nivel.LECTURA.value)

        with self.assertRaises(Exception):
            Permiso.objects.create(rol=rol, opcion="clientes", nivel=Nivel.ESCRITURA.value)

    def test_los_roles_del_usuario_se_consultan_al_reves(self) -> None:
        rol_con("Ventas", self.usuario)

        self.assertEqual([rol.nombre for rol in self.usuario.roles.all()], ["Ventas"])



class PruebasDelFormulario(TestCase):
    """El formulario del rol: se marca la matriz y se guarda."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user("quien-lleva-ventas")

    def _datos(self, **niveles: str) -> dict:
        datos = {"nombre": "Ventas", "descripcion": "Lo que llevan las ventas", "activo": "on"}
        datos.update({f"nivel_{clave}": nivel for clave, nivel in niveles.items()})
        return datos

    def test_marcar_opciones_las_guarda_con_su_nivel(self) -> None:
        formulario = RolForm(self._datos(clientes="lectura", facturar="escritura"))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        rol = formulario.save()

        self.assertEqual(
            rol.opciones, {"clientes": "lectura", "facturar": "escritura"}
        )

    def test_una_opcion_que_no_esta_en_la_lista_se_guarda_igual(self) -> None:
        # El formulario no inventa permisos: solo los de las opciones declaradas.
        Permiso.objects.create(rol=Rol.objects.create(nombre="Otro"), opcion="inventada", nivel="lectura")

        formulario = RolForm(self._datos(clientes="lectura"))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        rol = formulario.save()

        self.assertEqual(sorted(rol.opciones), ["clientes"])

    def test_volver_a_desmarcar_quita_el_permiso(self) -> None:
        formulario = RolForm(self._datos(clientes="lectura", facturar="escritura"))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        rol = formulario.save()

        otro = RolForm(
            {"nombre": "Ventas", "descripcion": "", "activo": "on", "nivel_clientes": "escritura"},
            instance=rol,
        )
        self.assertTrue(otro.is_valid(), otro.errors)
        otro.save()

        self.assertEqual(rol.opciones, {"clientes": "escritura"})

    def test_el_formulario_viene_con_lo_que_ya_estaba_marcado(self) -> None:
        rol = rol_con("Ventas", self.usuario, clientes=Nivel.LECTURA.value)

        formulario = RolForm(instance=rol)

        self.assertEqual(formulario.fields["nivel_clientes"].initial, Nivel.LECTURA.value)
        self.assertEqual(formulario.fields["nivel_productos"].initial, "")

    def test_el_nombre_del_rol_no_se_puede_repetir(self) -> None:
        Rol.objects.create(nombre="Ventas")

        formulario = RolForm(self._datos())

        self.assertFalse(formulario.is_valid())
        self.assertIn("nombre", formulario.errors)



class PruebasDelAdmin(TestCase):
    """El admin: donde se crean los roles y se marcan sus opciones."""

    def setUp(self) -> None:
        self.jefe = User.objects.create_superuser("quien-manda", "jefe@ejemplo.ec", "secreta-clave")
        self.client.force_login(self.jefe)

    def test_la_lista_y_las_pantallas_del_rol_se_abren(self) -> None:
        rol = Rol.objects.create(nombre="Ventas")

        for ruta in ("/admin/personalize_options/rol/", "/admin/personalize_options/rol/add/", f"/admin/personalize_options/rol/{rol.pk}/change/"):
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200, ruta)

    def test_la_pantalla_del_rol_trae_una_casilla_por_opcion(self) -> None:
        pagina = self.client.get("/admin/personalize_options/rol/add/").content.decode()

        for opcion in todas():
            self.assertIn(f'name="nivel_{opcion.clave}"', pagina, opcion.clave)
        self.assertIn("Sin acceso", pagina)
        self.assertIn("Lectura y escritura", pagina)

    def test_crear_un_rol_desde_el_admin_guarda_sus_permisos(self) -> None:
        respuesta = self.client.post(
            "/admin/personalize_options/rol/add/",
            {
                "nombre": "Ventas",
                "descripcion": "Lo que llevan las ventas",
                "activo": "on",
                "usuarios": [str(self.jefe.pk)],
                "nivel_clientes": Nivel.ESCRITURA.value,
                "nivel_tablero": Nivel.LECTURA.value,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        rol = Rol.objects.get(nombre="Ventas")
        self.assertEqual(rol.opciones, {"clientes": Nivel.ESCRITURA.value, "tablero": Nivel.LECTURA.value})
        self.assertEqual(list(rol.usuarios.all()), [self.jefe])

    def test_modificar_un_rol_cambia_lo_marcado(self) -> None:
        rol = rol_con("Ventas", self.jefe, clientes=Nivel.LECTURA.value)

        respuesta = self.client.post(
            f"/admin/personalize_options/rol/{rol.pk}/change/",
            {
                "nombre": "Ventas",
                "descripcion": "",
                "activo": "on",
                "usuarios": [str(self.jefe.pk)],
                "nivel_clientes": Nivel.ESCRITURA.value,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        rol.refresh_from_db()
        self.assertEqual(rol.opciones, {"clientes": Nivel.ESCRITURA.value})

    def test_las_acciones_marcan_y_quitan_las_opciones(self) -> None:
        rol = Rol.objects.create(nombre="Ventas")

        for accion, esperado in (
            ("todo_lectura", Nivel.LECTURA.value),
            ("todo_escritura", Nivel.ESCRITURA.value),
        ):
            with self.subTest(accion=accion):
                self.client.post(
                    "/admin/personalize_options/rol/",
                    {"action": accion, "_selected_action": [str(rol.pk)]},
                    follow=True,
                )
                self.assertEqual(set(rol.opciones.values()), {esperado})
                self.assertEqual(len(rol.opciones), len(todas()))

        self.client.post(
            "/admin/personalize_options/rol/",
            {"action": "quitar_todo", "_selected_action": [str(rol.pk)]},
            follow=True,
        )
        self.assertEqual(rol.opciones, {})


class PruebasDeLasTablasEnElAdmin(TestCase):
    """Las dos tablas del paquete se ven (y se retocan) en el admin."""

    def setUp(self) -> None:
        self.jefe = User.objects.create_superuser(
            "quien-manda", "jefe@ejemplo.ec", "secreta-clave"
        )
        self.client.force_login(self.jefe)

    def test_el_paquete_registra_sus_dos_tablas(self) -> None:
        registradas = {modelo._meta.label for modelo in (Rol, Permiso)}
        en_el_admin = {modelo._meta.label for modelo in admin.site._registry}

        self.assertEqual(registradas & en_el_admin, registradas)

    def test_el_indice_del_admin_lleva_a_las_dos_tablas(self) -> None:
        pagina = self.client.get("/admin/").content.decode()

        self.assertIn("/admin/personalize_options/rol/", pagina)
        self.assertIn("/admin/personalize_options/permiso/", pagina)

    def test_la_tabla_de_permisos_se_mira_y_se_retoca(self) -> None:
        rol = rol_con("Ventas", self.jefe, clientes=Nivel.LECTURA.value)
        permiso = rol.permisos.get()

        pagina = self.client.get("/admin/personalize_options/permiso/")
        self.assertEqual(pagina.status_code, 200)
        # Se enseña el nombre de la opción, no la clave que se guarda.
        self.assertIn("Clientes", pagina.content.decode())

        # Y el nivel se cambia desde la propia lista.
        respuesta = self.client.post(
            "/admin/personalize_options/permiso/",
            {
                "_save": "Guardar",
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(permiso.pk),
                "form-0-nivel": Nivel.ESCRITURA.value,
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        permiso.refresh_from_db()
        self.assertEqual(permiso.nivel, Nivel.ESCRITURA.value)
