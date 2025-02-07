"""
Главный модуль приложения для сравнения отчетов.
Содержит UI-логику и обработку событий.
"""

import sys
import csv

from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import Qt, QSortFilterProxyModel
from PyQt6.QtGui import QStandardItemModel, QStandardItem
from PyQt6.QtWidgets import (
    QFileDialog,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QHeaderView,
    QPushButton,
    QTableView,
    QCheckBox,
)

from compare import parse_file, compare
from constants import Constant as c
import functions as f


class MyWindow(QtWidgets.QMainWindow):
    """Главное окно приложения."""

    # Явные аннотации типов для виджетов из .ui-файла
    btnBox: QDialogButtonBox
    btnFile1: QPushButton
    btnFile2: QPushButton
    checkBoxFast: QCheckBox
    lblFilePath1: QLabel
    lblFilePath2: QLabel
    tblResult: QTableView

    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(c.FILE_UI, self)  # Загрузка интерфейса из .ui файла

        # Устанавливает признак быстрого диалога
        self.sign_fast_dialogue = f.get_sign_fast_dialogue()

        # Инициализация стилей и состояния
        self.styleSheet_btn_default = self.btnFile1.styleSheet()
        self.was_comparison = False  # Флаг выполнения сравнения

        # Настройка модели таблицы
        self.model = QStandardItemModel()
        # Настраиваем прокси-модель для числовой сортировки
        self.proxy = QSortFilterProxyModel()
        self.setup_model()

        # Настройка соединений и интерфейса
        self.setup_connections()
        self.setup_var()
        self.customize_interface()

        # Быстрый диалог. Без нажатия кнопок инициации выбора файлов.
        self.fast_dialogue()

    def setup_model(self):
        self.proxy.setSourceModel(self.model)
        # Сортируем по данным, имеющим UserRole
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.tblResult.setModel(self.proxy)

    def setup_var(self) -> None:
        """Сбрасывает пути к файлам"""
        self.lblFilePath1.setText("")
        self.lblFilePath2.setText("")
        self.checkBoxFast.setChecked(True if self.sign_fast_dialogue else False)

    def customize_interface(self) -> None:
        """Настраивает текст кнопок и внешний вид таблицы."""

        # Переименование кнопок и назначение им свойства AutoDefault
        buttons = {
            QDialogButtonBox.StandardButton.Ok: c.TEXT_BUTTON_COMPARE,
            QDialogButtonBox.StandardButton.Save: c.TEXT_BUTTON_SAVE,
            QDialogButtonBox.StandardButton.Cancel: c.TEXT_BUTTON_QUIT,
        }
        for btn_type, text in buttons.items():
            button = self.btnBox.button(btn_type)
            if button:
                button.setText(text)
                button.setAutoDefault(True)

        # Устанавливает ширину таблицы равной ширине окна
        self.set_table_width_to_window_width()

    def set_table_width_to_window_width(self) -> None:
        """Устанавливает ширину таблицы равной ширине окна"""

        header = self.tblResult.horizontalHeader()
        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            header = f.set_bold(header)

    def customize_model(self) -> None:
        """Устанавливает шапки в таблице модели"""
        self.model.setHorizontalHeaderLabels(c.LIST_HEADER_COLUMNS)

    def open_file_dialog(self, title: str, label: QLabel) -> None:
        """
        Открывает диалог выбора файла и записывает путь выбранного файла в метку.

        Args:
            title (str): Заголовок диалога,
            label (QLabel): Метка для отображения пути открытого файла.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            title,
            f.get_downloads_path(),
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

    def open_file_dialog2(self) -> None:
        """
        Открывает диалог выбора файла второго отчёта
        """
        self.btnFile2.setStyleSheet(self.styleSheet_btn_default)
        self.open_file_dialog(c.TITLE_OPEN_SECOND_REPORT, self.lblFilePath2)
        button = self.btnBox.button(QDialogButtonBox.StandardButton.Ok)
        if button:
            button.setFocus()

    def setup_connections(self) -> None:
        """
        Устанавливает соответствия между сигналами и слотами
        """
        self.btnFile1.clicked.connect(self.open_file_dialog1)
        self.btnFile2.clicked.connect(self.open_file_dialog2)
        self.btnBox.clicked.connect(self.handle_button_click)
        self.checkBoxFast.stateChanged.connect(self.on_checkbox_state_change)

    def handle_button_click(self, button: QPushButton) -> None:
        """
        Проводит обработку нажатия кнопок из стандартного блока кнопок
        :param button: Нажатая кнопка из стандартного набора кнопок
        """
        match self.btnBox.standardButton(button):
            case QDialogButtonBox.StandardButton.Ok:
                self.on_click_OK()
                btn = self.btnBox.button(QDialogButtonBox.StandardButton.Save)
                if btn:
                    btn.setFocus()
            case QDialogButtonBox.StandardButton.Save:
                self.on_save()
                btn = self.btnBox.button(QDialogButtonBox.StandardButton.Cancel)
                if btn:
                    btn.setFocus()
            case QDialogButtonBox.StandardButton.Cancel:
                f.on_cancel()

    def on_click_OK(self) -> None:
        """Обработчик кнопки 'Сравнить'. Запускает разбор и сравнение файлов."""
        self.model.clear()
        files_selected = True

        # Проверка. Выбраны ли файлы отчётов.
        if not self.lblFilePath1.text():
            files_selected = f.highlight_button_if_no_file(self.btnFile1)
        if not self.lblFilePath2.text():
            files_selected = f.highlight_button_if_no_file(self.btnFile2)

        if files_selected:
            self.sync_model_with_report_diffs()

    def on_checkbox_state_change(self, state):
        try:
            with open(c.FILE_TUNES, "w") as tunes:
                tunes.write(str(state))
        except Exception as e:
            QMessageBox.warning(self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE} {e}")

    def populate_model(
        self,
        records1: dict,
        records2: dict,
        only_in_1: set,
        only_in_2: set,
        differences: set,
    ) -> None:
        """
        Заселяет модель результатами сравнения отчётов.
        Records 1 и 2 - Словари, содержащие информацию о компонентах.
                        Ключ - имя компонента. Значение - характеристики компонента.
        :param records1: Словарь первого отчёта.
        :param records2: Словарь второго отчёта.
        Остальные параметры - множества, в которых находятся ключи словарей с рассогласованиями между отчётами
        :param only_in_1: Компоненты есть только в первом отчёте.
        :param only_in_2: Компоненты есть только во втором отчёте.
        :param differences: Компоненты есть в обоих отчётах, но их характеристики отличаются.
        :return: None
        """
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

        self.check_empty_data()

    def check_empty_data(self) -> None:
        """
        Проверяет заселена ли модель и если не заселена, выдаёт сообщение в модель.
        :return: None
        """
        if not self.model.rowCount():
            self.add_data_to_model([c.TEXT_SUCCESSFUL_COMPARISON])
            self.tblResult.setSpan(0, 0, 1, len(c.LIST_HEADER_COLUMNS))
        self.customize_model()  # Обновление заголовков

    def on_save(self) -> None:
        """Обработчик кнопки 'Сохранить'. Записывает модель в CSV файл и показывает
        предупреждение, если сравнение отчётов не выполнено.
        """
        if not self.was_comparison:
            QMessageBox.warning(self, c.TITLE_RESAVE, c.TEXT_RESAVE)
        else:
            self.was_comparison = False
            try:
                # Запись данных модели в csv филе
                with open("save.csv", "w", newline="") as csv_file:
                    writer = csv.writer(csv_file, delimiter=";")
                    writer.writerow(c.LIST_HEADER_COLUMNS)
                    self.write_model_to_csv(writer)
            except Exception as e:
                QMessageBox.critical(
                    self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE} {e}"
                )

    def sync_model_with_report_diffs(self) -> None:
        """Получает нужные записи из отчётов, инициирует их
        сравнение и заселение модели отличиями в отчётах
        """
        try:
            records1 = parse_file(self.lblFilePath1.text())
            records2 = parse_file(self.lblFilePath2.text())
            only_in_1, only_in_2, differences = compare(records1, records2)

            self.populate_model(records1, records2, only_in_1, only_in_2, differences)
            self.was_comparison = True
        except Exception as e:
            QMessageBox.critical(self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE} {e}")

    def write_model_to_csv(self, writer) -> None:
        """
        Извлекает данные из модели и с помощью объекта writer записывает их в csv файл.
        :param writer:
        :return: None
        """
        for row in range(self.model.rowCount()):
            csv_row = []
            for col in range(self.model.columnCount()):
                index = self.model.index(row, col)
                csv_row.append(self.model.data(index))
            writer.writerow(csv_row)

    def add_data_to_model(self, items: list) -> None:
        """
        Добавляет строку данных в модель таблицы
        :param items: Список элементов столбцов новой строки.
                      Элементами могут быть как строки, так и целые числа.
        :return: None
        """
        row_items = []
        for v_item in items:
            item = QStandardItem()
            item.setData(v_item, Qt.ItemDataRole.UserRole)
            if type(v_item) is int:
                v_item = f"{v_item:,}".replace(",", "'")
            item.setData(str(v_item), Qt.ItemDataRole.DisplayRole)
            row_items.append(item)
        self.model.appendRow(row_items)

    def fast_dialogue(self):
        """
        Анализирует запрошен ли сокращённый диалог
        и если запрошен то имитирует нажатие кнопок выбора файлов
        :return:
        """
        if self.sign_fast_dialogue:
            self.open_file_dialog1()
            self.open_file_dialog2()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
