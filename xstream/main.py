# -*- coding :utf-8 -*-
# xstream/main.py
"""This module provides the xstram data scraping and visualization package."""

import sys
from PyQt6.QtWidgets import QApplication
import xstream.views

def main():
    """Project main function"""
    # Create the application
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Run the event loop
    splash_screen = xstream.views.SplashScreen()
    splash_screen.exec()

    mainWindow = xstream.views.MainWindow()
    mainWindow.show()



    sys.exit(app.exec())


