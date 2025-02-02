"""
Модуль для разбора и сравнения данных из текстовых отчетов.
Содержит функции для обработки файлов, сравнения записей и управления UI.
"""

import re
from dataclasses import dataclass
from constant import Constant as c


@dataclass(frozen=True, slots=False)
class VS:
    """Класс для хранения версии и размера компонента."""

    version: str
    size: str


# Регулярное выражение для разбора строк отчетов
RE_PATTERN_COMPONENTS = re.compile(
    r"""
    (\W*)                      # Незначащие символы (игнорируются)
    (?P<type>\S+)\s+           # Тип компонента
    (?P<name>\S+)\s+           # Название компонента
    (?P<version>[\d\.]+)\s+    # Версия (числа и точки)
    (?P<size>[\d\s]+)\s+       # Размер (числа и пробелы)
    (?P<path>.+)$              # Путь (остаток строки)
""",
    re.VERBOSE,  # Режим для читаемого регулярного выражения
)


def parse_file(file_path: str) -> dict[str, VS]:
    """
    Разбирает текстовый файл отчета и возвращает словарь компонентов.

    Args:
        file_path (str): Путь к файлу.

    Returns:
        dict[str, VS]: Ключ — название компонента, значение — объект VS.

    Raises:
        Exception: Если возникает ошибка при чтении файла.
    """
    records = {}
    try:
        with open(file_path, "r", encoding=c.ENCODING_FILE) as file:
            for line in file:
                match = RE_PATTERN_COMPONENTS.match(line)
                if match:
                    key = match["name"]
                    value = VS(match["version"], match["size"].strip())
                    records[key] = value
    except Exception as e:
        raise e
    return records


def compare(records1: dict[str, VS], records2: dict[str, VS]):
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
        if records1[k].version != records2[k].version
        or records1[k].size != records2[k].size
    )
    return only_in_1, only_in_2, differences
