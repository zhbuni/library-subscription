import sys

from PyQt5 import uic
from PyQt5.QtCore import QDate
from PyQt5.QtWidgets import QApplication, QMainWindow,\
    QTableWidgetItem, QDialog

import sqlite3
from sqlite3 import Date


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('untitled.ui', self)

        self.con = sqlite3.connect("library.db")
        self.cur = self.con.cursor()

        self.search.clicked.connect(self.searchBook)
        self.addBookButton.clicked.connect(self.addBook)
        self.addAuthorButton.clicked.connect(self.addAuthor)
        self.addVisitorButton.clicked.connect(self.addVisitor)
        self.GiveOutBookButton.clicked.connect(self.giveOutBook)

    def giveOutBook(self):
        self.label.setText('')
        if len(self.tableWidget.selectedItems()) > 8:
            self.label.setText('Выберите одну книгу.')
            return
        self.label.setText('')
        id = self.tableWidget.currentRow()
        if id == -1:
            self.label.setText('Выберите книгу.')
        else:
            self.dialog = GiveOutBookClass(id, parent=self)
            self.dialog.show()

    def searchBook(self):
        txt = self.box.currentText()
        searchText = self.edit.text()
        self.label.setText('')
        result = []
        self.tableWidget.clear()
        if txt == 'Название':
            result = self.cur.execute("""SELECT * FROM books
            WHERE title LIKE '%{}'""".format(searchText)).fetchall()
        elif txt == 'Автор':
            name1, surname1 = '', ''
            try:
                name1, surname1 = searchText.split()
            except ValueError:
                print('Имя введено некорректно')
            print(name1, surname1)
            result1 = self.cur.execute("""SELECT id from author 
            WHERE name LIKE '{}'
             AND surname LIKE '{}'""".format(name1, surname1)).fetchall()
            if len(result1) == 1:
                result1 = result1[0][0]
            result = self.cur.execute("""SELECT * FROM books
                        WHERE author = '{}'""".format(result1)).fetchall()
        elif txt == 'Жанр':
            result = self.cur.execute("""SELECT * FROM books
                                    WHERE LOWER(genre) = LOWER('{}')  """.format(searchText)).fetchall()
        elif txt == 'Издательство':
            result1 = self.cur.execute("""SELECT id from publishing 
                        WHERE title = '{}'""".format(searchText)).fetchall()
            if len(result1) == 1:
                result1 = result1[0][0]
            print(result1)
            result = self.cur.execute("""SELECT * FROM books
                                    WHERE LOWER(pubhouse) = LOWER('{}')""".format(result1)).fetchall()
        else:
            result = self.cur.execute("""
            SELECT
             books.title, books.ISBN, 
             author.surname, publishing.title, 
             CASE WHEN books.IsAvailable = 1 THEN "Да" ELSE "Нет" END AS "IsAvailable",
			 books.pub_Year, books.genre
            FROM books
            INNER JOIN author ON author.id = books.author
            INNER JOIN publishing ON publishing.id = books.pubHouse
            """).fetchall()
        self.tableWidget.setColumnCount(7)
        self.tableWidget.setHorizontalHeaderLabels(['title',  'ISBN',  'Author',  'Publishing',
                                                    'pubYear',
                                                    'isAvailable',
                                                    'Genre',
                                                    ])
        self.tableWidget.setRowCount(0)
        for i, row in enumerate(result):
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))
        self.tableWidget.resizeColumnsToContents()
        print(result)

    def addBook(self):
        self.dialog = BookAddDialog(self)
        self.dialog.show()

    def addAuthor(self):
        self.is_visitor = False
        self.dialog = AuthorAddDialog(self)
        self.dialog.show()

    def addVisitor(self):
        self.is_visitor = True
        self.dialog = AuthorAddDialog(self)
        self.dialog.show()

    def closeEvent(self, event):
        self.con.close()


class GiveOutBookClass(QDialog):
    def __init__(self, BookId, parent=None):
        super(GiveOutBookClass, self).__init__(parent)
        self.parent = parent
        self.book_id = BookId
        self.setWindowTitle('Выдать книгу')
        self.setModal(True)
        uic.loadUi('giveOut.ui', self)
        self.addButton.clicked.connect(self.giveOut)

    def giveOut(self):
        self.statusLabel.setText('')
        name = self.nameEdit.text()
        surname = self.surnameEdit.text()

        date = self.dateEdit.text()
        if len(date.split('.')) != 3:
            self.statusLabel.setText('Неверный формат даты')
            return
        else:
            day, month, year = [el for el in date.split('.')]
            if not day.isdigit() or not month.isdigit() or not year.isdigit():
                self.statusLabel.setText('Неверный формат даты')
                return

        visitor = self.parent.cur.execute("""SELECT id FROM visitor WHERE
         name LIKE '{}' AND surname
          LIKE '{}'""".format(name, surname)).fetchall()

        if not name:
            self.statusLabel.setText('Неккорректное имя.')
        elif not surname:
            self.statusLabel.setText('Неккоректная фамилия.')
        elif not visitor:
            self.statusLabel.setText('Такого посетителя нет.')
        else:
            id = self.parent.cur.execute("""SELECT COUNT(id) FROM ListOfBooks""").fetchall()
            id = str(id[0][0]) if id else 0
            print(Date.month)
            print(self.parent.cur.execute("""SELECT * FROM ListOfBOoks""").fetchall())

            self.parent.cur.execute("""INSERT INTO ListOfBooks
             VALUES ('{}', '{}', '{}')""".format(id, visitor, self.book_id, ))
            print(self.parent.cur.execute("""SELECT * FROM ListOfBOoks
            WHERE id = '{}'""".format(id)).fetchall())

class BookAddDialog(QDialog):
    def __init__(self, parent=None):
        super(BookAddDialog, self).__init__(parent)
        self.parent = parent
        self.setModal(True)
        uic.loadUi('addDialog.ui', self)
        self.addButtonDialog.clicked.connect(self.addBook)

    def addBook(self):
        name, surname = self.nameEdit.text(), self.surnameEdit.text()

        self.statusLabel.setText('')

        pubHouse = self.parent.cur.execute("""
        SELECT id FROM Publishing WHERE title = '{}'""".format(self.pubEdit.text())).fetchall()
        author = self.parent.cur.execute("""SELECT * FROM Author WHERE 
        name = '{}' AND surname = '{}'""".format(name, surname)).fetchall()

        author = str(author[0][0]) if author else ''
        pubHouse = str(pubHouse[0][0]) if pubHouse else ''
        id = self.parent.cur.execute("""SELECT COUNT(id) FROM books""").fetchall()
        id = str(id[0][0]) if id else ''
        if not self.titleEdit.text():
            self.statusLabel.setText('Некорректное название')
        elif not author:
            self.statusLabel.setText('Такого автора нет')
        elif not pubHouse:
            self.statusLabel.setText('Такого издательства нет')
        elif not self.genreEdit.text():
            self.statusLabel.setText('Неккоректный жанр')
        else:
            title = self.titleEdit.text()
            genre = self.genreEdit.text()

            pubHouseBooks = self.parent.cur.execute("""SELECT COUNT(id) FROM books
            WHERE pubHouse = '{}'""".format(str(pubHouse))).fetchall()

            pubHouseBooks = pubHouseBooks[0][0] if pubHouseBooks else ''
            pubHouseBooks = str(pubHouseBooks).rjust(3, '0')

            ISBN = '978-5-' + str(pubHouse) + '-' + pubHouseBooks

            currentYear = str(QDate.currentDate().year())

            self.parent.cur.execute("""INSERT INTO books VALUES ('{}', '{}', 
            '{}', '{}', '{}', '{}', '{}', '{}')""".format(id, title, ISBN,
                                                          author, pubHouse,
                                                          currentYear, 1, genre))
            self.parent.label.setText('Книга успешно добавлена.')
            self.close()


class AuthorAddDialog(QDialog):
    def __init__(self, parent=None):
        super(AuthorAddDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle('Добавить автора')
        self.setModal(True)
        uic.loadUi('addAuthor.ui', self)
        self.addButton.clicked.connect(self.addAuthor)

    def addAuthor(self):
        name = self.nameEdit.text()
        surname = self.surnameEdit.text()
        print(self.parent.cur.execute("""SELECT * FROM visitor""").fetchall())

        id = self.parent.cur.execute("""SELECT COUNT(id) FROM author""").fetchall()
        id = str(id[0][0]) if id else ''
        print(self.parent.is_visitor)
        if not self.parent.is_visitor:
            res = self.parent.cur.execute("""Select * FROM author WHERE name LIKE '{}'
             AND surname LIKE '{}'""".format(name, surname)).fetchall()
        else:
            res = self.parent.cur.execute("""Select * FROM visitor WHERE name LIKE '{}'
                         AND surname LIKE '{}'""".format(name, surname)).fetchall()
        if not name:
            self.statusLabel.setText('Неккорректное имя.')
        elif not surname:
            self.statusLabel.setText('Неккоректная фамилия.')
        elif bool(res):
            print(12312321)
            self.statusLabel.setText('Такое поле уже существует.')
        elif not self.parent.is_visitor:
            self.parent.cur.execute("""INSERT INTO author
             values ('{}', '{}', '{}')""".format(id, name, surname))
            self.parent.label.setText('Автор успешно добавлен.')
            self.close()
        else:
            id = self.parent.cur.execute("""SELECT COUNT(id) FROM visitor""").fetchall()
            id = str(id[0][0]) if id else ''

            self.parent.cur.execute("""INSERT INTO visitor
                         values ('{}', '{}', '{}')""".format(id, name, surname))
            self.parent.label.setText('Посетитель успешно добавлен.')
            self.parent.is_visitor = False
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec_())