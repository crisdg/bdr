"""Validaciones del formulario de la GUI (no requieren abrir ventana)."""

import pytest
from helpers import make_row, write_workbook

from bdr_leader_merge.gui import NOMBRE_POR_DEFECTO, ValidationError, validar_entradas


@pytest.fixture
def entradas(tmp_path):
    n = write_workbook(tmp_path / "C12.xlsx", [make_row("15", "09", "000020")])
    n1 = write_workbook(tmp_path / "C13.xlsx", [make_row("15", "09", "000020")])
    salida = tmp_path / "out"
    salida.mkdir()
    return n, n1, salida


def test_nombre_vacio_usa_el_predeterminado(entradas):
    n, n1, carpeta = entradas
    _, _, destino = validar_entradas(str(n), str(n1), str(carpeta), "   ")
    assert destino.name == NOMBRE_POR_DEFECTO


def test_agrega_la_extension_si_falta(entradas):
    n, n1, carpeta = entradas
    _, _, destino = validar_entradas(str(n), str(n1), str(carpeta), "resultado")
    assert destino.name == "resultado.xlsx"


def test_respeta_el_nombre_indicado(entradas):
    n, n1, carpeta = entradas
    _, _, destino = validar_entradas(str(n), str(n1), str(carpeta), "C12_con_C13.xlsx")
    assert destino == carpeta / "C12_con_C13.xlsx"


def test_rechaza_archivo_faltante(entradas, tmp_path):
    _, n1, carpeta = entradas
    with pytest.raises(ValidationError, match="No se encuentra"):
        validar_entradas(str(tmp_path / "no_existe.xlsx"), str(n1), str(carpeta), "")


def test_rechaza_extension_distinta_de_xlsx(entradas, tmp_path):
    _, n1, carpeta = entradas
    csv = tmp_path / "datos.csv"
    csv.write_text("a,b")
    with pytest.raises(ValidationError, match="debe ser .xlsx"):
        validar_entradas(str(csv), str(n1), str(carpeta), "")


def test_acepta_extension_en_mayusculas(tmp_path):
    n = write_workbook(tmp_path / "C12.XLSX", [make_row("15", "09", "000020")])
    n1 = write_workbook(tmp_path / "C13.XLSX", [make_row("15", "09", "000020")])
    _, _, destino = validar_entradas(str(n), str(n1), str(tmp_path), "")
    assert destino.name == NOMBRE_POR_DEFECTO


def test_rechaza_archivos_iguales(entradas):
    n, _, carpeta = entradas
    with pytest.raises(ValidationError, match="deben ser distintos"):
        validar_entradas(str(n), str(n), str(carpeta), "")


def test_rechaza_campos_vacios(entradas):
    n, n1, carpeta = entradas
    with pytest.raises(ValidationError, match="Selecciona el archivo Leader n"):
        validar_entradas("", str(n1), str(carpeta), "")
    with pytest.raises(ValidationError, match="Selecciona la carpeta de salida"):
        validar_entradas(str(n), str(n1), "  ", "")


def test_rechaza_carpeta_inexistente(entradas, tmp_path):
    n, n1, _ = entradas
    with pytest.raises(ValidationError, match="carpeta de salida no existe"):
        validar_entradas(str(n), str(n1), str(tmp_path / "fantasma"), "")


def test_rechaza_nombre_con_carpetas(entradas):
    n, n1, carpeta = entradas
    with pytest.raises(ValidationError, match="no puede incluir carpetas"):
        validar_entradas(str(n), str(n1), str(carpeta), "sub/otro.xlsx")


def test_rechaza_sobrescribir_una_entrada(entradas):
    n, n1, _ = entradas
    with pytest.raises(ValidationError, match="no puede sobrescribir"):
        validar_entradas(str(n), str(n1), str(n.parent), n.name)
