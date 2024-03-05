from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, \
    QHeaderView, QStyledItemDelegate

from design import Ui_MainWindow
from database import DataBase

RAINBOW_COLORS = {
    0: (QColor(255, 231, 231), QColor(255, 150, 150)),
    1: (QColor(255, 255, 228), QColor(255, 255, 150)),
    2: (QColor(231, 255, 228), QColor(150, 255, 150)),
    3: (QColor(238, 255, 255), QColor(150, 255, 255)),
    4: (QColor(228, 228, 255), QColor(150, 150, 255)),
    5: (QColor(255, 228, 255), QColor(255, 150, 255)),
}


# Класс-делегат, запрещает редактирование определенной колонки или строки в QTableWidget
class ReadOnlyDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        return


class MainWindow(QMainWindow, Ui_MainWindow):
    # Переопределяем конструктор класса
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.db = DataBase('DataBase.db')
        self.db.prepare_timetable()

        # тут будут храниться количество строк в таблицах
        self.qual_row_table_1 = self.db.get_qual_teachers() + 1
        self.qual_row_table_2 = self.db.get_qual_forms() + 1

        self.qual_row_table_3 = self.qual_row_table_1  # кол-во учителей одинаково
        self.info_teachers_table.setRowCount(self.qual_row_table_3)

        self.qual_row_table_4 = self.db.get_qual_classrooms() + 1
        self.info_classrooms_table.setRowCount(self.qual_row_table_4)

        self.qual_row_table_5 = self.qual_row_table_2
        self.info_forms_table.setRowCount(self.qual_row_table_5)

        # создаем таблицы расписания учителей и классов
        self.create_timetable(self.timetable, "ФИО Учителя", self.qual_row_table_1)
        self.create_timetable(self.timetable_2, "Класс              ", self.qual_row_table_2)

        # запрещаем редактирование столбца с именами учителей(классов), для этого есть отдельная таблица
        self.timetable.setItemDelegateForColumn(0, ReadOnlyDelegate(self.timetable))
        self.timetable_2.setItemDelegateForColumn(0, ReadOnlyDelegate(self.timetable_2))
        for i in range(3):
            self.info_classrooms_table.setItemDelegateForColumn(i, ReadOnlyDelegate(self.info_classrooms_table))

        # заполняем первую колонку учителей(или классов) в расписании
        teachers = self.db.get_all_teachers()
        for i in range(self.qual_row_table_1 - 1):
            self.timetable.setItem(i, 0, QTableWidgetItem(teachers[i]))

        forms = self.db.get_all_forms()
        for i in range(self.qual_row_table_2 - 1):
            self.timetable_2.setItem(i, 0, QTableWidgetItem(forms[i][0]))

        # Загружаем значения в расписаниях
        self.load_timetable_values()

        # Загружаем информацию об учителях
        self.load_info_teachers_table()

        self.names = {}  # заранее сохраняем соотвествие № строк и id учителя
        for i in range(self.qual_row_table_3 - 1):
            self.names[i] = self.db.get_teacher_id(self.info_teachers_table.item(i, 0).text())

        # загружаем информацию о кабинетах
        self.load_info_classrooms_table()

        # загружаем информацию о классах
        self.load_info_forms_table()

        self.forms = {}  # заранее сохраняем соотвествие № строк и id класса
        for i in range(self.qual_row_table_5 - 1):
            self.forms[i] = self.db.get_form_id(self.db.form_to_numlet(self.info_forms_table.item(i, 0).text()))

        # загружаем информацию о времени уроков
        self.load_info_lessons_table()

        # включаем реакцию таблиц на изменения в них
        self.connect_tables()

    # ----------------------------------------connecting_funktions--------------------------------------------

    def connect_tables(self):  # включаем реакцию на изменение таблиц пользователем
        self.info_forms_table.itemChanged.connect(self.save_form_table)  # классы
        self.info_teachers_table.itemChanged.connect(self.save_teacher_table)  # учителя
        self.info_lessons_table.itemChanged.connect(self.save_lesson_info)  # время уроков
        self.timetable.itemChanged.connect(self.save_timetable_1)
        self.timetable_2.itemChanged.connect(self.save_timetable_2)

    def disconnect_tables(self):
        self.info_forms_table.itemChanged.disconnect(self.save_form_table)  # классы
        self.info_teachers_table.itemChanged.disconnect(self.save_teacher_table)  # учителя
        self.info_lessons_table.itemChanged.disconnect(self.save_lesson_info)  # время уроков
        self.timetable.itemChanged.disconnect(self.save_timetable_1)
        self.timetable_2.itemChanged.disconnect(self.save_timetable_2)

    # ---------------------------------------------statusbar-------------------------------------------------

    def show_error_message(self, message):

        self.statusbar.showMessage(message)
        self.statusbar.setStyleSheet('background-color : red')

    def show_ok_message(self):
        self.statusbar.showMessage('Statusbar')
        self.statusbar.setStyleSheet('background-color : white')

    # ---------------------------------------------showing_info_functions--------------------------------------

    @staticmethod
    def create_timetable(timetable, first_title, row_qual):  # заполняем заголовки колонок, без содержимого
        timetable.setColumnCount(49)
        timetable.setRowCount(row_qual)
        timetable.horizontalHeader().setDefaultSectionSize(38)

        # устанавливаем заголовки и их цвета
        timetable.setHorizontalHeaderItem(0, QTableWidgetItem(first_title))
        for i in range(6):  # кол-во рабочих дней недели
            for j in range(1, 9):  # по 8 уроков
                item1 = QTableWidgetItem(str(j))
                item1.setBackground(RAINBOW_COLORS[i][1])
                timetable.setHorizontalHeaderItem(i * 8 + j, item1)

        # блокируем изменение ширины колонок пользователем, выставляем размер у 1-й колонки как исключение
        timetable.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        timetable.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def load_timetable_values(self):
        # table_1

        # загружаем учителей
        teachers = self.db.get_all_teachers()
        for i in range(self.qual_row_table_1 - 1):
            self.timetable.setItem(i, 0, QTableWidgetItem(teachers[i][:13]))
        self.timetable.setItem(self.qual_row_table_1 - 1, 0, QTableWidgetItem())

        # загружаем значения
        for i in range(self.qual_row_table_1):
            teacher = self.timetable.item(i, 0).text() if self.timetable.item(i, 0) else ''
            for j in range(1, 49):
                day = (j - 1) // 8 + 1
                n_lesson = j - (day - 1) * 8

                form = self.db.get_lesson_info(day, n_lesson, teacher=teacher)

                if form:  # если ячейка заполнена
                    item = QTableWidgetItem(str(form[0]) + str(form[1]).lower())
                else:
                    item = QTableWidgetItem()

                item.setBackground(RAINBOW_COLORS[day - 1][0])
                self.timetable.setItem(i, j, item)

        # table_2

        # загружаем классы
        forms = self.db.get_all_forms()
        for i in range(self.qual_row_table_2 - 1):
            self.timetable_2.setItem(i, 0, QTableWidgetItem(forms[i][0]))
        self.timetable_2.setItem(self.qual_row_table_2 - 1, 0, QTableWidgetItem())

        # загружаем значения
        for i in range(self.qual_row_table_2):
            form = self.timetable_2.item(i, 0).text() if self.timetable_2.item(i, 0) else ''
            for j in range(1, 49):
                day = (j - 1) // 8 + 1
                n_lesson = j - (day - 1) * 8

                # Будем показывать не имя преподавателя, а его предмет
                subject = self.db.get_lesson_info(day, n_lesson, form=form)
                if subject:
                    item = QTableWidgetItem(subject[0][:4])
                else:
                    item = QTableWidgetItem()
                item.setBackground(RAINBOW_COLORS[day - 1][0])
                self.timetable_2.setItem(i, j, item)

    def load_info_teachers_table(self):
        teachers = self.db.get_all_teachers()
        info = sorted(list(map(lambda t: (t, self.db.get_teacher_id(t)), teachers)), key=lambda x: x[1])
        # info = [(name1, id1), (name2, id2),...]
        for i, t in enumerate(info):
            teacher, id = t[0], t[1]
            teacher_info = self.db.get_teacher_info(id)

            # графа "ФИО" задается всегда
            self.info_teachers_table.setItem(i, 0, QTableWidgetItem(teacher))

            if teacher_info['subj']:
                self.info_teachers_table.setItem(i, 1, QTableWidgetItem(teacher_info['subj'][0]))
            else:
                self.info_teachers_table.setItem(i, 1, QTableWidgetItem())

            if teacher_info['management']:
                self.info_teachers_table.setItem(i, 2, QTableWidgetItem(str(teacher_info['management'][0]) +
                                                                        teacher_info['management'][1]))
            else:
                self.info_teachers_table.setItem(i, 2, QTableWidgetItem())

            if teacher_info['classroom']:
                self.info_teachers_table.setItem(i, 3, QTableWidgetItem(str(teacher_info['classroom'][0])))
            else:
                self.info_teachers_table.setItem(i, 3, QTableWidgetItem())

            if teacher_info['hours']:
                self.info_teachers_table.setItem(i, 4, QTableWidgetItem(str(teacher_info['hours'])))
            else:
                self.info_teachers_table.setItem(i, 4, QTableWidgetItem())

            if teacher_info['forms']:
                self.info_teachers_table.setItem(i, 5, QTableWidgetItem(', '.join(list(map(lambda x: str(x[0]) +
                                                                                                     str(x[1]).upper(),
                                                                                           teacher_info['forms'])))))

    def load_info_classrooms_table(self):
        info = self.db.get_all_classrooms()  # [(id1, num1), (id2, num2)...]
        self.qual_row_table_4 = self.db.get_qual_classrooms() + 1
        self.info_classrooms_table.setRowCount(self.qual_row_table_4)
        for i, j in enumerate(info):  # i: 0, j: (id1, num1)
            id, num = j[0], j[1]
            info = self.db.get_classroom_info(id)

            self.info_classrooms_table.setItem(i, 0, QTableWidgetItem(str(num)))  # номер

            if info['subj']:  # предмет
                self.info_classrooms_table.setItem(i, 1, QTableWidgetItem(info['subj'][0]))
            else:
                self.info_classrooms_table.setItem(i, 1, QTableWidgetItem())

            if info['teacher']:
                self.info_classrooms_table.setItem(i, 2, QTableWidgetItem(info['teacher'][0]))
            else:
                self.info_classrooms_table.setItem(i, 2, QTableWidgetItem())

    def load_info_forms_table(self):
        forms = self.db.get_all_forms()

        self.qual_row_table_5 = self.db.get_qual_forms() + 1
        self.info_forms_table.setRowCount(self.qual_row_table_5)

        for i, j in enumerate(forms):
            form, id = j[0].upper(), j[1]
            info = self.db.get_form_info(id)
            # print(info)

            self.info_forms_table.setItem(i, 0, QTableWidgetItem(form))  # название

            if info['manager']:
                self.info_forms_table.setItem(i, 1, QTableWidgetItem(info['manager'][0]))
            else:
                self.info_forms_table.setItem(i, 1, QTableWidgetItem())

            if info['subj']:
                self.info_forms_table.setItem(i, 2, QTableWidgetItem(info['subj'][0]))
            else:
                self.info_forms_table.setItem(i, 2, QTableWidgetItem())

    def load_info_lessons_table(self):
        for i in range(1, 9):
            info = self.db.get_n_lesson_info(i)
            self.info_lessons_table.setItem(i - 1, 0, QTableWidgetItem(info[0]))
            self.info_lessons_table.setItem(i - 1, 1, QTableWidgetItem(info[1]))

    # ---------------------------------------------editing_info_functions--------------------------------------

    def save_teacher_table(self, e):
        row, col, new_text = e.row(), e.column(), e.text()
        try:
            if col == 0:  # если изменено имя
                if row in self.names:  # если имя уже было задано(изменяемая строка таблицы уже есть!!!!!!!)
                    if new_text:  # если это просто изменение в имени(БЕЗ УДАЛЕНИЯ)
                        self.db.edit_teacher_info(self.names[row], full_name=new_text)

                    else:  # если новая строка пустая (УДАЛЯЕМ!!!!)
                        if row == self.qual_row_table_3 - 2:  # если это последняя строка
                            self.db.delete_teacher_info(self.names[row])  # удаляем из БД
                            del self.names[row]  # удаляем из словаря

                            # уменьшаем кол-во строк
                            self.qual_row_table_3 -= 1  #
                            self.info_teachers_table.setRowCount(self.qual_row_table_3)  #
                            self.qual_row_table_1 = self.qual_row_table_3  #
                            self.timetable.setRowCount(self.qual_row_table_1)  #

                            # перезагружаем таблицу
                            self.load_info_teachers_table()
                        else:
                            self.info_teachers_table.setItem(row, col,
                                                             QTableWidgetItem(self.db.get_teacher_info(self.names[row])
                                                                              ['name']))
                    # обновляем таблицы, где есть упоминания учителей

                else:  # если данного имени еще нет (ДОБАВЛЯЕМ НОВУЮ ЗАПИСЬ!!!!)

                    # обновляем информацию в БД
                    new_teacher_id = self.db.add_teacher()
                    self.names[row] = new_teacher_id
                    self.db.edit_teacher_info(new_teacher_id, full_name=new_text)

                    # увеличиваем кол-во строк в таблице на 1
                    self.qual_row_table_3 += 1
                    self.qual_row_table_1 = self.qual_row_table_3

                    self.info_teachers_table.setRowCount(self.qual_row_table_3)
                    self.timetable.setRowCount(self.qual_row_table_1)


            elif col == 1:
                self.db.edit_teacher_info(self.names[row], subj=new_text)

            elif col == 2:
                self.db.edit_teacher_info(self.names[row], manag=new_text)

            elif col == 3:
                self.db.edit_teacher_info(self.names[row], classroom=new_text)


            elif col == 4:
                self.db.edit_teacher_info(self.names[row], hours=new_text)

            elif col == 5:
                self.db.edit_teacher_info(self.names[row], forms=new_text)

            self.disconnect_tables()
            self.load_info_classrooms_table()
            self.load_info_forms_table()
            self.load_timetable_values()  # после обновляем расписание
            self.connect_tables()

        except KeyError:
            self.statusbar.showMessage('Проверьте корректность входных данных, или перезагрузите приложение')

    def save_form_table(self, e):
        # отключаем таблицы
        self.disconnect_tables()

        row, col, new_text = e.row(), e.column(), e.text()
        try:
            if col == 0:  # если изменялось название класса
                if row in self.forms:  # если название уже было задано(изменяемая строка таблицы уже есть!!!!!!!)
                    if new_text:  # если это просто изменение в названии(БЕЗ УДАЛЕНИЯ)
                        a = self.db.get_form_info(self.forms[row])['form']
                        self.info_forms_table.setItem(row, col,
                                                      QTableWidgetItem(str(a[0]) + str(a[1]).upper()))
                        self.statusbar.showMessage('Нельзя изменить букву класса')
                        self.statusBar().setStyleSheet('background-color : red')

                    else:  # если новая строка пустая (УДАЛЯЕМ!!!!)
                        if row == self.qual_row_table_5 - 2:  # если это последняя строка
                            self.db.delete_form_info(self.forms[row])  # удаляем из БД
                            del self.forms[row]  # удаляем из словаря

                            # уменьшаем кол-во строк
                            self.qual_row_table_5 -= 1
                            self.info_forms_table.setRowCount(self.qual_row_table_5)
                            self.qual_row_table_2 = self.qual_row_table_5
                            self.timetable_2.setRowCount(self.qual_row_table_2)

                            # перезагружаем таблицу

                        else:
                            # возвращаем "все как было"
                            a = self.db.get_form_info(self.forms[row])['form']
                            self.info_forms_table.setItem(row, col,
                                                          QTableWidgetItem(str(a[0]) + str(a[1]).upper()))
                        # обновляем таблицы, где есть упоминания учителей
                        self.load_info_teachers_table()

                else:  # если данного класса еще нет (ДОБАВЛЯЕМ НОВУЮ ЗАПИСЬ!!!!)

                    # обновляем информацию в БД
                    new_form_id = self.db.add_form(self.db.form_to_numlet(new_text))
                    self.forms[row] = new_form_id
                    self.db.edit_form_info(new_form_id)

                    # увеличиваем кол-во строк в таблице на 1
                    self.qual_row_table_5 += 1
                    self.qual_row_table_2 = self.qual_row_table_5

                    self.info_forms_table.setRowCount(self.qual_row_table_5)
                    self.timetable_2.setRowCount(self.qual_row_table_2)

            elif col == 1:
                self.db.edit_form_info(self.forms[row], teacher=new_text)

            elif col == 2:
                self.db.edit_form_info(self.forms[row], subj=new_text)

            # обновляем таблицы и подключаем их назад
            self.load_info_forms_table()
            self.load_timetable_values()
            self.load_info_teachers_table()
            self.connect_tables()

        except KeyError:
            self.statusbar.showMessage('Проверьте корректность входных данных, или перезагрузите приложение')

    def save_lesson_info(self, e):
        row, col, new_text = e.row(), e.column(), e.text()
        if new_text:
            if col == 0:
                self.db.edit_n_lesson_info(row + 1, start=new_text)  # индексы в БД начинаются с 1, а не с 0
            elif col == 1:
                self.db.edit_n_lesson_info(row + 1, finish=new_text)
            self.show_ok_message()
        else:
            self.show_error_message('Нельзя удалять время начала или конца, только изменять!')

    def save_timetable_1(self, e):
        row, col, new_text = e.row(), e.column(), e.text()
        day = (col - 1) // 8 + 1
        n_lesson = col - (day - 1) * 8
        try:
            a = self.db.get_lesson_info(day, n_lesson, self.timetable.item(row, 0).text())
            assert new_text != a
            if new_text != '':
                self.db.edit_lesson_info(day, n_lesson, self.names[row], self.db.get_form_id(new_text))
            else:
                self.db.edit_lesson_info(day, n_lesson, self.names[row], new_text)
        except AssertionError:
            self.show_error_message('Проверьте корректность входных данных или перезапустите программу')

        self.disconnect_tables()
        self.load_timetable_values()
        self.connect_tables()

    def save_timetable_2(self, e):
        row, col, new_text = e.row(), e.column(), e.text()
        day = (col - 1) // 8 + 1
        n_lesson = col - (day - 1) * 8
        try:
            self.db.edit_lesson_info(day, n_lesson, new_text, self.forms[row])
        except AssertionError:
            self.show_error_message('Проверьте корректность входных данных или перезапустите программу')

        self.disconnect_tables()
        self.load_timetable_values()
        self.connect_tables()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())
