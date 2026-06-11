"""Модуль содержит класс работы с настройками и dataclass, описывающий структуру информации о настройки.
Настройки хранятся в словаре.
Ключами словаря являются имя настройки, а значениями - значения настроек."""

import json
from dataclasses import dataclass

from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import Qt

import src.functions as f
from src.constants import Constant as c

TuneValue = int | str


@dataclass
class VT:
    value: TuneValue  # Значение по умолчанию
    type: str  # Метод контроля типа


class Tunes:
    """Работа с настройками"""

    def __init__(self, description_tunes: dict[str, VT]) -> None:
        """
        Инициализация объекта класса
        :param description_tunes (dict): Имя настройки: (значение по умолчанию, метод контроля)
        """

        self.description_tunes = description_tunes
        self.dict_tunes: dict[str, TuneValue] = self.read_tunes()  # словарь настроек

    def get_tune(self, name: str) -> TuneValue:
        """
        Получение настройки
        :param name: Имя настройки
        :return: Значение настройки
        """
        if name in self.dict_tunes:
            return self.dict_tunes[name]
        else:
            raise ValueError(f"{c.TEXT_NO_TUNES} - {name}")

    def put_tune(self, name: str, value: TuneValue | Qt.CheckState, write: bool = False) -> None:
        """
        Запись настройки
        :param name: Имя настройки
        :param value: Значение настройки
        :param write: Параметр, определяющий следует ли записывать словарь в файл.
        :return: None
        """
        if not isinstance(name, str):
            raise ValueError(
                f"{c.TEXT_ERROR_TYPE_TUNES}. Имя {name} Тип {type(name).__name__}"
            )
        self.dict_tunes[name] = self.normalize_tune_value(name, value)

        if write:
            self.write_tunes()

    def get_default_tunes(self) -> dict[str, TuneValue]:
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

    def normalize_tune_value(
        self, name: str, value: TuneValue | Qt.CheckState
    ) -> TuneValue:
        if name not in self.description_tunes:
            raise ValueError(f"{c.TEXT_NO_TUNES} - {name}")

        match self.description_tunes[name].type:
            case "CheckBox":
                if isinstance(value, Qt.CheckState):
                    return value.value
                if isinstance(value, int):
                    check_state_value = value
                elif isinstance(value, str) and value.isdigit():
                    check_state_value = int(value)
                else:
                    raise ValueError(f"{c.TEXT_ERROR_TYPE_TUNES}. {name}={value}")

                if check_state_value not in (
                    Qt.CheckState.Checked.value,
                    Qt.CheckState.Unchecked.value,
                ):
                    raise ValueError(f"{c.TEXT_ERROR_TYPE_TUNES}. {name}={value}")
                return check_state_value
            case "String":
                if not isinstance(value, str):
                    raise ValueError(f"{c.TEXT_ERROR_TYPE_TUNES}. {name}={value}")
                return value
            case _:
                raise ValueError(f"{c.TEXT_NO_TUNES} - {name}")

    def normalize_tunes(self, tunes: dict[str, TuneValue]) -> dict[str, TuneValue]:
        return {
            key: self.normalize_tune_value(key, value)
            for key, value in tunes.items()
        }

    def is_validate(self, tunes: dict[str, TuneValue]) -> bool:
        """
        Проверка значений настроек из словаря настроек
        :param tunes: Словарь настроек
        :return:
        """
        if not isinstance(tunes, dict):
            return False
        try:
            self.normalize_tunes(tunes)
            return True
        except ValueError:
            return False

    def read_tunes(self) -> dict[str, TuneValue]:
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
                    return self.normalize_tunes(tunes_from_file)
                else:
                    QMessageBox.warning(
                        None, c.TITLE_ERROR_READ, f"{c.TEXT_ERROR_READ} - "
                    )
        except FileNotFoundError:
            pass  # Отсутствие файла настроек не ошибка.
        except Exception as e:
            QMessageBox.warning(None, c.TITLE_ERROR_READ, f"{c.TEXT_ERROR_READ}\n {e}")
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
            QMessageBox.warning(None, c.TITLE_ERROR_WRITE, f"{c.TEXT_ERROR_WRITE}\n{e}")
