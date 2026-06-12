"""
Модуль содержит автономные функции
"""

from pathlib import Path
import sys

from PyQt6.QtWidgets import QPushButton, QApplication, QMessageBox
from PyQt6.QtCore import QTimer

from src.constants import Constant as c


def set_bold(widget) -> None:
    """
    Устанавливает жирное начертание в тексте виджета
    :param widget:
    :return: None
    """
    font = widget.font()
    font.setBold(True)
    widget.setFont(font)


def highlight_button_if_no_file(button: QPushButton) -> bool:
    """
    Метод вызывают при ошибочных действиях пользователя.
    Устанавливает стиль кнопки, по нажатию которой надо исправить ошибку и возвращает False.
    """
    button.setStyleSheet(c.STYLE_ERROR_BUTTON)
    return False


def on_click_cancel() -> None:
    """Завершает работу приложения."""
    QApplication.quit()


def get_downloads_path() -> str:
    """
    Формирует путь на каталог Downloads
    :return: Строковое представление пути на каталог Downloads
    """
    return str(Path.home() / c.DOWNLOADS)


def set_focus(btn: QPushButton | None) -> None:
    """
    Устанавливает фокус на требуемую кнопку
    :param btn: Кнопка
    :return: None
    """
    if btn:
        btn.setFocus()


def get_base_dir(folder_level: int = 1) -> Path:
    """
    Структура проекта:
        project_root/       folder_level=1
            _Internal/
            src/            folder_level = 0
                    paths_win.py
    """
    if getattr(sys, "frozen", False):
        # запуск из exe
        base_dir = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        # запуск из исходников:
        # __file__ = project_root/src/GENERAL/paths_win.py
        # parents[0] = .../src
        # parents[1] = .../project_root
        base_dir = Path(__file__).resolve().parents[folder_level]

    return base_dir


def get_file_ui_name() -> Path:
    base_dir = get_base_dir()
    return base_dir / "_Internal" / c.FILE_UI_NAME


def show_message(parent, text: str, wait: int) -> None:
    """
    Отображает всплывающее сообщение.
    Сообщение автоматически закрывается через заданное в параметре время.
    Параметры:
    text - текст выводимого сообщения
    wait - максимальное время нахождения сообщения на экране в мс
    Если wait <= 0, сообщение не показывается.
    """
    # Создаём окно сообщения
    msg_box = QMessageBox(parent)
    msg_box.setText(text)
    msg_box.show()

    # Для закрытия окна устанавливаем таймер
    QTimer.singleShot(wait, msg_box.accept)
