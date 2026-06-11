import pytest
import csv
import os
from unittest import mock

from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from src.compare_reports import MyWindow
from src.compare import PREFIX_COMPONENT, parse_file, compare
from src.constants import Constant as c
from src.tunes import Tunes

# Тестовые данные
TEST_DATA_1 = """Component, Stamp, Size
DLL Button   1.0.0   1024   C:\\App\\button.dll
EXE Label    2.1.3   2048   C:\\App\\label.exe"""

TEST_DATA_2 = """Component, Stamp, Size
DLL Button   1.0.1   1024   C:\\App\\button.dll
EXE Slider   3.0.0   4096   C:\\App\\slider.exe"""


# Фикстуры для тестовых файлов
@pytest.fixture
def test_files(tmp_path):
    file1 = tmp_path / "test1.csv"
    file2 = tmp_path / "test2.csv"

    with open(file1, "w") as f:
        f.write(TEST_DATA_1)

    with open(file2, "w") as f:
        f.write(TEST_DATA_2)

    return str(file1), str(file2)


@pytest.fixture
def test_tunes(tmp_path, monkeypatch):
    tunes = {
        c.CHECK_BOX_FAST: Qt.CheckState.Unchecked.value,
        c.CHECK_BOX_SUPER_FAST: Qt.CheckState.Unchecked.value,
        c.CHECK_BOX_COMPS: Qt.CheckState.Checked.value,
        c.CHECK_BOX_LOADS: Qt.CheckState.Unchecked.value,
        c.WORKING_FOLDER: str(tmp_path),
    }
    monkeypatch.setattr(Tunes, "read_tunes", lambda self: tunes.copy())


@pytest.fixture
def qapp():
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


@pytest.fixture
def window(qapp, test_tunes):
    window = MyWindow()
    yield window
    window.close()


# Тесты для функций сравнения
class TestCompareFunctions:
    def test_parse_file(self, test_files):
        file1, _ = test_files
        result = parse_file(file1, True, True)
        assert len(result) == 2
        assert f"{PREFIX_COMPONENT}Button" in result
        assert result[f"{PREFIX_COMPONENT}Label"].stamp == "2.1.3"

    def test_compare(self, test_files):
        file1, file2 = test_files
        data1 = parse_file(file1, True, True)
        data2 = parse_file(file2, True, True)

        only1, only2, diff = compare(data1, data2)

        assert f"{PREFIX_COMPONENT}Label" in only1
        assert f"{PREFIX_COMPONENT}Slider" in only2
        assert f"{PREFIX_COMPONENT}Button" in diff


# Тесты для главного окна
class TestMainWindow:
    def test_initial_state(self, window):
        assert window.lblFilePath1.text() == ""
        assert window.lblFilePath2.text() == ""
        assert window.model.rowCount() == 0

    def test_file_selection(self, window, test_files):
        file1, file2 = test_files

        with mock.patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as mock_dialog:
            mock_dialog.return_value = (file1, None)
            window.open_file_dialog1()

            assert window.lblFilePath1.text() == file1
            assert "test1.csv" in window.lblFilePath1.text()

    def test_comparison_logic(self, window, test_files):
        file1, file2 = test_files
        window.lblFilePath1.setText(file1)
        window.lblFilePath2.setText(file2)

        window.on_click_OK()

        assert window.model.rowCount() == 3
        assert window.was_comparison is True

    def test_save_functionality(self, window, test_files, tmp_path, monkeypatch):
        file1, file2 = test_files
        window.lblFilePath1.setText(file1)
        window.lblFilePath2.setText(file2)
        window.on_click_OK()

        monkeypatch.chdir(tmp_path)
        save_path = tmp_path / "save.csv"

        window.on_click_save()

        assert os.path.exists(save_path)

        with open(save_path) as f:
            reader = csv.reader(f, delimiter=";")
            rows = list(reader)
            assert len(rows) == 4  # Header + 3 rows


# Тесты обработки ошибок
class TestErrorHandling:
    def test_missing_files_error(self, window):
        window.on_click_OK()
        assert window.model.rowCount() == 0

    def test_corrupted_file_handling(self, window, tmp_path):
        bad_file = tmp_path / "bad.csv"
        with open(bad_file, "w") as f:
            f.write("Invalid,Data\n1,2,3")

        window.lblFilePath1.setText(str(bad_file))
        window.lblFilePath2.setText(str(bad_file))

        window.on_click_OK()
        assert window.model.rowCount() == 1
