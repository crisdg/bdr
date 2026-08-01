import pytest

from helpers import make_row

from bdr_leader_merge.merge import merge_estimados
from bdr_leader_merge.model import ceil_estimado, normalize_code, parse_estimado


class TestNormalizacion:
    @pytest.mark.parametrize(
        "entrada,esperado",
        [
            ("000015", "15"),
            (15, "15"),
            (15.0, "15"),
            ("15", "15"),
            ("09", "9"),
            ("000000", "0"),
            (None, ""),
            ("  15  ", "15"),
        ],
    )
    def test_normalize_code(self, entrada, esperado):
        assert normalize_code(entrada) == esperado

    @pytest.mark.parametrize(
        "entrada,esperado", [("000020", 20.0), (20, 20.0), (None, 0.0), ("", 0.0)]
    )
    def test_parse_estimado(self, entrada, esperado):
        assert parse_estimado(entrada) == esperado

    @pytest.mark.parametrize(
        "entrada,esperado", [(9.45, 10), (21.0, 21), (0.5, 1), (0.0, 0), (135.00000000000003, 135)]
    )
    def test_ceil_estimado(self, entrada, esperado):
        assert ceil_estimado(entrada) == esperado


class TestCruce:
    def test_clave_en_ambas_suma_5_por_ciento(self):
        n = [make_row("000015", "09", "000020")]
        n1 = [make_row("000015", "09", "000020")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 21  # 20 + 1
        assert res.report.cruces_exactos == 1
        assert res.filas_nuevas == []

    def test_fraccion_escala_al_entero_siguiente(self):
        n = [make_row("000078", "09", "000009")]
        n1 = [make_row("000078", "09", "000009")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 10  # 9 + 0.45 -> 9.45 -> 10

    def test_clave_exclusiva_de_n1_solo_lleva_el_5_por_ciento(self):
        n = [make_row("000015", "09", "000020")]
        n1 = [make_row("000999", "01", "000200")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 20  # sin aporte
        assert res.filas_nuevas == [(0, 10)]  # 5 % de 200
        assert res.report.filas_nuevas == 1

    def test_material_igual_tipo_distinto_va_a_la_primera_ocurrencia(self):
        n = [
            make_row("000500", "07", "000010"),
            make_row("000600", "01", "000010"),
        ]
        n1 = [make_row("000500", "01", "000200")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 20  # 10 + 5 % de 200
        assert res.estimados_base[1] == 10  # intacta
        assert res.report.cruces_por_material == 1
        assert res.report.cruces_exactos == 0
        assert res.filas_nuevas == []

    def test_tipo_exacto_tiene_prioridad_sobre_el_material(self):
        n = [
            make_row("000500", "07", "000010"),
            make_row("000500", "01", "000010"),
        ]
        n1 = [make_row("000500", "01", "000200")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 10  # no recibe nada
        assert res.estimados_base[1] == 20  # 10 + 10
        assert res.report.cruces_exactos == 1
        assert res.report.cruces_por_material == 0

    def test_aportes_multiples_se_acumulan_antes_del_techo(self):
        # 10 + 5 % de 2500 + 5 % de 10 = 135.5 -> 136 (techo una sola vez)
        n = [make_row("901035", "09", "000010")]
        n1 = [
            make_row("901035", "04", "002500"),
            make_row("901035", "09", "000010"),
        ]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 136
        assert res.report.cruces_exactos == 1
        assert res.report.cruces_por_material == 1

    def test_clave_duplicada_en_n_recibe_el_aporte_una_sola_vez(self):
        n = [
            make_row("500778", "04", "000030"),
            make_row("500778", "04", "000000"),
        ]
        n1 = [make_row("500778", "04", "000030")]
        res = merge_estimados(n, n1)
        assert res.estimados_base[0] == 32  # 30 + 1.5 -> 31.5 -> 32
        assert res.estimados_base[1] == 0  # la duplicada no recibe nada
        assert ("500778", "04".lstrip("0")) in res.report.claves_duplicadas_n

    def test_filas_de_n_sin_par_en_n1_quedan_igual(self):
        n = [make_row("000015", "09", "000020"), make_row("000015", "14", "000000")]
        n1 = []
        res = merge_estimados(n, n1)
        assert res.estimados_base == {0: 20, 1: 0}
        assert res.report.filas_resultado == 2

    def test_conteo_de_filas_resultado(self):
        n = [make_row("1", "1", "10"), make_row("2", "1", "10")]
        n1 = [make_row("1", "1", "20"), make_row("3", "1", "20"), make_row("4", "1", "20")]
        res = merge_estimados(n, n1)
        assert res.report.filas_resultado == 4
        assert res.report.filas_n == 2
        assert res.report.filas_n1 == 3
