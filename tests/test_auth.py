"""Pruebas del login simple con credenciales de variables de entorno.

Cubren: regla de acceso global (sin sesión todo redirige a /login),
credenciales incorrectas (no abren sesión), credenciales correctas
(crean sesión y redirigen a /), entorno sin credenciales (login imposible)
y cierre de sesión en /salir.

Usan clientes ANÓNIMOS creados a mano (app.test_client()) porque el fixture
`client` ya viene autenticado desde conftest.py.
"""

from conftest import PRUEBA_CLAVE, PRUEBA_USUARIO


def _cliente_anonimo(app):
    """Cliente de prueba SIN sesión."""
    return app.test_client()


class TestReglaDeAcceso:
    def test_get_calendario_sin_sesion_redirige_a_login(self, app):
        resp = _cliente_anonimo(app).get("/")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/login")

    def test_rutas_de_citas_y_api_redirigen_sin_sesion(self, app):
        c = _cliente_anonimo(app)
        for ruta in (
            "/citas/nueva",
            "/citas/lista",
            "/api/disponibilidad/2026-11-04",
            "/ia/propuesta",
        ):
            resp = c.get(ruta)
            assert resp.status_code == 302, f"{ruta} debería redirigir a /login"
            assert resp.headers["Location"].endswith("/login"), f"{ruta} redirigió a otro lado"

    def test_login_es_accessible_sin_sesion(self, app):
        resp = _cliente_anonimo(app).get("/login")
        assert resp.status_code == 200
        assert "Entrar" in resp.get_data(as_text=True)


class TestLogin:
    def test_credenciales_incorrectas_muestran_error_y_no_abren_sesion(self, app):
        c = _cliente_anonimo(app)
        resp = c.post("/login", data={"usuario": "otro@example.com", "clave": "clave-mala"})
        assert resp.status_code == 200
        assert "Usuario o contraseña incorrectos" in resp.get_data(as_text=True)
        # Sin sesión: las rutas protegidas siguen cerradas.
        assert c.get("/").status_code == 302

    def test_credenciales_correctas_crea_sesion_y_redirigen_a_calendario(self, app):
        c = _cliente_anonimo(app)
        resp = c.post("/login", data={"usuario": PRUEBA_USUARIO, "clave": PRUEBA_CLAVE})
        assert resp.status_code == 302
        assert not resp.headers["Location"].endswith("/login")
        # Con la sesión creada, el calendario ya responde.
        assert c.get("/").status_code == 200

    def test_sin_credenciales_en_entorno_el_login_no_abre(self, app, monkeypatch):
        monkeypatch.delenv("APP_USUARIO", raising=False)
        monkeypatch.delenv("APP_CLAVE", raising=False)
        c = _cliente_anonimo(app)
        resp = c.post("/login", data={"usuario": PRUEBA_USUARIO, "clave": PRUEBA_CLAVE})
        assert resp.status_code == 200
        assert "Usuario o contraseña incorrectos" in resp.get_data(as_text=True)
        assert c.get("/").status_code == 302


class TestSalir:
    def test_salir_cierra_la_sesion(self, app):
        c = _cliente_anonimo(app)
        c.post("/login", data={"usuario": PRUEBA_USUARIO, "clave": PRUEBA_CLAVE})
        assert c.get("/").status_code == 200

        resp = c.post("/salir")
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/login")
        # Sesión cerrada: vuelve a exigir login.
        assert c.get("/").status_code == 302
