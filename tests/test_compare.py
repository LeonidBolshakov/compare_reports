import pytest

from src.compare import PREFIX_COMPONENT, PREFIX_LOAD, VS, compare, parse_file
from src.constants import Constant as c


def write_report(tmp_path, name, content):
    report_path = tmp_path / name
    report_path.write_text(content, encoding=c.ENCODING_FILE)
    return report_path


def test_vs_class():
    vs = VS("1.0", 100)

    assert vs.stamp == "1.0"
    assert vs.size == 100


def test_parse_file_components(tmp_path):
    test_data = """
    Component name1 1.0 1000 path1
    Component name2 2.0 2000 path2
    """
    report_path = write_report(tmp_path, "components.txt", test_data)

    result = parse_file(str(report_path), True, False)

    assert len(result) == 2
    assert result[f"{PREFIX_COMPONENT}name1"] == VS("1.0", 1000)
    assert result[f"{PREFIX_COMPONENT}name2"] == VS("2.0", 2000)


def test_parse_file_allows_same_duplicate_component(tmp_path):
    test_data = """
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    """
    report_path = write_report(tmp_path, "components.txt", test_data)

    result = parse_file(str(report_path), True, False)

    assert result[f"{PREFIX_COMPONENT}Z_STAFFDOPREPORTS"] == VS(
        "9.1.49.0", 883209
    )


def test_parse_file_raises_on_different_duplicate_component(tmp_path):
    test_data = """
    \a RES   Z_STAFFDOPREPORTS      9.1.47.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    \a RES   Z_STAFFDOPREPORTS      9.1.49.0       883 209   .\\Z_STAFFDOPREPORTS.RES
    """
    report_path = write_report(tmp_path, "components.txt", test_data)

    with pytest.raises(ValueError, match="присутствует в исходном отчете"):
        parse_file(str(report_path), True, False)


def test_parse_file_loads(tmp_path):
    test_data = """
    module1 01\\02\\2023 10:30 1000 path1
    module2 01\\02\\2023 11:30 2000 path2
    """
    report_path = write_report(tmp_path, "loads.txt", test_data)

    result = parse_file(str(report_path), False, True)

    assert len(result) == 2
    assert result[f"{PREFIX_LOAD}module1"].stamp == "01\\02\\2023 10:30"
    assert result[f"{PREFIX_LOAD}module1"].size == 1000


def test_compare_function():
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


def test_parse_file_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_file(str(tmp_path / "nonexistent.txt"), True, True)
