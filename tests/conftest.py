import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Chequeo de seguridad: nunca correr los tests contra la base real ---
REQUERIDAS = ['DB_HOST', 'DB_PORT', 'DB_USER', 'DB_PASSWORD', 'DB_NAME', 'SECRET_KEY']
faltantes = [v for v in REQUERIDAS if not os.environ.get(v)]
if faltantes:
    raise RuntimeError(
        f"Faltan variables de entorno para correr los tests: {', '.join(faltantes)}. "
        "Definilas apuntando a tu base de TEST antes de correr pytest."
    )

if os.environ.get('DB_NAME') == 'defaultdb':
    raise RuntimeError(
        "¡PELIGRO! DB_NAME apunta a 'defaultdb' (producción). "
        "Los tests borran datos. Configurá DB_NAME='test_gimnasio' antes de correr pytest."
    )

import pytest
from app import app as flask_app, get_connection

@pytest.fixture
def app():
    flask_app.config.update({"TESTING": True})
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def limpiar_base():
    """Antes de cada test, deja USUARIO/PAGO/ASISTENCIA vacio, para que cada
    test arranque desde un estado limpio"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ASISTENCIA")
    cursor.execute("DELETE FROM PAGO")
    cursor.execute("DELETE FROM USUARIO")
    conn.commit()
    cursor.close()
    conn.close()
    yield
        