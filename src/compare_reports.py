"""
Главный модуль приложения для сравнения отчетов.
Содержит UI-логику и обработку событий.
"""

from datetime import datetime
import sys
import csv
from pathlib import Path
from enum import Enum, auto

from PyQt6 import QtWidgets, uic
from PyQt6 import QtCore
from PyQt6.QtCore import QSortFilterProxyModel, Qt
from PyQt6.QtGui import QStandardItemModel, QStandardItem, QAction
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
)

from src.compare import parse_file, compare, VS
from src.constants import Constant as c
import src.functions as f
from src.tunes import Tunes, DESCRIPTION_TUNES
from src.customtextbrowser import CustomTextBrowser


class DialogueState(Enum):
    NORMAL = auto()
    FAST = auto()
    SUPER_FAST = auto()


class MyWindow(QtWidgets.QMainWindow):
    """Главное окно приложения."""

    # Явные аннотации типов для виджетов из .ui-файла
    actionAbout: QAction
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
    btnOutputFolder: QToolButton
    txtOutputFolder: CustomTextBrowser

    # 1. init
    def __init__(self) -> None:
        super().__init__()
        uic.loadUi(f.get_file_ui_name(), self)  # Загрузка интерфейса из .ui файла

        # Переменные объекта
        self.dialogue_state: DialogueState = DialogueState.NORMAL

        # Устанавливает настройки программы
        self.tunes = Tunes(DESCRIPTION_TUNES)

        # Инициализация стилей и состояния
        self.btn_file_default_style = self.btnFile1.styleSheet()
        self.was_comparison = False  # Флаг завершения выполнения сравнения отчётов

        # Настройка модели таблицы
        self.model = QStandardItemModel()
        # Настраиваем прокси-модель для числовой сортировки
        self.proxy = QSortFilterProxyModel()
        self.setup_model()

        # Настройка соединений и интерфейса
        self.customize_interface()
        self.setup_connections()

        # При необходимости - быстрый диалог.
        self.run_fast_dialogues()

    # 2. Настройка окна
    def setup_model(self) -> None:
        self.proxy.setSourceModel(self.model)
        # Сортируем по данным, имеющим UserRole
        self.proxy.setSortRole(Qt.ItemDataRole.UserRole)
        self.tblResult.setModel(self.proxy)

    def setup_table_view(self) -> None:
        """Настраивает внешний вид таблицы результатов"""

        header = self.tblResult.horizontalHeader()
        if header is None:
            return

        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        header.setMinimumSectionSize(55)
        header.setStretchLastSection(False)

        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        for col in (1, 2, 3, 4):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)

        self.tblResult.setColumnWidth(1, 105)
        self.tblResult.setColumnWidth(2, 105)
        self.tblResult.setColumnWidth(3, 80)
        self.tblResult.setColumnWidth(4, 80)

        f.set_bold(header)

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
                button.setAutoDefault(False)
                button.setDefault(False)

        # Настраиваем таблицу для просмотра
        self.setup_table_view()

        # Инициализируем значения виджетов
        self.init_widgets()

    def setup_connections(self) -> None:
        """
        Устанавливает соответствия между сигналами и слотами
        """
        self.btnFile1.clicked.connect(self.select_first_report)
        self.btnFile2.clicked.connect(self.select_second_report)

        self.checkBoxComps.stateChanged.connect(self.on_checkbox_state_change)
        self.checkBoxLoads.stateChanged.connect(self.on_checkbox_state_change)
        self.checkBoxFast.stateChanged.connect(self.on_checkbox_fast_state_change)
        self.checkBoxSuperFast.stateChanged.connect(
            self.on_checkbox_super_fast_state_change
        )

        self.btnOutputFolder.clicked.connect(self.set_saver_folder)
        self.txtOutputFolder.connect(self.set_saver_folder)

        self.btnBox.clicked.connect(self.handle_button_click)
        self.actionAbout.triggered.connect(self.show_about_dialog)

    def init_widgets(self) -> None:
        """Устанавливает значения видимых частей виджетов"""
        self.lblFilePath1.setText("")
        self.lblFilePath2.setText("")
        saver_folder = self.tunes.get_str_tune(c.SAVER_FOLDER)
        self.save_saver_folder(saver_folder)
        self.init_checkbox(self.checkBoxFast, c.CHECK_BOX_FAST)
        self.init_checkbox(self.checkBoxSuperFast, c.CHECK_BOX_SUPER_FAST)
        self.init_checkbox(self.checkBoxComps, c.CHECK_BOX_COMPS)
        self.init_checkbox(self.checkBoxLoads, c.CHECK_BOX_LOADS)

    def init_checkbox(self, checkbox, name_value):
        checkbox.setCheckState(
            QtCore.Qt.CheckState.Checked
            if self.tunes.is_checked(name_value)
            else QtCore.Qt.CheckState.Unchecked
        )

    # 3. Диалоги выбора файлов и папок
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
            self.tunes.get_str_tune(c.SAVER_FOLDER),
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
                str(self.tunes.get_str_tune(c.SAVER_FOLDER)),
                c.TYPES_FILES_OPEN,
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if len(filenames) == 0 or len(filenames) == 2:
                return filenames
            QMessageBox.warning(
                None, "Предупреждение", "Необходимо выбрать ровно 2 файла отчётов"
            )

    def set_saver_folder(self) -> None:
        """
        Запрашивает у Пользователя рабочую папку.
        При отказе от выбора папки путь на рабочую папку остаётся прежним.
        :return: None
        """
        saver_folder = QFileDialog.getExistingDirectory(
            self,
            c.TITLE_SET_SAVER_FOLDER,
            str(self.tunes.get_str_tune(c.SAVER_FOLDER)),
        )

        if saver_folder:
            self.save_saver_folder(saver_folder)

    def save_saver_folder(self, saver_folder: str) -> None:
        self.txtOutputFolder.setText(saver_folder)
        self.tunes.put_tune(c.SAVER_FOLDER, saver_folder, write=True)

    def select_first_report(self) -> None:
        """
        Открывает диалог выбора файла первого отчёта
        """
        self.btnFile1.setStyleSheet(self.btn_file_default_style)
        self.open_file_dialog(c.TITLE_OPEN_FIRST_REPORT, self.lblFilePath1)
        f.set_focus(self.btnFile2)  # Приглашает открыть файл со вторым отчётом

    def select_second_report(self) -> None:
        """
        Открывает диалог выбора файла второго отчёта
        """
        self.btnFile2.setStyleSheet(
            self.btn_file_default_style
        )  # Восстанавливает стиль кнопки для случая, если раньше была ошибка
        self.open_file_dialog(c.TITLE_OPEN_SECOND_REPORT, self.lblFilePath2)
        # Приглашает приступить к сравнению отчётов
        f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Ok))

    # 4. Обработчики UI
    def handle_button_click(self, button: QPushButton) -> None:
        """
        Проводит обработку нажатия кнопок из стандартного блока кнопок
        :param button: Нажатая кнопка из стандартного набора кнопок
        """
        match self.btnBox.standardButton(button):
            case QDialogButtonBox.StandardButton.Ok:
                self.compare_reports()
                f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Save))
            case QDialogButtonBox.StandardButton.Save:
                self.save_results()
                f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Cancel))
            case QDialogButtonBox.StandardButton.Cancel:
                QtWidgets.QApplication.quit()

    def compare_reports(self) -> None:
        """Разбор и сравнение файлов отчётов."""
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
            checkbox.checkState().value,
            write,
        )

    def save_results(self) -> None:
        """Обработчик кнопки 'Сохранить'. Записывает модель в CSV файл и выдаёт
        предупреждение, если сравнение отчётов не выполнено.
        """
        if not self.was_comparison:
            QMessageBox.warning(self, c.TITLE_RESAVE, c.TEXT_RESAVE)
            return

        try:
            # Запись данных модели в csv филе
            file_path = self.get_result_file_path()

            with open(file_path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file, delimiter=";")
                writer.writerow(c.LIST_HEADER_COLUMNS)
                self.write_model_to_csv(writer)

        except Exception as e:
            QMessageBox.critical(self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE}\n{e}")
            return

        self.was_comparison = False
        wait = self.get_wait_ms()
        f.show_message(self, f"Отчёт сохранён по пути\n{file_path}", wait=wait)

    # 5. Сравнение и заполнение таблицы
    def sync_model_with_report_diffs(self) -> None:
        """Получает нужные записи из отчётов, инициирует их
        сравнение и заселение модели отличиями в отчётах
        """
        compare_comps = self.tunes.is_checked(c.CHECK_BOX_COMPS)
        compare_loads = self.tunes.is_checked(c.CHECK_BOX_LOADS)

        if not compare_comps and not compare_loads:
            # Не выбран ни один из вариантов сравнения
            QMessageBox.warning(self, c.TITLE_NO_COMP, c.TEXT_NO_COMP)
            return

        try:
            records1 = parse_file(
                self.lblFilePath1.text(),
                compare_comps,
                compare_loads,
            )
            records2 = parse_file(
                self.lblFilePath2.text(),
                compare_comps,
                compare_loads,
            )
            only_in_1, only_in_2, differences = compare(records1, records2)

            self.populate_model(records1, records2, only_in_1, only_in_2, differences)
            self.was_comparison = True
        except Exception as e:
            QMessageBox.critical(self, c.TITLE_ERROR_FILE, f"{c.TEXT_ERROR_FILE}\n{e}")

    def make_only_in_first_row(
        self, item: str, records1: dict[str, VS]
    ) -> list[str | int]:
        record = records1[item]
        return [item, record.stamp, "", record.size, ""]

    def make_only_in_second_row(
        self, item: str, records2: dict[str, VS]
    ) -> list[str | int]:
        record = records2[item]
        return [item, "", record.stamp, "", record.size]

    def make_difference_row(
        self,
        item: str,
        records1: dict[str, VS],
        records2: dict[str, VS],
    ) -> list[str | int]:
        record1 = records1[item]
        record2 = records2[item]
        return [item, record1.stamp, record2.stamp, record1.size, record2.size]

    def populate_model(
        self,
        records1: dict[str, VS],
        records2: dict[str, VS],
        only_in_1: set[str],
        only_in_2: set[str],
        differences: set[str],
    ) -> None:
        """
        Заселяет модель результатами сравнения отчётов.
        Records 1 и 2 - Словари, содержащие информацию о компонентах.
                        Ключ — имя компонента. Значение — характеристики компонента.
        :param records1: Словарь первого отчёта.
        :param records2: Словарь второго отчёта.
        Остальные параметры — множества, в которых находятся ключи словарей с рассогласованиями между отчётами.
        :param only_in_1: Компоненты есть только в первом отчёте.
        :param only_in_2: Компоненты есть только во втором отчёте.
        :param differences: Компоненты есть в обоих отчётах, но их характеристики отличаются.
        :return: None
        """
        # Добавление данных в модель
        for item in sorted(only_in_1):
            self.add_data_to_model(self.make_only_in_first_row(item, records1))

        for item in sorted(only_in_2):
            self.add_data_to_model(self.make_only_in_second_row(item, records2))

        for item in sorted(differences):
            self.add_data_to_model(self.make_difference_row(item, records1, records2))

        self.check_empty_data()

    def add_data_to_model(self, items: list[str | int]) -> None:
        """
        Добавляет строку данных в модель таблицы
        :param items: Список элементов столбцов новой строки.
                      Элементами могут быть как строки, так и целые числа.
        :return: None
        """
        row_items = []
        for value in items:
            item = QStandardItem()
            item.setData(value, Qt.ItemDataRole.UserRole)

            if isinstance(value, int):
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                display_value = f"{value:,}".replace(",", "'")
            else:
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                display_value = str(value)

            item.setData(display_value, Qt.ItemDataRole.DisplayRole)
            row_items.append(item)
        self.model.appendRow(row_items)

    def check_empty_data(self) -> None:
        """
        Проверяет заселена ли модель и если не заселена, выдаёт информационное сообщение в модель.
        :return: None
        """
        if not self.model.rowCount():
            self.add_data_to_model([c.TEXT_SUCCESSFUL_COMPARISON])
            self.tblResult.setSpan(0, 0, 1, len(c.LIST_HEADER_COLUMNS))
        self.setup_model_headers()  # Обновление заголовков

    def setup_model_headers(self) -> None:
        """Устанавливает шапки в таблице модели"""
        self.model.setHorizontalHeaderLabels(c.LIST_HEADER_COLUMNS)
        self.setup_table_view()

    # 6. CSV
    def get_result_file_path(self) -> Path:
        output_folder = Path(self.tunes.get_str_tune(c.SAVER_FOLDER))
        time_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f"compare_{time_stamp}.csv"

        return output_folder / file_name

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

    # 7. Быстрые режимы
    def run_fast_dialogue(self) -> None:
        """
        Анализирует запрошен ли сокращённый диалог
        и если запрошен то имитирует нажатие кнопок выбора файлов
        :return: None
        """
        if self.tunes.is_checked(c.CHECK_BOX_FAST):
            self.dialogue_state = DialogueState.FAST
            self.select_first_report()
            self.select_second_report()

    def run_super_fast_dialogue(self) -> None:
        """
        Анализирует запрошен ли очень быстрый диалог (выбор двух отчётов в одном диалоге).
        Если запрошен, то в одном диалоге запрашивает два файла отчётов и организует их обработку
        :return:
        """
        if self.tunes.is_checked(c.CHECK_BOX_SUPER_FAST):
            self.dialogue_state = DialogueState.SUPER_FAST
            files = self.open_files_dialog()
            if not files:
                return

            self.lblFilePath1.setText(files[0])
            self.lblFilePath2.setText(files[1])
            self.compare_reports()
            self.save_results()
            f.set_focus(self.btnBox.button(QDialogButtonBox.StandardButton.Cancel))

    def get_wait_ms(self) -> int:
        match self.dialogue_state:
            case DialogueState.NORMAL:
                return 2500
            case DialogueState.FAST:
                return 1000
            case DialogueState.SUPER_FAST:
                return 0

    def run_fast_dialogues(self) -> None:
        """Запускает быстрый или сверхбыстрый сценарий выбора отчётов."""
        if self.tunes.is_checked(c.CHECK_BOX_SUPER_FAST):
            self.run_super_fast_dialogue()
        elif self.tunes.is_checked(c.CHECK_BOX_FAST):
            self.run_fast_dialogue()

    def show_about_dialog(self) -> None:
        QMessageBox.about(
            self,
            "О программе",
            """
            <h3>Compare Reports</h3>

            <p>
            Программа сравнивает полученные с разных установок системы
            «Галактика» отчёты:
            </p>

            <ul>
                <li>сводный отчёт о компонентах;</li>
                <li>полный отчёт о компонентах;</li>
                <li>отчёт о рабочей станции.</li>
            </ul>

            <p>
            В результате сравнения для компонентов и загруженных модулей отображаются различия 
            в версиях, датах и размерах.
            </p>

            <p><b>Основные возможности:</b></p>

            <ul>
                <li>сравнение версий, дат и размеров компонентов;</li>
                <li>быстрый и сверхбыстрый режимы выбора отчётов;</li>
                <li>сохранение результатов сравнения в CSV-файл,
                открываемый в Microsoft Excel.</li>
            </ul>

            <p>Автор: Большаков Л.А.</p>
            <p>Версия: 1.0<br>Июнь 2026 года</p>
            """,
        )


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
