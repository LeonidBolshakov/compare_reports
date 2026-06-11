"""
Модуль для разбора и сравнения данных из текстовых отчетов.
Содержит функции для обработки файлов и сравнения записей.
"""

import re
from dataclasses import dataclass

from PyQt6.QtWidgets import QMessageBox

from src.constants import Constant as c

PREFIX_COMPONENT = "C: "
PREFIX_LOAD = "L: "


@dataclass(frozen=True, slots=False)
class VS:
    """Класс для хранения версии и размера компонента."""

    stamp: str
    size: int


# Регулярное выражение для разбора строк информации о компонентах
RE_PATTERN_COMPONENTS = re.compile(
    r"""
    \W*                 # Незначащие символы, игнорируются
    (?P<type>\S+)       # Тип компонента
    \s+
    (?P<name>\S+)       # Название компонента
    \s+
    (?P<stamp>[\d.]+)   # Версия компонента
    \s+
    (?P<size>[\d\s]+)   # Размер, числа и пробелы
    \s+
    (?P<path>.+)        # Путь, остаток строки
    """,
    re.VERBOSE,
)

# Регулярное выражение для разбора строк загруженных модулей

RE_PATTERN_LOADS = re.compile(
    r"""
    \s*                                          # Пробелы, игнорируются
    (?P<name>\S+)                                # Название элемента загрузки
    \s+
    (?P<stamp>\d{2}\\\d{2}\\\d{4}\s\d{2}:\d{2})  # Дата/время: ДД\ММ\ГГГГ ЧЧ:ММ
    \s+
    (?P<size>[\d\s]+)                            # Размер, числа и пробелы
    \s+
    (?P<path>.+)                                 # Путь, остаток строки
    """,
    re.VERBOSE,
)


def parse_file(
    file_path: str, compare_comps: bool, compare_loads: bool
) -> dict[str, VS]:
    """
    Разбирает текстовый файл отчета и возвращает словарь компонентов и/или загруженных модулей.

    Args:
        file_path (str): Путь к файлу
        compare_comps (bool): Признак того, что надо сравнивать компоненты
        compare_loads (bool): Признак того, что надо сравнивать загрузки

    Returns:
        dict[str, VS]: Ключ — название компонента/модуля, значение — объект VS.

    Raises:
        Exception: Если возникает ошибка при чтении файла.
    """
    result: dict[str, VS] = {}
    try:
        with open(file_path, "r", encoding=c.ENCODING_FILE) as file:
            for line in file:
                if compare_loads:
                    add_parsed_line_to_result(RE_PATTERN_LOADS, line, result)

                if compare_comps:
                    add_parsed_line_to_result(RE_PATTERN_COMPONENTS, line, result)

    except Exception as e:
        QMessageBox.critical(None, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE}\n{e}")
        raise e
    return result


def add_parsed_line_to_result(
    re_pattern: re.Pattern,
    line: str,
    result: dict[str, VS],
) -> None:
    match_result = re_pattern.match(line)
    if not match_result:
        return

    data = match_result.groupdict()

    prefix = PREFIX_LOAD if re_pattern is RE_PATTERN_LOADS else PREFIX_COMPONENT

    name = prefix + data["name"]
    stamp = data["stamp"]
    size = int("".join(data["size"].split()))
    parsed_state = VS(stamp=stamp, size=size)

    if name not in result:
        result[name] = parsed_state
    elif result[name] != parsed_state:
        raise ValueError(
            f"{name} присутствует в исходном отчете с разными характеристиками: "
            f"версия/дата: {result[name].stamp}, размер: {result[name].size}; "
            f"версия/дата: {parsed_state.stamp}, размер: {parsed_state.size}"
        )


def compare(records1: dict[str, VS], records2: dict[str, VS]) -> tuple[set, set, set]:
    """
    Сравнивает два набора записей и возвращает различия.

    Args:
        records1 (dict): Данные первого отчета.
        records2 (dict): Данные второго отчета.

    Returns:
        tuple: (only_in_1, only_in_2, differences) — множества уникальных и измененных компонентов.
    """
    only_in_1 = set(records1) - set(records2)
    only_in_2 = set(records2) - set(records1)
    differences = set(
        k
        for k in records1.keys() & records2.keys()
        if records1[k].stamp != records2[k].stamp
        or records1[k].size != records2[k].size
    )
    return only_in_1, only_in_2, differences
