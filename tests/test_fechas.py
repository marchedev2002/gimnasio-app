import sys
import os

#Para que el test pueda encontrar a app.py, que esta un nivel arriba
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from datetime import date
from app import calcular_siguiente_vencimiento


def test_vencimiento_mes_normal():
    """Si pago el 15 de julio, el proximo vencimiento deberia ser el 15 de agosto"""
    fecha_base = date(2026, 7, 15)
    resultado = calcular_siguiente_vencimiento(fecha_base, dia_vencimiento=15)
    assert resultado == date(2026, 8, 15)

def test_vencimiento_cruza_diciembre_a_enero():
    """Si paga en diciembre el vencimiento tiene que caer en enero del año proximo"""
    fecha_base = date(2026, 12, 10)
    resultado = calcular_siguiente_vencimiento(fecha_base, dia_vencimiento=10)
    assert resultado == date(2027, 1, 10)

def test_vencimiento_dia_31_en_mes_corto():
    """Si el dia de vencimiento es 31 pero el mes sigiuente no tiene dia 31"""
    fecha_base = date(2026, 1, 31)
    resultado = calcular_siguiente_vencimiento(fecha_base, dia_vencimiento=31)
    assert resultado == date(2026, 2, 28)


##assert es la palabra clave de los tests:
# "afirmo que esto es verdad, y si no es verdad, hace fallar el test"
# "Cada assert compara lo que tu funcion devolvio contra lo que vos esperabas que devuelva"
#     