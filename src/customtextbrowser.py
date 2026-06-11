"""
Модуль содержит класс CustomTextBrowser унаследованный от QTextBrowser.
Класс заменяет в базовом классе методы нажатия клавиши клавиатуры и двойного клика мыши
"""

import typing

from PyQt6.QtWidgets import QTextBrowser
from PyQt6.QtCore import Qt


class CustomTextBrowser(QTextBrowser):
    def __init__(self, parent):
        super().__init__(parent)
        self.event_handler: typing.Callable | None = None

    def keyPressEvent(self, event):
        """
         Переопределяет обработку нажатия клавиш.
         При нажатии на клавишу Ввод, вызывается пользовательская функция.
         Остальные клавиши обрабатываются базовым классом
        :param event:
        :return:
        """

        # Проверяем, была ли нажата клавиша Enter или Return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if callable(self.event_handler):
                self.event_handler()
                event.accept()  # Предотвращаем дальнейшую обработку события
        else:
            super().keyPressEvent(event)  # Стандартная обработка для других клавиш

    def mouseDoubleClickEvent(self, *args, **kwargs):
        """
        Переопределяет двойной клик мыши. При двойном клике вызывается пользовательская функция.
        :param args:
        :param kwargs:
        :return:
        """
        if callable(self.event_handler):
            self.event_handler()

    def connect(self, event_handler):
        """
        Принимает пользовательскую функцию для возможного последующего вызова
        :param event_handler: Пользовательская функция
        :return:
        """
        if callable(event_handler):
            self.event_handler = event_handler
