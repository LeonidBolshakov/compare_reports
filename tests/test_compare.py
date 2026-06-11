# test_compare.py

import pytest

from src.compare import PREFIX_COMPONENT, PREFIX_LOAD, VS, parse_file, compare


def test_vs_class():
    # Тест создания объекта VS
    vs = VS("1.0", 100)
    assert vs.stamp == "1.0"
    assert vs.size == 100


def test_parse_file_components():
    # Тест парсинга файла с компонентами
    test_data = """
    Component name1 1.0 1000 path1
    Component name2 2.0 2000 path2
    """
    with open("test_components.txt", "w") as f:
        f.write(test_data)

    result = parse_file("test_components.txt", True, False)
    assert len(result) == 2
    assert result[f"{PREFIX_COMPONENT}name1"] == VS("1.0", 1000)
    assert result[f"{PREFIX_COMPONENT}name2"] == VS("2.0", 2000)


def test_parse_file_allows_same_duplicate_component():
    test_data = """
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    """
    with open("test_components.txt", "w") as f:
        f.write(test_data)

    result = parse_file("test_components.txt", True, False)

    assert result[f"{PREFIX_COMPONENT}Z_STAFFDOPREPORTS"] == VS("9.1.49.0", 883209)


def test_parse_file_raises_on_different_duplicate_component(monkeypatch):
    test_data = """
    \a RES   Z_STAFFDOPREPORTS      9.1.47.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    """
    with open("test_components.txt", "w") as f:
        f.write(test_data)

    monkeypatch.setattr("src.compare.QMessageBox.critical", lambda *args: None)

    with pytest.raises(ValueError, match="присутствует в исходном отчете"):
        parse_file("test_components.txt", True, False)


def test_parse_file_loads():
    # Тест парсинга файла с загруженными модулями
    test_data = """
    module1 01\\02\\2023 10:30 1000 path1
    module2 01\\02\\2023 11:30 2000 path2
    """
    with open("test_loads.txt", "w") as f:
        f.write(test_data)

    result = parse_file("test_loads.txt", False, True)
    assert len(result) == 2
    assert result[f"{PREFIX_LOAD}module1"].stamp == "01\\02\\2023 10:30"
    assert result[f"{PREFIX_LOAD}module1"].size == 1000


def test_compare_function():
    # Тест функции сравнения
    records1 = {
        "comp1": VS("1.0", 100),
        "comp2": VS("2.0", 200),
        "comp3": VS("3.0", 300),
    }

    records2 = {
        "comp2": VS("2.1", 200),
        "comp3": VS("3.0", 300),
        "comp4": VS("4.0", 400),
    }

    only_in_1, only_in_2, differences = compare(records1, records2)

    assert only_in_1 == {"comp1"}
    assert only_in_2 == {"comp4"}
    assert differences == {"comp2"}


def test_parse_file_invalid(monkeypatch):
    # Тест обработки некорректного файла
    monkeypatch.setattr("src.compare.QMessageBox.critical", lambda *args: None)

    with pytest.raises(FileNotFoundError):
        parse_file("nonexistent.txt", True, True)
