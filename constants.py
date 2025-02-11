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
    FILE_UI = r"_internal\compare_reports.ui"

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

    # Заголовки диалогов открытия файлов и директорий
    TITLE_OPEN_FIRST_REPORT = "Первый отчёт"
    TITLE_OPEN_SECOND_REPORT = "Второй отчёт"
    TITLE_SET_WORKING_FOLDER = "Выбор рабочей директории"
    TITLE_OPEN_TWO_FILES = "Выберите два файла отчётов"

    # Уточняющая информация о файлах отчётов
    TYPES_FILES_OPEN = "Текстовые файлы(*.txt);;Все файлы (*)"

    # Сообщения об ошибках
    TITLE_RESAVE = "Предупреждение"
    TEXT_RESAVE = "Новое сравнение не произведено. Сохранять нечего."
    TITLE_ERROR_FILE = "Ошибка"
    TEXT_ERROR_FILE = "Произошла ошибка:"
    TITLE_NO_COMP = "Предупреждение"
    TEXT_NO_COMP = " Выберите что надо сравнивать компоненты и/или загрузки"
    TEXT_NO_TUNES = "Ошибка в программе. Запрошена несуществующая настройка"
    TITLe_ERROR_WRITE = "Ошибка"
    TEXT_ERROR_WRITE = "Ошибка записи файла настроек"
    TEXT_ERROR_TYPE_TUNES = "Попытка записать настройку с типом не str"
    TITLE_ERROR_READ = "Ошибка"
    TEXT_ERROR_READ = (
        "Неверная информация в файле настроек.\n"
        "Программа работает с настройками по умолчанию"
    )

    # Сообщение об удачном сравнении
    TEXT_SUCCESSFUL_COMPARISON = "Различия в компонентах отчётов не обнаружены"

    # Имя файла настроек
    FILE_TUNES = "tunes.txt"

    # Признаки выбора checkBox
    CHECK_STATE_CHECKED = "2"
    CHECK_STATE_UNCHECKED = "0"

    # Имя папки Downloads
    DOWNLOADS = "Downloads"

    # Имена параметров
    CHECK_BOX_FAST = "checkBoxFast"
    CHECK_BOX_SUPER_FAST = "checkBoxSuperFast"
    CHECK_BOX_COMPS = "checkBoxComps"
    CHECK_BOX_LOADS = "checkBoxLoads"
    WORKING_FOLDER = "working_folder"

    # Типы контроля
    CHECK_BOX = "CheckBox"
    STRING = "String"
