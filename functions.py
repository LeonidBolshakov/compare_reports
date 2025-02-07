"""
Модуль содержит автономные функции
"""

from pathlib import Path

from PyQt6.QtWidgets import QPushButton, QApplication

from constants import Constant as c


def set_bold(widget):
    """
    Устанавливает жирное начертание в тексте виджета
    :param widget:
    :return:
    """
    font = widget.font()
    font.setBold(True)
    widget.setFont(font)
    return widget


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
    :return: Строковое представление пути
    """
    return str(Path.home() / c.DOWNLOADS)


def get_sign_fast_dialogue() -> int:
    """
    Возвращает значение признака сокращённого интерфейса.
    Признак читается из файла.
    Если файла нет или возникли проблемы с чтением файла, то считается что интерфейс полный.
    :return: True Если установлен признак сокращённого интерфейса. False в противном случае.
    """
    # noinspection PyBroadException
    try:
        with open(c.FILE_TUNES, "r") as tunes:
            check_state = int(tunes.read(1))
            return (
                check_state
                if check_state in (c.CHECKSTATE_CHECKED, c.CHECKSTATE_UNCHECKED)
                else c.CHECKSTATE_UNCHECKED
            )
    except:
        return c.CHECKSTATE_UNCHECKED
