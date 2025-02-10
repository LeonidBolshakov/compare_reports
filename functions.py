"""
Модуль содержит автономные функции
"""

from pathlib import Path
from PyQt6.QtWidgets import QPushButton, QApplication

from constants import Constant as c


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


def on_cancel() -> None:
    """Завершает работу приложения."""
    QApplication.quit()


def get_downloads_path() -> str:
    """
    Формирует путь на каталог Downloads
    :return: Строковое представление пути на каталог Downloads
    """
    return str(Path.home() / c.DOWNLOADS)
