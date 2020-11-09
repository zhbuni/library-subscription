import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt5.Qt import QFont
import sqlite3


class MyWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('untitled.ui', self)
        self.listWidget.itemDoubleClicked.connect(self.onClicked)
        self.search.clicked.connect(self.searchBook)
        self.con = sqlite3.connect("library.db")
        self.cur = self.con.cursor()

    def searchBook(self):
        txt = self.box.currentText()
        searchText = self.edit.text()
        result = []
        if txt == 'Название':
            result = self.cur.execute("""SELECT title FROM books
            WHERE title LIKE '%{}'""".format(searchText)).fetchall()
        elif txt == 'Автор':
            name1, surname1 = searchText.split()
            print(name1, surname1)
            result1 = self.cur.execute("""SELECT id from author 
            WHERE name = '{}' AND surname = '{}'""".format(name1, surname1)).fetchall()[0][0]
            result = self.cur.execute("""SELECT title FROM books
                        WHERE author = '{}'""".format(result1)).fetchall()
        elif txt == 'Жанр':
            result = self.cur.execute("""SELECT title FROM books
                                    WHERE genre = '{}'""".format(searchText)).fetchall()
        elif txt == 'Издательство':
            result1 = self.cur.execute("""SELECT id from publishing 
                        WHERE title = '{}'""".format(searchText)).fetchall()[0][0]
            result = self.cur.execute("""SELECT title FROM books
                                    WHERE pubhouse = '{}'""".format(result1)).fetchall()
        else:
            searchText = int(searchText)
            result = self.cur.execute("""SELECT title FROM books
            WHERE pub_year = '{}'""".format(searchText)).fetchall()
        for el in result:
            self.listWidget.addItem(el[0])
        print(result)

    def onClicked(self, item):
        QMessageBox.information(self, "Info", item.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())