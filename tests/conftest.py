import pytest

from helpers import write_workbook


@pytest.fixture
def build_wb(tmp_path):
    def _build(nombre, filas):
        return write_workbook(tmp_path / nombre, filas)

    return _build
