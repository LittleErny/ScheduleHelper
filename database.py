import sqlite3


class DataBase:
    def __init__(self, file):
        self.file = file

        # Подключаемся к БД
        self.con = sqlite3.connect(file)

        # Создание курсора
        self.cur = self.con.cursor()

    @staticmethod
    def form_to_numlet(name):
            if len(name) == 2:
                return name[0], name[1].lower()
            else:
                return name[:1], name[2].lower()

    # Функция подготовки расписания, т.е. заранее заполняет дни недели, номера уроков и тп
    def prepare_timetable(self):
        for day in self.cur.execute("""SELECT id FROM weekdays""").fetchall():
            n_lessons = self.cur.execute("""SELECT id FROM lessons""").fetchall()
            for num_les in n_lessons:
                for classroom in self.cur.execute("""SELECT id FROM classrooms""").fetchall():
                    lesson_id = self.cur.execute("""SELECT id FROM schedule 
                                                    WHERE weekday = ?
                                                    AND n_lesson = ?
                                                    AND classroom = ?""", (day[0], num_les[0], classroom[0])).fetchone()
                    teacher = self.cur.execute("""SELECT teacher FROM teachersubject WHERE classroom = ?""",
                                               (classroom[0],)).fetchone()
                    if not lesson_id and teacher:
                        self.cur.execute("""INSERT INTO schedule(weekday, n_lesson, classroom) VALUES(?, ?, ?)""",
                                         (day[0], num_les[0], classroom[0]))

        self.con.commit()

    # -----------------------------------getting_information_functions----------------------------------

    def get_teacher_id(self, name):
        return self.cur.execute("""SELECT id FROM teachers
                                   WHERE full_name = ?""", (name,)).fetchone()[0]

    def get_teacher_info(self, id):

        info = {
            'name': self.cur.execute("""SELECT full_name FROM teachers
                                        WHERE id = ?""", (id,)).fetchall()[0][0],

            'subj': self.cur.execute("""SELECT name FROM subjects
                                            WHERE id IN (
                                                SELECT subject FROM teachersubject
                                                WHERE teacher = ?)""", (id,)).fetchone(),

            'management': self.cur.execute("""SELECT number, letter FROM forms
                                                         WHERE id = (
                                                             SELECT form FROM formmanagement
                                                             WHERE teacher = ?)""", (id,)).fetchone(),

            'classroom': self.cur.execute("""SELECT number FROM classrooms
                                                    WHERE id = (
                                                        SELECT classroom FROM teachersubject
                                                        WHERE teacher = ?)""", (id,)).fetchone(),

            'hours': self.cur.execute("""SELECT hours_a_week FROM teachers
                                                    WHERE id = ?""", (id,)).fetchone()[0],

            'forms': self.cur.execute("""SELECT number, letter FROM forms
                                            WHERE id IN (
                                                SELECT form FROM teacherforms
                                                WHERE teacher = ?)""", (id,)).fetchall()
        }

        return info

    def get_classroom_id(self, number):
        return self.cur.execute("""SELECT id FROM classrooms
                                    WHERE number = ?""", (number,)).fetchone()

    def get_classroom_info(self, id):
        info = {
            'num': self.cur.execute("""SELECT number FROM classrooms
                                        WHERE id = ?""", (id,)).fetchone()[0],

            'subj': self.cur.execute("""SELECT name FROM subjects
                                            WHERE id = (
                                                SELECT subject FROM teachersubject
                                                WHERE classroom = ?)""", (id,)).fetchone(),

            'teacher': self.cur.execute("""SELECT full_name FROM teachers
                                            WHERE id IN (
                                                SELECT teacher FROM teachersubject
                                                WHERE classroom = ?)""", (id,)).fetchone()
        }
        return info

    def get_form_id(self, name):
        number, letter = self.form_to_numlet(name)
        return str(self.cur.execute("""SELECT id FROM forms
                                    WHERE number = ? and letter = ?""", (number, letter)).fetchone()[0])

    def get_form_info(self, id):
        info = {
            'form': self.cur.execute("""SELECT number, letter FROM forms
                                        WHERE id = ?""", (int(id),)).fetchone(),

            'manager': self.cur.execute("""SELECT full_name FROM teachers
                                                        WHERE id = (
                                                            SELECT teacher FROM formmanagement
                                                            WHERE form = ?)""", (id,)).fetchone(),

            'subj': self.cur.execute("""SELECT name FROM subjects
                                        WHERE id = (
                                            SELECT subject FROM forms
                                            WHERE id = ?)""", (id,)).fetchone()
        }
        return info

    def get_n_lesson_info(self, id):
        try:
            return *self.cur.execute("""SELECT start, finish FROM lessons
                                                        WHERE id = ?""", (id,)).fetchone(),
        except TypeError:
            return None, None

    def get_lesson_info(self, weekday_id, lesson_id, teacher=None, form=None):
        if form:
            return self.cur.execute("""SELECT name FROM subjects WHERE id = (
                                            SELECT subject FROM teachersubject WHERE teacher = (
                                                SELECT teacher FROM schedule
                                                WHERE weekday = ?
                                                AND n_lesson = ?
                                                AND form = (SELECT id FROM forms
                                                            WHERE number = ?
                                                            AND letter = ?)))""",
                                    (weekday_id, lesson_id, *self.form_to_numlet(form))).fetchone()

        if teacher:
            return self.cur.execute("""SELECT number, letter FROM forms WHERE id = 
                                            (SELECT form FROM schedule 
                                            WHERE weekday = ?
                                            AND n_lesson = ?
                                            AND teacher = 
                                            (SELECT id FROM teachers WHERE full_name = ?))""",
                                    (weekday_id, lesson_id, teacher)).fetchone()

    def get_qual_teachers(self):
        return len(self.get_all_teachers())

    def get_all_teachers(self):
        return list(map(lambda x: x[0], self.cur.execute("""SELECT full_name FROM teachers""").fetchall()))

    def get_qual_forms(self):
        return len(self.cur.execute("""SELECT id FROM forms""").fetchall())

    def get_all_forms(self):
        return list(map(lambda x: (str(x[0]) + str(x[1]).lower(), x[2]),
                        self.cur.execute("""SELECT number, letter, id FROM forms""")))

    def get_all_classrooms(self):
        return self.cur.execute("""SELECT id, number FROM classrooms""").fetchall()

    def get_qual_classrooms(self):
        return len(self.get_all_classrooms())

    # --------------------------------------------------editing_functions-----------------------------------------------

    def add_teacher(self):  # создание пустую строку в таблице училелей и заполнение таблиц с учителем, кроме расписания
        self.cur.execute("""INSERT INTO teachers(full_name) VALUES(NULL)""")
        id = self.cur.execute("""SELECT MAX(id) FROM teachers""").fetchone()[0]
        self.cur.execute("""INSERT INTO teachersubject(teacher) VALUES(?)""", (id,))
        self.cur.execute("""INSERT INTO formmanagement(teacher) VALUES(?)""", (id,))
        self.cur.execute("""INSERT INTO teacherforms(teacher) VALUES(?)""", (id,))
        self.con.commit()
        return id

    def edit_teacher_info(self, id, full_name=None, subj=None, manag=None, classroom=None, hours=None, forms=None):
        if full_name:
            self.cur.execute("""UPDATE teachers 
                                SET full_name = ?
                                WHERE id = ?""",
                             (full_name, id))

        if subj is not None:
            if subj != '':
                subj_id = self.cur.execute("""SELECT id FROM subjects WHERE name = ?""", (subj,)).fetchone()
                if not subj_id:
                    self.add_subject(subj)  # если данного предмета еще нет, то мы его добавляем
                    subj_id = self.cur.execute("""SELECT MAX(id) FROM subjects""").fetchone()  # id предмета
                self.cur.execute("""UPDATE teachersubject
                                    SET subject = ?
                                    WHERE teacher = ?""", (subj_id[0], id))
            else:
                self.cur.execute("""UPDATE teachersubject
                                                    SET subject = ?
                                                    WHERE teacher = ?""", (None, id))

        if manag is not None:
            if manag == '':
                self.cur.execute("""UPDATE formmanagement
                                                SET form = NULL
                                                WHERE teacher = ?""", (id,))
            else:

                num, let = self.form_to_numlet(manag)
                if not self.cur.execute("""SELECT id FROM forms WHERE number = ? AND letter = ?""", (num, let)).fetchone():
                    self.add_form(manag)
                self.cur.execute("""UPDATE formmanagement
                                    SET form = (SELECT id FROM forms WHERE number = ? and letter = ?)
                                    WHERE teacher = ?""", (num, let, id))

        if classroom is not None:
            room_id = self.cur.execute("""SELECT id FROM classrooms WHERE number = ?""", (int(classroom),)).fetchone()
            if not room_id:
                if classroom != '':
                    room_id = self.add_classroom(classroom)  # если данного кабинета еше нет, мы его добавляем
                else:
                    room_id = (None,)

            self.cur.execute("""UPDATE teachersubject
                                SET classroom = ?
                                WHERE teacher = ?""", (room_id[0], id))

            self.prepare_timetable()  # если мы убрали/добавили кабинет, или открепили его от учителя, то

        if hours:
            self.cur.execute("""UPDATE teachers
                                SET hours_a_week = ?
                                WHERE id = ?""", (hours, id))

        if forms is not None:
            self.cur.execute("""DELETE FROM teacherforms
                                WHERE teacher = ?""", (id,))
            for form in forms.split(', '):
                if form:
                    num, let = self.form_to_numlet(form)
                    if not self.cur.execute("""SELECT id FROM forms WHERE number = ? AND letter = ?""",
                                            (num, let)).fetchone():
                        form_id = self.add_form(form)
                        self.cur.execute("""INSERT INTO teacherforms(teacher, form) VALUES(?, ?)""", (id, form_id))
                    self.cur.execute("""INSERT INTO teacherforms(teacher, form) VALUES(?, (
                                            SELECT id FROM forms WHERE number = ? AND letter = ?))""", (id, num, let))

        self.con.commit()

    def add_subject(self, name):
        self.cur.execute("""INSERT INTO subjects(name) VALUES(?)""", (name,))

        return self.cur.execute("""SELECT MAX(id) FROM subjects""").fetchone()[0]

    def add_classroom(self, number):  # возвращает id добавленного кабинета
        self.cur.execute("""INSERT INTO classrooms(number) VALUES(?)""", (number,))
        # self.con.commit()
        return self.cur.execute("""SELECT MAX(id) FROM classrooms""").fetchone()

    def add_form(self, name):
        num, let = self.form_to_numlet(name)
        self.cur.execute("""INSERT INTO forms(number, letter) VALUES(?, ?)""", (num, let))
        # self.con.commit()
        return self.cur.execute("""SELECT MAX(id) FROM forms""").fetchone()[0]

    def edit_form_info(self, id, teacher=None, subj=None):
        if teacher is not None:
            teacher_id = self.cur.execute("""SELECT id FROM teachers WHERE full_name = ?""", (teacher,)).fetchone()
            if teacher_id:
                self.cur.execute("""UPDATE formmanagement
                                    SET form = ?
                                    WHERE teacher = ?""", (int(id), teacher_id[0]))
            elif teacher == '':
                self.cur.execute("""UPDATE formmanagement
                                    SET form = NULL
                                    WHERE teacher = (SELECT teacher FROM formmanagement WHERE form = ?)""", (int(id),))
            else:
                new_teacher_id = self.add_teacher()
                self.edit_teacher_info(new_teacher_id, full_name=teacher)
                self.cur.execute("""UPDATE formmanagement
                                    SET form = ?
                                    WHERE teacher = ?""", (id, teacher_id))

        if subj is not None:
            if not self.cur.execute("""SELECT id FROM subjects WHERE name = ?""", (subj,)).fetchone():
                self.add_subject(subj)  # если данного предмета еще нет, то мы его добавляем

            self.cur.execute("""UPDATE forms
                                SET subject = (SELECT id FROM subjects WHERE name = ?)
                                WHERE id = ?""", (subj, int(id)))

        self.con.commit()

    def edit_n_lesson_info(self, id, start=None, finish=None):
        if start:
            self.cur.execute("""UPDATE lessons
                                SET start = ?
                                WHERE id = ?""", (start, id))

        if finish:
            self.cur.execute("""UPDATE lessons
                                SET finish = ?
                                WHERE id = ?""", (finish, id))

        self.con.commit()

    def edit_lesson_info(self, weekday, n_lesson, teacher, form):
        # assert self.cur.execute("""SELECT classroom FROM teachersubject WHERE teacher = ?""").fetchone()
        if form == '' or teacher == '':
            self.cur.execute("""UPDATE schedule
                            SET form = NULL, teacher = NULL
                            WHERE weekday = ? AND n_lesson = ? AND classroom = 
                            (SELECT classroom FROM teachersubject WHERE teacher = ?)""",
                         (weekday, n_lesson, teacher))
        else:
            self.cur.execute("""UPDATE schedule
                                SET form = ?, teacher = ?
                                WHERE weekday = ? AND n_lesson = ? AND classroom = 
                                (SELECT classroom FROM teachersubject WHERE teacher = ?)""",
                             (form, teacher, weekday, n_lesson, teacher))

        self.con.commit()

    def delete_teacher_info(self, id):
        self.cur.execute("""DELETE FROM formmanagement
                            WHERE teacher = ?""", (id,))
        self.cur.execute("""DELETE FROM schedule
                                    WHERE teacher = ?""", (id,))
        self.cur.execute("""DELETE FROM teachersubject
                                    WHERE teacher = ?""", (id,))
        self.cur.execute("""DELETE FROM teacherforms
                                    WHERE teacher = ?""", (id,))
        self.cur.execute("""DELETE FROM teachers
                                    WHERE id = ?""", (id,))

        self.con.commit()

    def delete_form_info(self, id):
        self.cur.execute("""DELETE FROM formmanagement
                            WHERE form = ?""", (id,))
        self.cur.execute("""DELETE FROM schedule
                                    WHERE form = ?""", (id,))
        self.cur.execute("""DELETE FROM teacherforms
                                    WHERE form = ?""", (id,))
        self.cur.execute("""DELETE FROM forms
                                    WHERE id = ?""", (id,))

        self.con.commit()


# db = DataBase('Schedule.db')
