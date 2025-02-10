""" Модуль содержит класс работы с настройками и dataclass, описывающий структуру информации о настройки.
    Настройки хранятся в словаре.
    Ключами словаря являются имя настройки, а значениями - значения настроек."""

import json
from dataclasses import dataclass

from PyQt6.QtWidgets import QMessageBox
from PyQt6.uic.Compiler.qtproxies import QtWidgets

import functions as f
from constants import Constant as c


@dataclass
class VT:
    value: str  # Значение по умолчанию
    type: str  # Метод контроля


class Tunes(QtWidgets.QWidget):
    """Работа с настройками"""

    def __init__(self, description_tunes: dict[str, VT]) -> None:
        """
        Инициализация объекта класса
        :param description_tunes (dict): Имя настройки: (значение по умолчанию, метод контроля)
        """
        super().__init__(self)

        self.description_tunes = description_tunes
        self.dict_tunes: dict[str, str] = self.read_tunes()  # словарь настроек

    def get_tune(self, name: str) -> str:
        """
        Получение настройки
        :param name: Имя настройки
        :return: Значение настройки
        """
        if name in self.dict_tunes:
            return self.dict_tunes[name]
        else:
            raise ValueError(f"{c.TEXT_NO_TUNES} - {name}")

    def put_tune(self, name: str, value: str, write: bool = False) -> None:
        """
        Запись настройки
        :param name: Имя настройки
        :param value: Значение настройки
        :param write: Параметр, определяющий следует ли записывать словарь в файл.
        :return: None
        """
        if not (isinstance(name, str) and isinstance(value, str)):
            raise ValueError(
                f"{c.TEXT_ERROR_TYPE_TUNES}. Имя {type(name)} Значение {type(str)}"
            )
        self.dict_tunes[name] = value
        if write:
            self.write_tunes()

    def get_default_tunes(self) -> dict[str, str]:
        """
        Возвращает словарь настроек, со значениями по умолчанию
        :return: Словарь настроек, со значениями по умолчанию
        """
        default_tunes = {
            key: self.description_tunes[key].value
            for key in self.description_tunes.keys()
        }
        #  У настройки WORKING_FOLDER значение по умолчанию - путь к папке Downloads.
        #  Путь к Downloads может быть разным на разных компьютерах, поэтому он формируется программно.
        default_tunes[c.WORKING_FOLDER] = f.get_downloads_path()
        return default_tunes

    def is_validate(self, tunes: dict[str, str]) -> bool:
        """
        Проверка значений настроек из словаря настроек
        :param tunes: Словарь настроек
        :return:
        """
        if not isinstance(tunes, dict):
            return False
        for key in tunes.keys():
            match self.description_tunes[key].type:
                case "CheckBox":
                    if tunes[key] not in (
                            c.CHECK_STATE_CHECKED,
                            c.CHECK_STATE_UNCHECKED,
                    ):
                        return False
                case "String":
                    if not isinstance(tunes[key], str):
                        return False
                case _:
                    return False
        return True

    def read_tunes(self) -> dict[str, str]:
        """
        Чтение словаря настроек из файла настроек.
        Если с чтением файла проблемы - словарь формируется значениями настроек по умолчанию.

        :return:    Словарь настроек.
        """
        # noinspection PyBroadException
        try:
            with open(c.FILE_TUNES, "r") as file:
                tunes_from_file = json.load(file)
                if self.is_validate(tunes_from_file):
                    return tunes_from_file
                else:
                    QMessageBox.warning(None, c.TITLE_ERROR_READ, c.TEXT_ERROR_READ)
        except FileNotFoundError:
            pass  # Отсутствие файла настроек не ошибка.
        except Exception as e:
            QMessageBox.warning(None, c.TITLE_ERROR_READ, c.TEXT_ERROR_READ)
        return self.get_default_tunes()

    def write_tunes(self):
        """
        Запись словаря настроек в файл настроек
        :return:
        """
        try:
            with open(c.FILE_TUNES, "w") as file:
                # noinspection PyTypeChecker
                json.dump(self.dict_tunes, file)
        except Exception as e:
            QMessageBox.warning(None, c.TITLe_ERROR_WRITE, f"{c.TEXT_ERROR_WRITE}\n{e}")
