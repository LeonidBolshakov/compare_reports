"""
Главный модуль приложения для сравнения отчетов.
Содержит UI-логику и обработку событий.
"""

import sys
import csv

from PyQt6 import QtWidgets, uic
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView,
    QPushButton,
    QApplication,
    QTableView,
)
from compare import parse_file, compare
from constant import Constant as c


class MyWindow(QtWidgets.QMainWindow):
    """Главное окно приложения."""

    # Явные аннотации типов для виджетов из .ui-файла
    btnBox: QDialogButtonBox
    btnFile1: QPushButton
    btnFile2: QPushButton
    lblFilePath1: QLabel
    lblFilePath2: QLabel
    tblResult: QTableView

    def __init__(self):
        super().__init__()
        uic.loadUi(c.FILE_UI, self)  # Загрузка интерфейса из .ui файла

        # Инициализация стилей и состояния
        self.styleSheet_btn_default = self.btnFile1.styleSheet()
        self.was_comparison = False  # Флаг выполнения сравнения

        # Настройка модели таблицы
        self.model = QStandardItemModel()
        self.tblResult.setModel(self.model)

        # Настройка соединений и интерфейса
        self.setup_connections()
        self.setup_var()
        self.customize_interface()

    def setup_var(self):
        """Сбрасывает пути к файлам."""
        self.lblFilePath1.setText("")
        self.lblFilePath2.setText("")

    def customize_interface(self):
        """Настраивает текст кнопок и внешний вид таблицы."""
        # Переименование кнопок
        buttons = {
            QDialogButtonBox.StandardButton.Ok: c.TEXT_BUTTON_COMPARE,
            QDialogButtonBox.StandardButton.Save: c.TEXT_BUTTON_SAVE,
            QDialogButtonBox.StandardButton.Cancel: c.TEXT_BUTTON_QUIT,
        }
        for btn_type, text in buttons.items():
            self.btnBox.button(btn_type).setText(text)

        # Делает кнопки стандартного бокса кнопок - AutoDefault.
        # После установки фокуса на кнопку, по клавише Enter вызывается обработка нажатия кнопки
        for button in self.btnBox.buttons():
            button.setAutoDefault(True)

        # Устанавливает ширину таблицы равной ширине окна
        header = self.tblResult.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def customize_model(self):
        self.model.setHorizontalHeaderLabels(c.LIST_HEADER_COLUMNS)

    def open_file_dialog(self, title: str, label: QLabel) -> None:
        """
        Открывает диалог выбора файла.

        Args:
            title (str): Заголовок диалога.
            label (QLabel): Метка для отображения пути.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            title,
            "",
            c.TYPES_FILES_OPEN,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        label.setText(file_name)

    def open_file_dialog1(self) -> None:
        """
        Открывает диалог выбора файла первого отчёта
        """
        self.btnFile1.setStyleSheet(self.styleSheet_btn_default)
        self.open_file_dialog(c.TITLE_OPEN_FIRST_REPORT, self.lblFilePath1)
        self.btnFile2.setFocus()

    def open_file_dialog2(self):
        """
        Открывает диалог выбора файла второго отчёта
        """
        self.btnFile2.setStyleSheet(self.styleSheet_btn_default)
        self.open_file_dialog(c.TITLE_OPEN_SECOND_REPORT, self.lblFilePath2)
        self.btnBox.button(QDialogButtonBox.StandardButton.Ok).setFocus()

    def setup_connections(self):
        """
        Устанавливает соответствия между сигналами и слотами
        """
        self.btnFile1.clicked.connect(self.open_file_dialog1)
        self.btnFile2.clicked.connect(self.open_file_dialog2)
        self.btnBox.clicked.connect(self.handle_button_click)

    def handle_button_click(self, button) -> None:
        """
        Проводит обработку нажатия кнопки из стандартного блока кнопок
        :param button: Нажатая кнопка из стандартного набора кнопок
        """
        match self.btnBox.standardButton(button):
            case QDialogButtonBox.StandardButton.Ok:
                self.on_click_OK()
                self.btnBox.button(QDialogButtonBox.StandardButton.Save).setFocus()
            case QDialogButtonBox.StandardButton.Save:
                self.on_save()
                self.btnBox.button(QDialogButtonBox.StandardButton.Cancel).setFocus()
            case QDialogButtonBox.StandardButton.Cancel:
                self.on_cancel()

    def on_click_OK(self):
        """Обработчик кнопки 'Сравнить'. Запускает разбор и сравнение файлов."""
        self.model.clear()
        ok = True

        # Проверка. Выбраны ли файлы отчётов.
        if not self.lblFilePath1.text():
            ok = self.btn_error(self.btnFile1)
        if not self.lblFilePath2.text():
            ok = self.btn_error(self.btnFile2)

        if ok:
            try:
                records1 = parse_file(self.lblFilePath1.text())
                records2 = parse_file(self.lblFilePath2.text())
                only_in_1, only_in_2, differences = compare(records1, records2)
                self.populate_model(
                    records1, records2, only_in_1, only_in_2, differences
                )
                self.was_comparison = True
            except Exception as e:
                QMessageBox.critical(
                    self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE} {e}"
                )

    def populate_model(self, records1, records2, only_in_1, only_in_2, differences):
        """Заполняет таблицу результатами сравнения."""
        # Добавление данных в модель
        for item in only_in_1:
            self.add_data_to_model(
                [item, records1[item].version, records1[item].size, "", ""]
            )
        for item in only_in_2:
            self.add_data_to_model(
                [item, "", "", records2[item].version, records2[item].size]
            )
        for item in differences:
            self.add_data_to_model(
                [
                    item,
                    records1[item].version,
                    records1[item].size,
                    records2[item].version,
                    records2[item].size,
                ]
            )

        # Если заселять модель нечем
        if not self.model.rowCount():
            self.add_data_to_model(["Различия в компонентах отчётов не обнаружены"])
            print(self.model.columnCount())
            self.tblResult.setSpan(0, 0, 1, len(c.LIST_HEADER_COLUMNS))
        self.customize_model()  # Обновление заголовков

    @staticmethod
    def btn_error(button: QPushButton) -> bool:
        """Устанавливает стиль кнопки при ошибке и возвращает False."""
        button.setStyleSheet(c.STYLE_ERROR_BUTTON)
        return False

    @staticmethod
    def on_cancel():
        """Завершает работу приложения."""
        QApplication.quit()

    def on_save(self):
        """Обработчик кнопки 'Сохранить'. Показывает предупреждение, если сравнение не выполнено."""
        if not self.was_comparison:
            QMessageBox.warning(self, "Предупреждение", c.RESAVE_TEXT)
        else:
            # Запись данных модели в csv филе
            with open("save.csv", "w", newline="") as csv_file:
                writer = csv.writer(csv_file, delimiter=";")
                for row in range(self.model.rowCount()):
                    csv_row = []
                    for col in range(self.model.columnCount()):
                        index = self.model.index(row, col)
                        csv_row.append(self.model.data(index))
                    writer.writerow(csv_row)
            self.was_comparison = False

    def add_data_to_model(self, items: list) -> None:
        """Добавляет строку данных в модель таблицы."""
        self.model.appendRow([QStandardItem(str(item)) for item in items])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
