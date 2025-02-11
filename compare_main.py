"""
Главный модуль приложения для сравнения отчетов.
Содержит UI-логику и обработку событий.
"""

import sys
import csv

from PyQt6 import QtWidgets, uic
from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QSortFilterProxyModel, QTimer
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
    QToolButton,
    QApplication,
)

import functions
from compare import parse_file, compare
from constants import Constant as c
import functions as f
from tunes import VT, Tunes
from customtextbrowser import CustomTextBrowser

DESCRIPTION_TUNES = {
    c.CHECK_BOX_FAST: VT(c.CHECK_STATE_UNCHECKED, c.CHECK_BOX),
    c.CHECK_BOX_SUPER_FAST: VT(c.CHECK_STATE_UNCHECKED, c.CHECK_BOX),
    c.CHECK_BOX_COMPS: VT(c.CHECK_STATE_CHECKED, c.CHECK_BOX),
    c.CHECK_BOX_LOADS: VT(c.CHECK_STATE_UNCHECKED, c.CHECK_BOX),
    c.WORKING_FOLDER: VT("", c.STRING),
}  # Имя настройки: (значение по умолчанию, метод контроля)


class MyWindow(QtWidgets.QMainWindow):
    """Главное окно приложения."""

    # Явные аннотации типов для виджетов из .ui-файла
    btnBox: QDialogButtonBox
    btnFile1: QPushButton
    btnFile2: QPushButton
    checkBoxFast: QCheckBox
    checkBoxSuperFast: QCheckBox
    checkBoxComps: QCheckBox
    checkBoxLoads: QCheckBox
    lblFilePath1: QLabel
    lblFilePath2: QLabel
    tblResult: QTableView
    tBtnWorkingFolder: QToolButton
    txtWorkingFolder: CustomTextBrowser

    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(c.FILE_UI, self)  # Загрузка интерфейса из .ui файла

        # Устанавливает настройки программы
        self.tunes = Tunes(DESCRIPTION_TUNES)

        # Инициализация стилей и состояния
        self.styleSheet_btn_default = self.btnFile1.styleSheet()
        self.was_comparison = False  # Флаг выполнения сравнения отчётов

        # Настройка модели таблицы
        self.model = QStandardItemModel()
        # Настраиваем прокси-модель для числовой сортировки
        self.proxy = QSortFilterProxyModel()
        self.setup_model()

        # Настройка соединений и интерфейса
        self.customize_interface()
        self.setup_connections()

        # Быстрый диалог. Без нажатия кнопок инициации выбора файлов.
        self.check_fast_dialogue()

        # Сверхбыстрый диалог. Выбор двух отчётов в одном диалоге.
        self.check_super_fast_dialogue()

    def setup_model(self):
        self.proxy.setSourceModel(self.model)
        # Сортируем по данным, имеющим UserRole
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.tblResult.setModel(self.proxy)

    def init_widgets(self) -> None:
        """Устанавливает значения видимых частей виджетов"""
        self.lblFilePath1.setText("")
        self.lblFilePath2.setText("")
        self.txtWorkingFolder.setText(self.tunes.get_tune(c.WORKING_FOLDER))
        self.init_checkbox(self.checkBoxFast, c.CHECK_BOX_FAST)
        self.init_checkbox(self.checkBoxSuperFast, c.CHECK_BOX_SUPER_FAST)
        self.init_checkbox(self.checkBoxComps, c.CHECK_BOX_COMPS)
        self.init_checkbox(self.checkBoxLoads, c.CHECK_BOX_LOADS)

    def init_checkbox(self, checkbox, name_value):
        checkbox.setCheckState(
            QtCore.Qt.CheckState.Checked
            if self.tunes.get_tune(name_value) == c.CHECK_STATE_CHECKED
            else QtCore.Qt.CheckState.Unchecked
        )

    def customize_interface(self) -> None:
        """Настраивает текст кнопок, внешний вид таблицы, значения виджетов"""

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

        # Инициализируем значения виджетов
        self.init_widgets()

    def set_table_width_to_window_width(self) -> None:
        """Устанавливает ширину таблицы равной ширине окна и делаем заголовки 'жирными'"""

        header = self.tblResult.horizontalHeader()

        if header is not None:
            header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            f.set_bold(header)

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
            self.tunes.get_tune(c.WORKING_FOLDER),
            c.TYPES_FILES_OPEN,
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if file_name:
            label.setText(file_name)

    def open_files_dialog(self) -> list[str]:
        while True:
            filenames, _ = QFileDialog.getOpenFileNames(
                self,
                c.TITLE_OPEN_TWO_FILES,
                self.tunes.get_tune(c.WORKING_FOLDER),
                c.TYPES_FILES_OPEN,
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if len(filenames) == 0 or len(filenames) == 2:
                return filenames
            QMessageBox.warning(
                None, "title", "Необходимо выбрать ровно 2 файла отчётов"
            )

    def open_file_dialog1(self) -> None:
        """
        Открывает диалог выбора файла первого отчёта
        """
        self.btnFile1.setStyleSheet(self.styleSheet_btn_default)
        self.open_file_dialog(c.TITLE_OPEN_FIRST_REPORT, self.lblFilePath1)
        f.set_focus(self.btnFile2)  # Приглашает открыть файл со вторым отчётом

    def open_file_dialog2(self) -> None:
        """
        Открывает диалог выбора файла второго отчёта
        """
        self.btnFile2.setStyleSheet(
            self.styleSheet_btn_default
        )  # Восстанавливает стиль кнопки для случая, если раньше была ошибка
        self.open_file_dialog(c.TITLE_OPEN_SECOND_REPORT, self.lblFilePath2)
        # Приглашает приступить к сравнению отчётов
        f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Ok))

    def setup_connections(self) -> None:
        """
        Устанавливает соответствия между сигналами и слотами
        """
        self.btnFile1.clicked.connect(self.open_file_dialog1)
        self.btnFile2.clicked.connect(self.open_file_dialog2)
        self.btnBox.clicked.connect(self.handle_button_click)
        self.checkBoxFast.stateChanged.connect(self.on_checkbox_fast_state_change)
        self.checkBoxSuperFast.stateChanged.connect(
            self.on_checkbox_super_fast_state_change
        )
        self.checkBoxLoads.stateChanged.connect(self.on_checkbox_state_change)
        self.checkBoxComps.stateChanged.connect(self.on_checkbox_state_change)
        self.tBtnWorkingFolder.clicked.connect(self.set_working_folder)
        self.txtWorkingFolder.connect(self.set_working_folder)

    def handle_button_click(self, button: QPushButton) -> None:
        """
        Проводит обработку нажатия кнопок из стандартного блока кнопок
        :param button: Нажатая кнопка из стандартного набора кнопок
        """
        match self.btnBox.standardButton(button):
            case QDialogButtonBox.StandardButton.Ok:
                self.on_click_OK()
                f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Save))
            case QDialogButtonBox.StandardButton.Save:
                self.on_click_save()
                f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Cancel))
            case QDialogButtonBox.StandardButton.Cancel:
                f.on_click_cancel()

    # noinspection PyPep8Naming
    def on_click_OK(self) -> None:
        """Обработчик кнопки 'Сравнить'. Запускает разбор и сравнение файлов."""
        self.model.clear()

        # Проверка. Выбраны ли файлы отчётов.
        files_selected = True
        if not self.lblFilePath1.text():
            files_selected = f.highlight_button_if_no_file(self.btnFile1)
        if not self.lblFilePath2.text():
            files_selected = f.highlight_button_if_no_file(self.btnFile2)

        if files_selected:
            self.sync_model_with_report_diffs()

    def on_checkbox_fast_state_change(self):
        """
        Проверяет выбраны ли одновременно быстрый и сверхбыстрый диалог.
        Если выбраны, то сверхбыстрый диалог отменяется, остаётся только быстрый.
        Далее вызывается стандартная обработка чек боксов.
        :return: None
        """
        if (
            self.checkBoxSuperFast.checkState() == QtCore.Qt.CheckState.Checked
            and self.checkBoxFast.checkState() == QtCore.Qt.CheckState.Checked
        ):
            self.checkBoxSuperFast.setCheckState(QtCore.Qt.CheckState.Unchecked)

        self.on_checkbox_state_change()

    def on_checkbox_super_fast_state_change(self) -> None:
        """
        Проверяет выбраны ли одновременно быстрый и сверхбыстрый диалог.
        Если выбраны, то быстрый диалог отменяется, остаётся только сверхбыстрый.
        Далее вызывается стандартная обработка чек боксов.
        :return: None
        """
        if (
            self.checkBoxSuperFast.checkState() == QtCore.Qt.CheckState.Checked
            and self.checkBoxFast.checkState() == QtCore.Qt.CheckState.Checked
        ):
            self.checkBoxFast.setCheckState(QtCore.Qt.CheckState.Unchecked)

        self.on_checkbox_state_change()

    def on_checkbox_state_change(self):
        """Обрабатывает изменение статуса любого чекбокса.
        Считывает статусы всех чек боксов и отдаёт их объекту работу с настройками"""
        self.checkbox_state_change(self.checkBoxFast, c.CHECK_BOX_FAST)
        self.checkbox_state_change(self.checkBoxSuperFast, c.CHECK_BOX_SUPER_FAST)
        self.checkbox_state_change(self.checkBoxComps, c.CHECK_BOX_COMPS)
        self.checkbox_state_change(self.checkBoxLoads, c.CHECK_BOX_LOADS, write=True)

    def checkbox_state_change(self, checkbox, name: str, write: bool = False) -> None:
        """
        Инициирует изменение настройки о статусе чекбокса.
        :param checkbox: Чекбокс, статус которого проверяется.
        :param name: Имя настройки
        :param write: Признак, надо ли сохранять изменения настроек в файл.
        :return: None
        """
        self.tunes.put_tune(
            name,
            (
                c.CHECK_STATE_CHECKED
                if checkbox.checkState() == QtCore.Qt.CheckState.Checked
                else c.CHECK_STATE_UNCHECKED
            ),
            write,
        )

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
        Проверяет заселена ли модель и если не заселена, выдаёт информационное сообщение в модель.
        :return: None
        """
        if not self.model.rowCount():
            self.add_data_to_model([c.TEXT_SUCCESSFUL_COMPARISON])
            self.tblResult.setSpan(0, 0, 1, len(c.LIST_HEADER_COLUMNS))
        self.customize_model()  # Обновление заголовков

    def on_click_save(self) -> None:
        """Обработчик кнопки 'Сохранить'. Записывает модель в CSV файл и выдаёт
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
                    self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE}\n{e}"
                )

    def sync_model_with_report_diffs(self) -> None:
        """Получает нужные записи из отчётов, инициирует их
        сравнение и заселение модели отличиями в отчётах
        """
        if (
            self.tunes.get_tune(c.CHECK_BOX_COMPS) == c.CHECK_STATE_UNCHECKED
            and self.tunes.get_tune(c.CHECK_BOX_LOADS) == c.CHECK_STATE_UNCHECKED
        ):  # Не выбран ни один из вариантов сравнения
            QMessageBox.warning(self, c.TITLE_NO_COMP, c.TEXT_NO_COMP)
            return
        try:
            records1 = parse_file(
                self.lblFilePath1.text(),
                self.tunes.get_tune(c.CHECK_BOX_COMPS) == c.CHECK_STATE_CHECKED,
                self.tunes.get_tune(c.CHECK_BOX_LOADS) == c.CHECK_STATE_CHECKED,
            )
            records2 = parse_file(
                self.lblFilePath2.text(),
                self.tunes.get_tune(c.CHECK_BOX_COMPS) == c.CHECK_STATE_CHECKED,
                self.tunes.get_tune(c.CHECK_BOX_LOADS) == c.CHECK_STATE_CHECKED,
            )
            only_in_1, only_in_2, differences = compare(records1, records2)

            self.populate_model(records1, records2, only_in_1, only_in_2, differences)
            self.was_comparison = True
        except Exception as e:
            QMessageBox.critical(self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE}\n{e}")

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
            v_item_str = (
                f"{v_item:,}".replace(",", "'")
                if isinstance(v_item, int)
                else str(v_item)
            )
            item.setData(v_item_str, Qt.ItemDataRole.DisplayRole)
            row_items.append(item)
        self.model.appendRow(row_items)

    def check_fast_dialogue(self) -> None:
        """
        Анализирует запрошен ли сокращённый диалог
        и если запрошен то имитирует нажатие кнопок выбора файлов
        :return: None
        """
        if self.tunes.get_tune(c.CHECK_BOX_FAST) == c.CHECK_STATE_CHECKED:
            self.open_file_dialog1()
            self.open_file_dialog2()

    def check_super_fast_dialogue(self) -> None:
        """
        Анализирует запрошен ли очень сокращённый диалог (выбор двух отчётов в одном диалоге).
        Если запрошен, то в одном диалоге запрашивает два файла отчётов и организует их обработку
        :return:
        """
        if self.tunes.get_tune(c.CHECK_BOX_SUPER_FAST) == c.CHECK_STATE_CHECKED:
            files = self.open_files_dialog()
            if len(files) == 0:
                sys.exit(1000)
            self.lblFilePath1.setText(files[0])
            self.lblFilePath2.setText(files[1])
            self.on_click_OK()
            self.on_click_save()
            f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Cancel))

    def set_working_folder(self) -> None:
        """
        Запрашивает у Пользователя рабочую папку.
        При отказе от выбора папки путь на рабочую папку остаётся прежним.
        :return: None
        """
        worker_folder = QFileDialog.getExistingDirectory(
            self,
            c.TITLE_SET_WORKING_FOLDER,
            self.tunes.get_tune(c.WORKING_FOLDER),
        )

        if worker_folder:
            self.txtWorkingFolder.setText(worker_folder)
            self.tunes.put_tune(c.WORKING_FOLDER, worker_folder, write=True)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
