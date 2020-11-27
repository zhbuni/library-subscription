import sys
import datetime
import os

from PyQt5 import uic
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QMainWindow, \
    QTableWidgetItem, QDialog, QFileDialog

import sqlite3

from PIL import Image


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('UIs/untitled.ui', self)

        self.con = sqlite3.connect("library.db")
        self.cur = self.con.cursor()

        self.search.clicked.connect(self.searchBook)
        self.addBookButton.clicked.connect(self.addBook)
        self.addAuthorButton.clicked.connect(self.addAuthor)
        self.addVisitorButton.clicked.connect(self.addVisitor)
        self.GiveOutBookButton.clicked.connect(self.giveOutBook)
        self.filterButton.clicked.connect(self.setFilters)
        self.tableWidget.itemSelectionChanged.connect(self.bookSelected)
        self.giveBackButton.clicked.connect(self.giveBack)
        self.addGenreButton.clicked.connect(self.addGenre)
        self.addPubButton.clicked.connect(self.addPubHouse)
        self.deleteBookButton.clicked.connect(self.deleteBook)
        self.picAddButton.clicked.connect(self.addPicture)

        self.outdated = 0
        self.givenOut = 0

        self.clearTextOfStaticLabels()
        self.searchBook()

    def deleteBook(self):
        listOfItems = [el.text() for el in self.tableWidget.selectedItems()]
        if len(listOfItems) != 8:
            return

        newInd = self.tableWidget.model().index(self.tableWidget.currentRow(), 1)
        isnb = self.tableWidget.model().data(newInd)
        self.cur.execute("""
            DELETE FROM Books
            WHERE ISBN = '{}'""".format(isnb))

        self.searchBook()

    def resizeImage(self, image):
        """Подгон размера изображения для вывода в PyQt"""
        img = Image.open(image)
        width = 250
        height = 365
        resized_img = img.resize((width, height), Image.ANTIALIAS)
        resized_img.save(image)

    def clearTextOfStaticLabels(self):
        self.titleLabel1.clear()
        self.authorLabel1.clear()
        self.genreLabel1.clear()
        self.pubLabel1.clear()
        self.titleLabel.clear()
        self.authorLabel.clear()
        self.genreLabel.clear()
        self.pubLabel.clear()
        self.yearLabel.clear()

    def bookSelected(self):
        """Вывод информации о книге."""
        self.image.clear()

        self.clearTextOfStaticLabels()

        listOfItems = [el.text() for el in self.tableWidget.selectedItems()]
        if len(listOfItems) != 8:
            return

        self.titleLabel1.setText('Название')
        self.authorLabel1.setText('Автор')
        self.genreLabel1.setText('Жанр')
        self.pubLabel1.setText('Издательство')
        self.titleLabel.setText(listOfItems[0])
        self.authorLabel.setText(listOfItems[2] + ' ' + listOfItems[3])
        self.genreLabel.setText(listOfItems[-1])
        self.pubLabel.setText(listOfItems[4])
        self.yearLabel.setText(listOfItems[-2])

        fname = self.cur.execute("""
            SELECT picPath
            FROM Books
            WHERE Title = '{}'""".format(listOfItems[0])).fetchall()[0][0]
        fname = '' if fname is None else fname
        if os.path.exists(fname):
            self.resizeImage(fname)

            self.pixmap = QPixmap(fname)

            self.image.setPixmap(self.pixmap)
        else:
            self.pixmap = QPixmap('Images/standart.jpg')
            self.image.setPixmap(self.pixmap)

    def addPicture(self):
        listOfItems = [el.text() for el in self.tableWidget.selectedItems()]
        if len(listOfItems) != 8:
            self.label.setText('Выберите одну книгу.')
            return

        newInd = self.tableWidget.model().index(self.tableWidget.currentRow(), 1)
        isnb = self.tableWidget.model().data(newInd)

        fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '')[0]
        if fname:
            print(fname)
            self.cur.execute("""
                UPDATE Books
                SET picPath = '{}'
                WHERE ISBN = '{}'""".format(fname, isnb))

            self.bookSelected()

    def giveOutBook(self):
        """Создание диалогового окна для выдачи книги"""
        self.label.setText('')

        if len(self.tableWidget.selectedItems()) > 8:
            self.label.setText('Выберите одну книгу.')
            return
        id = self.tableWidget.currentRow()

        if id == -1:
            self.label.setText('Выберите книгу.')
        else:
            self.dialog = GiveOutBookClass(id, parent=self)
            self.dialog.show()

    def searchBook(self):
        """Поиск книги в БД"""
        txt = self.box.currentText()
        searchText = self.edit.text()

        self.label.setText('')

        self.tableWidget.clear()
        if txt == 'Посетитель':
            pass
        elif self.outdated:
            today = datetime.date.today()

            result = self.cur.execute("""
                SELECT
                books.title, books.ISBN,
                author.name, 
                author.surname, publishing.title,
                CASE WHEN books.IsAvailable = 1 THEN "Да" ELSE "Нет" END AS "IsAvailable",
                books.pub_Year, genres.title
                FROM books
                INNER JOIN author ON author.id = books.author
                INNER JOIN publishing ON publishing.id = books.pubHouse
                INNER JOIN Genres ON Genres.id = books.genre
                INNER JOIN ListOfBooks ON ListOfBooks.bookid = Books.id
                WHERE (books.title LIKE '%{}' OR genres.title LIKE '%{}'
                OR publishing.title LIKE '%{}' OR Books.pub_year LIKE '%{}')
                AND books.isAvailable = 0
                AND CASE WHEN '{}' = '1'
                THEN Date(ListOfBooks.expireDate) < Date('{}')
                ELSE 1 END
                """.format(searchText, searchText,
                           searchText, searchText,
                           self.outdated, today)).fetchall()

        elif txt == 'Название' or txt == 'Жанр' \
                or txt == 'Издательство' or txt == 'Год выпуска':
            result = self.cur.execute("""
                SELECT
                books.title, books.ISBN,
                author.name, 
                author.surname, publishing.title,
                CASE WHEN books.IsAvailable = 1 THEN "Да" ELSE "Нет" END AS "IsAvailable",
                books.pub_Year, genres.title
                FROM books
                INNER JOIN author ON author.id = books.author
                INNER JOIN publishing ON publishing.id = books.pubHouse
                INNER JOIN Genres ON Genres.id = books.genre
                WHERE (books.title LIKE '%{}' OR genres.title LIKE '%{}'
                OR publishing.title LIKE '%{}' OR Books.pub_year LIKE '%{}')
                AND CASE WHEN '{}' = '1'
                THEN books.isAvailable = 0 
                ELSE books.isAvailable = 0 or books.isAvailable = 1 END
                """.format(searchText, searchText,
                           searchText, searchText, self.givenOut)).fetchall()
        elif txt == 'Автор':
            name1, surname1 = '', ''

            try:
                name1, surname1 = searchText.split()
            except ValueError:
                print('Имя введено некорректно')

            result = self.cur.execute("""
                SELECT
                books.title, books.ISBN,
                author.name, 
                author.surname, publishing.title,
                CASE WHEN books.IsAvailable = 1 THEN "Да" ELSE "Нет" END AS "IsAvailable",
            	books.pub_Year, genres.title
                FROM books
                INNER JOIN author ON author.id = books.author
                INNER JOIN publishing ON publishing.id = books.pubHouse
                INNER JOIN Genres ON Genres.id = books.genre
                WHERE 
                author.surname LIKE '%{}' AND author.name LIKE '%{}'
                AND CASE WHEN '{}' = '1'
                THEN books.isAvailable = 0 
                ELSE books.isAvailable = 0 or books.isAvailable = 1 END
                        """.format(surname1, name1,
                                   self.givenOut)).fetchall()

        self.tableWidget.setColumnCount(8)
        self.tableWidget.setHorizontalHeaderLabels(['Название', 'ISBN', 'Имя', 'Фамилия',
                                                    'Издательство', 'В наличии',
                                                    'Год', 'Жанр'])

        self.tableWidget.setRowCount(0)

        for i, row in enumerate(result):
            self.tableWidget.setRowCount(
                self.tableWidget.rowCount() + 1)
            for j, elem in enumerate(row):
                QTableWidgetItem(elem).setFlags(Qt.ItemIsEnabled)
                self.tableWidget.setItem(
                    i, j, QTableWidgetItem(str(elem)))

        self.tableWidget.resizeColumnsToContents()

    def addBook(self):
        """Вызов диалогово окна для добавления книги"""
        self.dialog = BookAddDialog(self)
        self.dialog.show()

    def setFilters(self):
        """Окно для задания фильтров поиска"""
        self.dialog = FilterDialog(self)
        self.dialog.show()

    def giveBack(self):
        """Создание окна для возврата книги"""
        self.dialog = BookReturnDialog(self)
        self.dialog.show()

    def addAuthor(self):
        """Создание окна для добавления автора"""
        self.is_visitor = False
        self.dialog = AuthorAddDialog(self)
        self.dialog.show()

    def addVisitor(self):
        """Создание окна для добавления посетителя"""
        self.is_visitor = True
        self.dialog = AuthorAddDialog(self)
        self.dialog.show()

    def addGenre(self):
        """Создание окна для добавления жанра"""
        self.isGenre = True
        self.dialog = AddGenreOrPubHouseClass(self)
        self.dialog.show()

    def addPubHouse(self):
        """Создание окна для добавления издательства"""
        self.isGenre = False
        self.dialog = AddGenreOrPubHouseClass(self)
        self.dialog.show()

    def closeEvent(self, event):
        """Метод, вызываемый перед закрытием приложения"""
        self.con.commit()


class AddGenreOrPubHouseClass(QDialog):
    """Класс, создающий окно для добавления жанра или издательства"""

    def __init__(self, parent=None):
        super(AddGenreOrPubHouseClass, self).__init__(parent)

        self.parent = parent

        self.setModal(True)
        uic.loadUi('UIs/addGenre.ui', self)

        if self.parent.isGenre:
            self.titleLabel.setText("Жанр")
        else:
            self.titleLabel.setText("Издательство")

        self.pushButton.clicked.connect(self.add)

    def add(self):
        txt = self.lineEdit.text()
        if self.parent.isGenre:
            self.titleLabel.setText("Жанр")
            id = self.parent.cur.execute("""
                SELECT MAX(id) 
                FROM genres""").fetchall()
            id = int(id[0][0]) + 1 if id else 0

            if not txt:
                self.label.setText('Введите жанр.')
                return
            if self.parent.cur.execute("""
                    SELECT *
                    FROM Genres
                    WHERE title = '{}'""".format(txt)).fetchall():
                self.label.setText('Такой жанр уже есть.')
                return
            self.parent.cur.execute("""
                INSERT INTO Genres (id, title) 
                VALUES ({}, '{}')""".format(id, txt))
            self.parent.label.setText('Жанр добавлен.')
        else:
            self.titleLabel.setText("Издательство")
            id = self.parent.cur.execute("""
                            SELECT COUNT(id) 
                            FROM Publishing""").fetchall()
            id = id[0][0] if id else 0

            if not txt:
                self.label.setText('Введите название.')
                return

            self.parent.cur.execute("""
                            INSERT INTO Publishing (id, title) 
                            VALUES ({}, '{}')""".format(id, txt))

            self.parent.label.setText('Издательство добавлено.')
        self.close()


class FilterDialog(QDialog):
    """Класс, создающий окно для выбора фильтров поиска"""

    def __init__(self, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.parent = parent
        self.setModal(True)

        uic.loadUi('UIs/filters.ui', self)

        self.givenBox.setCheckState(self.parent.givenOut + 1 if self.parent.givenOut else 0)
        self.dateBox.setCheckState(self.parent.outdated + 1 if self.parent.outdated else 0)

        self.applyButton.clicked.connect(self.apply)

    def apply(self):
        self.parent.outdated = self.dateBox.checkState() - 1 \
            if bool(self.dateBox.checkState()) else 0
        self.parent.givenOut = self.givenBox.checkState() - 1 \
            if bool(self.givenBox.checkState()) else 0

        self.parent.searchBook()
        self.close()


class BookReturnDialog(QDialog):
    """Класс, создающий окно для возврата книги"""

    def __init__(self, parent=None):
        super(BookReturnDialog, self).__init__(parent)

        self.parent = parent

        self.setWindowTitle('Возврат книги')
        self.setModal(True)

        uic.loadUi('UIs/giveBack.ui', self)
        self.pushButton.clicked.connect(self.returnBook)

    def returnBook(self):
        txt = self.lineEdit.text()
        print(txt)

        self.label.clear()
        if not txt:
            self.label.setText('Введите название книги.')
            return
        elif not self.parent.cur.execute("""
                SELECT *
                FROM Books
                WHERE title = '{}'""".format(txt)).fetchall():
            self.label.setText('Такой книги нет.')
            return
        elif self.parent.cur.execute("""
                SELECT isAvailable
                FROM Books
                WHERE title = '{}'""".format(txt)).fetchall()[0][0]:
            self.label.setText("Данная книга не выдана.")
            return
        self.parent.cur.execute("""
            UPDATE Books
            SET isAvailable = 1
            WHERE Title = '{}'""".format(txt))

        self.parent.cur.execute("""
            DELETE FROM ListOfBooks
            WHERE bookId 
            IN (SELECT Books.id FROM Books
            INNER JOIN listOfBooks ON Books.id = listOfBooks.bookId
            WHERE Books.title = '{}')""".format(txt))

        self.parent.label.setText('Возврат осуществлен.')
        self.close()


class GiveOutBookClass(QDialog):
    """Класс, создающий окно для выдачи книги"""

    def __init__(self, BookId, parent=None):
        super(GiveOutBookClass, self).__init__(parent)

        self.parent = parent
        self.book_id = BookId

        self.setWindowTitle('Выдать книгу')
        self.setModal(True)

        uic.loadUi('UIs/giveOut.ui', self)

        lstOfVisitors = self.parent.cur.execute("""
                SELECT name, surname 
                FROM Visitor""").fetchall()

        for el in lstOfVisitors:
            self.comboBox.addItem(el[0] + " " + el[1])

        self.addButton.clicked.connect(self.giveOut)

    def giveOut(self):
        self.statusLabel.setText('')
        name, surname = self.comboBox.currentText().split()

        todaysDate = datetime.date.today()
        selectedDate = self.calendar.selectedDate().toPyDate()

        if selectedDate <= todaysDate:
            self.statusLabel.setText('Дата некорректна.')
            return

        isAvailable = self.parent.cur.execute("""
                SELECT isavailable 
                FROM Books
                WHERE id = '{}'""".format(self.book_id)).fetchall()[0][0]

        if isAvailable == 0:
            self.statusLabel.setText('Книга уже выдана.')
            return

        visitor = self.parent.cur.execute("""
            SELECT id 
            FROM visitor 
            WHERE name LIKE '{}' 
            AND surname LIKE '{}'""".format(name, surname)).fetchall()[0][0]

        id = self.parent.cur.execute("""
            SELECT COUNT(id) 
            FROM ListOfBooks""").fetchall()
        id = id[0][0] if id else 0

        date = sqlite3.Date.fromisoformat(str(selectedDate))

        self.parent.cur.execute("""
            INSERT INTO ListOfBooks
            VALUES ('{}', '{}', '{}', '{}')""".format(id, visitor, self.book_id, date))

        self.parent.cur.execute("""
            UPDATE Books
            SET isAvailable = 0
            WHERE id = '{}'""".format(self.book_id))

        self.parent.label.setText('Книга успешно выдана.')

        self.close()


class BookAddDialog(QDialog):
    """Класс, создающий окно для добавления книги"""

    def __init__(self, parent=None):

        super(BookAddDialog, self).__init__(parent)
        self.parent = parent
        self.setModal(True)

        self.fname = ''

        uic.loadUi('UIs/addDialog.ui', self)

        self.addBookButton.clicked.connect(self.addBook)
        self.picButton.clicked.connect(self.picture)

        lstOfAuthors = self.parent.cur.execute("""
            SELECT name, surname 
            FROM Author""").fetchall()

        lstOfGenres = self.parent.cur.execute("""
            SELECT title 
            FROM Genres""").fetchall()

        lstOfPublishings = self.parent.cur.execute("""
            SELECT title 
            FROM Publishing""").fetchall()

        for el in lstOfAuthors:
            self.authorEdit.addItem(el[0] + " " + el[1])

        for el in lstOfGenres:
            self.genreEdit.addItem(el[0])

        for el in lstOfPublishings:
            self.pubEdit.addItem(el[0])

    def picture(self):
        self.fname = QFileDialog.getOpenFileName(self, 'Выбрать картинку', '')[0]

    def addBook(self):
        self.statusLabel.setText('')
        pubHouse = self.pubEdit.currentText()
        author = self.authorEdit.currentText()

        id = self.parent.cur.execute("""
            SELECT MAX(id) 
            FROM books""").fetchall()
        id = id[0][0] + 1 if id else 0

        if not self.titleEdit.text():
            self.statusLabel.setText('Некорректное название')
        elif not author:
            self.statusLabel.setText('Такого автора нет')
        elif pubHouse != 0 and not pubHouse:
            self.statusLabel.setText('Такого издательства нет')
        elif not self.genreEdit.currentText():
            self.statusLabel.setText('Неккоректный жанр')
        else:
            title = self.titleEdit.text()

            genre = self.parent.cur.execute("""
                SELECT id
                FROM Genres
                WHERE title = '{}'""".format(self.genreEdit.currentText())).fetchall()[0][0]

            pubHouse = self.parent.cur.execute("""
                SELECT id
                FROM publishing
                WHERE title = '{}'""".format(pubHouse)).fetchall()[0][0]

            name, surname = author.split()
            author = self.parent.cur.execute("""
                SELECT id
                FROM author
                WHERE name LIKE '{}' 
                AND surname LIKE '{}'""".format(name, surname)).fetchall()[0][0]

            pubHouseBooks = self.parent.cur.execute("""
                SELECT COUNT(id) 
                FROM books
                WHERE pubHouse = '{}'""".format(str(pubHouse))).fetchall()

            pubHouseBooks = pubHouseBooks[0][0] if pubHouseBooks else ''
            pubHouseBooks = str(pubHouseBooks).rjust(3, '0')

            ISBN = '978-5-' + str(pubHouse) + '-' + pubHouseBooks

            currentYear = str(QDate.currentDate().year())

            print(self.fname)
            self.parent.cur.execute("""
                INSERT INTO books 
                VALUES ('{}', '{}', '{}', '{}',
                        '{}', '{}', '{}', '{}', '{}')""".format(id, title, ISBN,
                                                                author, pubHouse,
                                                                currentYear, 1,
                                                                genre, self.fname))

            self.parent.label.setText('Книга успешно добавлена.')
            self.parent.searchBook()
            self.close()


class AuthorAddDialog(QDialog):
    """Класс, создающий окно для добавления автора"""

    def __init__(self, parent=None):
        super(AuthorAddDialog, self).__init__(parent)

        self.parent = parent
        self.setWindowTitle('Добавить автора')

        self.setModal(True)
        uic.loadUi('UIs/addAuthor.ui', self)

        self.addButton.clicked.connect(self.addAuthor)

    def addAuthor(self):
        name = self.nameEdit.text()
        surname = self.surnameEdit.text()

        id = self.parent.cur.execute("""
            SELECT COUNT(id) 
            FROM author""").fetchall()
        id = str(id[0][0]) if id else ''

        if not self.parent.is_visitor:
            res = self.parent.cur.execute("""
                SELECT * 
                FROM author 
                WHERE name LIKE '{}'
                AND surname LIKE '{}'""".format(name, surname)).fetchall()
        else:
            res = self.parent.cur.execute("""
                SELECT * 
                FROM visitor 
                WHERE name LIKE '{}'
                AND surname LIKE '{}'""".format(name, surname)).fetchall()

        if not name:
            self.statusLabel.setText('Неккорректное имя.')
        elif not surname:
            self.statusLabel.setText('Неккоректная фамилия.')
        elif bool(res):
            self.statusLabel.setText('Такое поле уже существует.')
        elif not self.parent.is_visitor:
            self.parent.cur.execute("""
                INSERT INTO author
                VALUES ('{}', '{}', '{}')""".format(id, name, surname))

            self.parent.label.setText('Автор успешно добавлен.')

            self.close()
        else:
            id = self.parent.cur.execute("""
                SELECT COUNT(id) 
                FROM visitor""").fetchall()
            id = str(id[0][0]) if id else ''

            self.parent.cur.execute("""
                INSERT INTO visitor
                VALUES ('{}', '{}', '{}')""".format(id, name, surname))

            self.parent.label.setText('Посетитель успешно добавлен.')
            self.parent.is_visitor = False

            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec_())
