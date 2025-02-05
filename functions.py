from PyQt6.QtWidgets import QPushButton, QApplication

from constant import Constant as c


def set_bold(header):
    font = header.font()
    font.setBold(True)
    header.setFont(font)
    return header


def highlight_button_if_no_file(button: QPushButton) -> bool:
    """
    Метод вызывают в случае, если не был выбран файл отчёта.
    Устанавливает стиль кнопки выбора файла и возвращает False.
    """
    button.setStyleSheet(c.STYLE_ERROR_BUTTON)
    return False


def on_cancel() -> None:
    """Завершает работу приложения."""
    QApplication.quit()


def write_head_to_csv(writer, head: list[str]) -> None:
    """
    Записывает шапку таблицы в CSV файл
    :param writer: объект, записывающий в CSV файл
    :param head: список с текстами заголовков столбцов
    :return: None
    """
    writer.writerow(head)
