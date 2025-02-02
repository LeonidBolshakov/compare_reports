"""
Модуль содержит константы и настройки, используемые в приложении.
Все значения заданы как атрибуты неизменяемого класса Constant.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=False)
class Constant:
    """Класс для хранения констант приложения."""

    # Кодировка для чтения/записи файлов
    ENCODING_FILE = "OEM"

    # Стиль кнопки при ошибке (желтый фон, красная рамка)
    STYLE_ERROR_BUTTON = "background-color: #ffff00; border: 2px solid red;"

    # Путь к файлу интерфейса Qt
    FILE_UI = "compare_reports.ui"

    # Тексты кнопок
    TEXT_BUTTON_COMPARE = "Сравнить"
    TEXT_BUTTON_SAVE = "Сохранить"
    TEXT_BUTTON_QUIT = "Выйти"

    # Заголовки столбцов таблицы
    LIST_HEADER_COLUMNS = [
        "Компонент",
        "Отчёт 1\nверсия",
        "Отчёт 1\nразмер",
        "Отчёт 2\nверсия",
        "Отчёт 2\nразмер",
    ]

    # Заголовки диалогов открытия файлов
    TITLE_OPEN_FIRST_REPORT = "Первый сводный отчёт"
    TITLE_OPEN_SECOND_REPORT = "Второй сводный отчёт"

    # Фильтры для выбора файлов
    TYPES_FILES_OPEN = "Текстовые файлы(*.txt);;Все файлы (*)"

    # Сообщения об ошибках
    RESAVE_TEXT = "Новое сравнение не произведено. Сохранять нечего"
    TITLE_ERROR_FILE = "Ошибка"
    TEXT_ERROR_FILE = "Произошла ошибка:"
