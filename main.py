# -*- coding: utf-8 -*-
import sys
from PyQt5 import QtWidgets as QW
from interface import MainWindow





if __name__=="__main__":
	
	app = QW.QApplication(sys.argv)

	mainwin = MainWindow()

	mainwin.show()

	sys.exit(app.exec_())
