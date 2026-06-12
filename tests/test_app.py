import csv
from unittest.mock import patch

import pytest
from PyQt6 import QtWidgets
from PyQt6.QtCore import Qt

from src.compare import PREFIX_COMPONENT, compare, parse_file
from src.compare_reports import MyWindow
from src.constants import Constant as c
from src.tunes import Tunes

TEST_DATA_1 = """Component, Stamp, Size
DLL Button   1.0.0   1024   C:\\App\\button.dll
EXE Label    2.1.3   2048   C:\\App\\label.exe"""

TEST_DATA_2 = """Component, Stamp, Size
DLL Button   1.0.1   1024   C:\\App\\button.dll
EXE Slider   3.0.0   4096   C:\\App\\slider.exe"""


@pytest.fixture
def test_files(tmp_path):
    file1 = tmp_path / "test1.csv"
    file2 = tmp_path / "test2.csv"
    file1.write_text(TEST_DATA_1, encoding=c.ENCODING_FILE)
    file2.write_text(TEST_DATA_2, encoding=c.ENCODING_FILE)
    return str(file1), str(file2)


@pytest.fixture
def test_tunes(tmp_path, monkeypatch):
    tunes = {
        c.CHECK_BOX_FAST: Qt.CheckState.Unchecked.value,
        c.CHECK_BOX_SUPER_FAST: Qt.CheckState.Unchecked.value,
        c.CHECK_BOX_COMPS: Qt.CheckState.Checked.value,
        c.CHECK_BOX_LOADS: Qt.CheckState.Unchecked.value,
        c.SAVER_FOLDER: str(tmp_path),
    }
    monkeypatch.setattr(Tunes, "_read_tunes", lambda self: tunes.copy())
    monkeypatch.setattr(Tunes, "_write_tunes", lambda self: None)


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

        only1, only2, differences = compare(data1, data2)

        assert f"{PREFIX_COMPONENT}Label" in only1
        assert f"{PREFIX_COMPONENT}Slider" in only2
        assert f"{PREFIX_COMPONENT}Button" in differences


class TestMainWindow:
    def test_initial_state(self, window):
        assert window.lblFilePath1.text() == ""
        assert window.lblFilePath2.text() == ""
        assert window.model.rowCount() == 0

    def test_file_selection(self, window, test_files):
        file1, _ = test_files

        with patch("PyQt6.QtWidgets.QFileDialog.getOpenFileName") as file_dialog:
            file_dialog.return_value = (file1, None)
            window.select_first_report()

        assert window.lblFilePath1.text() == file1
        assert "test1.csv" in window.lblFilePath1.text()

    def test_comparison_logic(self, window, test_files):
        file1, file2 = test_files
        window.lblFilePath1.setText(file1)
        window.lblFilePath2.setText(file2)

        window.compare_reports()

        assert window.model.rowCount() == 3
        assert window.was_comparison is True

    def test_save_functionality(self, window, test_files, tmp_path):
        file1, file2 = test_files
        window.lblFilePath1.setText(file1)
        window.lblFilePath2.setText(file2)
        window.compare_reports()
        save_path = tmp_path / "compare_test.csv"

        with (
            patch.object(window, "get_result_file_path", return_value=save_path),
            patch("src.compare_reports.f.show_message"),
        ):
            window.save_results()

        assert save_path.exists()
        assert window.was_comparison is False

        with save_path.open(encoding="utf-8-sig") as csv_file:
            rows = list(csv.reader(csv_file, delimiter=";"))

        assert rows[0] == c.LIST_HEADER_COLUMNS
        assert len(rows) == 4


class TestErrorHandling:
    def test_missing_files_error(self, window):
        window.compare_reports()

        assert window.model.rowCount() == 0

    def test_unrecognized_file_has_no_differences(self, window, tmp_path):
        bad_file = tmp_path / "bad.csv"
        bad_file.write_text("Invalid,Data\n1,2,3", encoding=c.ENCODING_FILE)
        window.lblFilePath1.setText(str(bad_file))
        window.lblFilePath2.setText(str(bad_file))

        window.compare_reports()

        assert window.model.rowCount() == 1
        assert window.model.index(0, 0).data() == c.TEXT_SUCCESSFUL_COMPARISON
